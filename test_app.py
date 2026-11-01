import json
import socket
import threading
import time
import unittest
import urllib.request
import tempfile
from pathlib import Path
from api_config import enable_stats_api
from app import Store, GameConnection, make_server, normalize_config, series_state, preview_snapshot


class ScoreboardTests(unittest.TestCase):
    def test_panel_palette_survives_profiles_and_old_profiles_still_load(self):
        config = normalize_config({'panel_colors': {'boost': 'pink', 'stats': 'coral',
                                                    'players0': 'dark', 'players1': 'yellow'}})
        loaded = normalize_config(json.loads(json.dumps(config)))
        self.assertEqual(loaded['panel_colors'], config['panel_colors'])
        legacy = normalize_config({'event': 'Mi torneo'})
        self.assertEqual(legacy['panel_colors']['boost'], 'dark')
        self.assertEqual(normalize_config({'panel_colors': {'boost': 'bad'}})['panel_colors']['boost'], 'dark')

    def test_goal_does_not_display_scorer_or_interrupt_score_sync(self):
        store = Store()
        store.match['banner'] = 'Previous message'
        store.banner_until = time.monotonic()+10
        store.ingest({'Event': 'GoalScored', 'Data': json.dumps({'Scorer': {'Name': 'Scorer'}})})
        self.assertEqual(store.snapshot()['match']['banner'], '')
        store.ingest({'Event': 'UpdateState', 'Data': json.dumps({'Game': {
            'TimeSeconds': 80, 'Teams': [{'TeamNum': 0, 'Score': 2}, {'TeamNum': 1, 'Score': 1}]}})})
        self.assertEqual(store.match['scores'], [2, 1])
    def test_real_wire_data_is_json_text(self):
        store = Store()
        # Structure observed from the game over TCP: Data is a JSON string.
        def packet(scores, seconds, boost, score):
            return {'Event': 'UpdateState', 'Data': json.dumps({
                'Players': [{'Name': 'Jugador en cámara', 'TeamNum': 0, 'Shortcut': 3,
                             'Score': score, 'Goals': 1, 'Shots': 2, 'Assists': 0,
                             'Saves': 2, 'Boost': boost}],
                'Game': {'Teams': [{'TeamNum': i, 'Score': value} for i, value in enumerate(scores)],
                         'TimeSeconds': seconds, 'bOvertime': False,
                         'Target': {'Name': 'Jugador en cámara', 'Shortcut': 3, 'TeamNum': 0}}
            }, ensure_ascii=False)}
        self.assertTrue(store.ingest(packet([1, 1], 228, 85, 88)))
        first = store.snapshot()
        self.assertEqual(first['match']['scores'], [1, 1])
        self.assertEqual(first['match']['time'], 228)
        self.assertEqual(first['match']['target'], 'Jugador en cámara')
        self.assertEqual(first['match']['players'][0]['Boost'], 85)
        self.assertTrue(first['connection']['receiving'])
        self.assertTrue(store.ingest(packet([2, 1], 227, 34, 198)))
        second = store.snapshot()
        self.assertEqual(second['match']['scores'], [2, 1])
        self.assertEqual(second['match']['time'], 227)
        self.assertEqual(second['match']['players'][0]['Score'], 198)
        self.assertEqual(second['match']['players'][0]['Boost'], 34)
        self.assertTrue(store.ingest({'Event': 'ClockUpdatedSeconds', 'Data': json.dumps({'TimeSeconds': 226, 'bOvertime': True})}))
        self.assertTrue(store.match['overtime'])
        self.assertEqual(store.match['time'], 226)
        for _ in range(2):
            store.ingest({'Event': 'MatchEnded', 'Data': json.dumps({'WinnerTeamNum': 0, 'MatchGuid': 'wire-match'})})
        self.assertEqual(store.config['teams'][0]['wins'], 1)

    def test_invalid_wire_payload_is_not_live(self):
        store = Store()
        for data in ('not json', '[]', None, {'Game': None}):
            self.assertFalse(store.ingest({'Event': 'UpdateState', 'Data': data}))
        self.assertFalse(store.snapshot()['connection']['receiving'])

    def test_live_spectator_zero_boost_omission_and_no_camera_target(self):
        store = Store()
        data = {'Game': {'TimeSeconds': 200, 'Target': {'Name': 'Camera'}}, 'Players': [
            {'Name': 'Camera', 'TeamNum': 0, 'Score': 128, 'bHasCar': True, 'Speed': 34.3},
            {'Name': 'No telemetry', 'TeamNum': 1, 'Score': 20}]}
        store.ingest({'Event': 'UpdateState', 'Data': json.dumps(data)})
        self.assertEqual(store.match['players'][0]['Boost'], 0)
        self.assertNotIn('Boost', store.match['players'][1])
        self.assertNotIn('Boost', data['Players'][0])
        data['Players'][0]['Boost'] = None
        store.ingest({'Event': 'UpdateState', 'Data': json.dumps(data)})
        self.assertEqual(store.match['players'][0]['Boost'], 0)
        data['Game']['Target'] = None
        self.assertTrue(store.ingest({'Event': 'UpdateState', 'Data': json.dumps(data)}))
        self.assertEqual(store.match['target'], '')

    def test_enable_api_preserves_settings_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'TAStatsAPI.ini'
            original = '[Other]\nPort=100\n[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\nPort=50000\nWebPort=50000\nKeep=True\n[After]\nValue=yes\n'
            path.write_text(original, 'utf-8')
            backup, port = enable_stats_api(path)
            updated = path.read_text('utf-8')
            self.assertEqual(backup.read_text('utf-8'), original)
            self.assertEqual(port, 50000)
            self.assertIn('PacketSendRate=10', updated)
            self.assertIn('WebPort=49124', updated)
            self.assertIn('[Other]\nPort=100', updated)
            self.assertIn('[After]\nValue=yes', updated)
            self.assertIn('Keep=True', updated)

    def test_authoritative_updates_resync_after_goal_pause_and_new_game(self):
        s = Store()
        for scores, clock, overtime in [([2, 1], 90, False), ([3, 1], 90, False),
                                         ([3, 1], 90, False), ([3, 3], 18, True), ([0, 0], 300, False)]:
            s.ingest({'Event': 'UpdateState', 'Data': {'Game': {
                'Teams': [{'TeamNum': i, 'Score': score} for i, score in enumerate(scores)],
                'TimeSeconds': clock, 'bOvertime': overtime}, 'Players': []}})
            snapshot = s.snapshot()
            self.assertEqual(snapshot['match']['scores'], scores)
            self.assertEqual(snapshot['match']['time'], clock)
            self.assertEqual(snapshot['match']['overtime'], overtime)
            self.assertTrue(snapshot['connection']['receiving'])

    def test_live_state_and_series_duplicate(self):
        s = Store()
        s.ingest({'Event': 'UpdateState', 'Data': {'Players': [{'Name': 'Piru', 'TeamNum': 0, 'Boost': 45}],
                 'Game': {'Teams': [{'TeamNum': 1, 'Score': 3}, {'TeamNum': 0, 'Score': 2}],
                          'TimeSeconds': 8, 'bOvertime': True, 'Target': {'Name': 'Piru'}}}})
        self.assertEqual(s.match['scores'], [2, 3])
        self.assertTrue(s.match['overtime'])
        self.assertEqual(s.match['target'], 'Piru')
        for _ in range(2):
            s.ingest({'Event': 'MatchEnded', 'Data': {'WinnerTeamNum': 1, 'MatchGuid': 'match1'}})
        self.assertEqual(s.config['teams'][1]['wins'], 1)
        self.assertEqual(s.config['game'], 2)

    def test_profiles(self):
        self.assertEqual(normalize_config({'scale': 999})['scale'], 150)
        with self.assertRaises(ValueError):
            normalize_config({'bestof': 6})

    def test_all_formats_roundtrip_and_finish(self):
        for bestof in (1, 2, 3, 4, 5, 7):
            with self.subTest(bestof=bestof):
                store = Store()
                store.config = normalize_config({'bestof': bestof})
                target = bestof//2+1
                self.assertEqual(series_state(store.config)['slots'], target)
                for i in range(target+2):
                    store.ingest({'Event': 'MatchEnded', 'Data': {'WinnerTeamNum': 0, 'MatchGuid': f'm{i}'}})
                self.assertEqual(store.config['teams'][0]['wins'], target)
                self.assertTrue(series_state(store.config)['complete'])
                self.assertEqual(store.config, normalize_config(json.loads(json.dumps(store.config))))

    def test_even_formats_can_end_in_draw(self):
        for bestof in (2, 4):
            store = Store()
            store.config = normalize_config({'bestof': bestof})
            for i in range(bestof):
                store.ingest({'Event': 'MatchEnded', 'Data': {'WinnerTeamNum': i%2, 'MatchGuid': f'm{i}'}})
            self.assertTrue(series_state(store.config)['tied'])
            self.assertEqual(store.config['game'], bestof)
            wins = [t['wins'] for t in store.config['teams']]
            store.ingest({'Event': 'MatchEnded', 'Data': {'WinnerTeamNum': 0, 'MatchGuid': 'extra'}})
            self.assertEqual([t['wins'] for t in store.config['teams']], wins)

    def test_preview_does_not_change_live_data_or_connection(self):
        store = Store()
        store.automatic = True
        before = store.snapshot()
        example = preview_snapshot(store)
        self.assertEqual(example['match']['players'][0]['Boost'], 72)
        self.assertEqual(example['match']['players'][0]['Score'], 541)
        self.assertEqual(store.snapshot(), before)

    def test_tcp_fragmented_stream_and_reconnect_stop(self):
        s = Store()
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        listener.settimeout(3)
        port = listener.getsockname()[1]
        def sender():
            with listener:
                conn, _ = listener.accept()
                with conn:
                    data = (json.dumps({'Event': 'ClockUpdatedSeconds', 'Data': json.dumps({'TimeSeconds': 42})})+
                            json.dumps({'Event': 'ClockUpdatedSeconds', 'Data': json.dumps({'TimeSeconds': 41})})).encode()
                    conn.sendall(data[:13])
                    time.sleep(.02)
                    conn.sendall(data[13:])
                    time.sleep(.1)
        t = threading.Thread(target=sender)
        t.start()
        client = GameConnection(s)
        client.connect(port)
        deadline = time.monotonic()+2
        while s.match['time'] != 41 and time.monotonic() < deadline:
            time.sleep(.01)
        client.disconnect()
        t.join()
        self.assertEqual(s.match['time'], 41)
        self.assertFalse(client.thread.is_alive())

    def test_obs_endpoint(self):
        server = make_server(Store())
        t = threading.Thread(target=server.serve_forever)
        t.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}'
            with urllib.request.urlopen(url+'/state', timeout=3) as response:
                self.assertEqual(json.load(response)['config']['event'], 'TORNEO PIRULETA')
            with urllib.request.urlopen(url+'/overlay', timeout=3) as response:
                self.assertIn(b'background:transparent', response.read())
            with urllib.request.urlopen(url+'/preview-state', timeout=3) as response:
                self.assertEqual(json.load(response)['match']['target'], 'PIRU')
            with urllib.request.urlopen(url+'/state', timeout=3) as response:
                self.assertEqual(json.load(response)['match']['players'], [])
            with urllib.request.urlopen(url+'/assets/torneo.png', timeout=3) as response:
                self.assertEqual(response.headers['Content-Type'], 'image/png')
        finally:
            server.shutdown()
            server.server_close()
            t.join()


if __name__ == '__main__':
    unittest.main()
