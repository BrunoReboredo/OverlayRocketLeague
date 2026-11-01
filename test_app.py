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
                    data = (json.dumps({'Event': 'ClockUpdatedSeconds', 'Data': {'TimeSeconds': 42}})+
                            json.dumps({'Event': 'ClockUpdatedSeconds', 'Data': {'TimeSeconds': 41}})).encode()
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
