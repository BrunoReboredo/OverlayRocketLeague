"""Piruleta - Overlay. Python 3.11+, standard library only."""
import base64
import binascii
import copy
import json
import math
import os
import re
from pathlib import Path
import socket
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit, parse_qsl, urlencode
import webbrowser
from api_config import discover_stats_ini, find_stats_ini, enable_stats_api

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
APP_VERSION = '3.1'
RESOURCE_ROOT = Path(getattr(sys, '_MEIPASS', ROOT))

def resource_path(relative):
    external = ROOT / relative
    return external if external.is_file() else RESOURCE_ROOT / relative

# Private online, offline exhibition and local LAN lobby.
PRIVATE_PLAYLISTS = frozenset((6, 8, 24))
SERIES_FORMATS = (1, 2, 3, 4, 5, 7)
MAX_LOGO_BYTES = 4_000_000
MAX_LOGO_DATA_URL_CHARS = ((MAX_LOGO_BYTES + 2) // 3) * 4 + 64


FONT_DIRECTORY = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'PiruletaOverlay' / 'fonts'
STANDARD_FONTS = ('Montserrat', 'Arial', 'Segoe UI', 'Verdana', 'Trebuchet MS', 'Impact')
FONT_TYPES = {
    '.ttf': ('font/ttf', (b'\x00\x01\x00\x00', b'true')),
    '.otf': ('font/otf', (b'OTTO',)),
    '.woff': ('font/woff', (b'wOFF',)),
    '.woff2': ('font/woff2', (b'wOF2',)),
}
CUSTOM_FONT_PREFIX = 'Personalizada · '
MAX_FONT_BYTES = 16 * 1024 * 1024


def series_state(config):
    bestof = config['bestof']
    wins = [team['wins'] for team in config['teams']]
    target = bestof//2 + 1
    complete = max(wins) >= target or sum(wins) >= bestof
    tied = complete and wins[0] == wins[1]
    return {'target': target, 'complete': complete, 'tied': tied,
            'game': min(bestof, sum(wins) + (0 if complete else 1)),
            'slots': bestof if bestof % 2 == 0 else target}


def swap_team_sides(config):
    """Move identities and series wins; live game telemetry keeps its game-side indexes."""
    swapped = copy.deepcopy(config)
    swapped['teams'].reverse()
    colors = swapped['colors']
    colors['pink'], colors['yellow'] = colors['yellow'], colors['pink']
    backgrounds = swapped['panel_colors']
    remap = {'pink': 'yellow', 'yellow': 'pink'}
    left, right = backgrounds['players0'], backgrounds['players1']
    backgrounds['players0'], backgrounds['players1'] = remap.get(right, right), remap.get(left, left)
    for panel in ('boost', 'stats'):
        a, b = backgrounds[panel+'0'], backgrounds[panel+'1']
        backgrounds[panel+'0'], backgrounds[panel+'1'] = remap.get(b, b), remap.get(a, a)
    return swapped


ROTATION_SLOTS = ('rotation1', 'rotation2', 'rotation3')
MIN_ROTATING_SPONSORS = 2
MAX_ROTATING_SPONSORS = 8
SPONSOR_SLOTS = (*ROTATION_SLOTS, 'overtime', 'replay')
SPONSOR_IMAGE_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}


DEFAULT = {
    'sponsor_interval': 8, 'sponsor_rotation_count': 3,
    'show_sponsor_rotation': True, 'show_sponsor_replay': True, 'show_sponsor_overtime': True,
    'sponsors': {slot: {'name': '', 'logo': ''} for slot in SPONSOR_SLOTS},
    'event': 'TORNEO PIRULETA', 'round': 'GRAN FINAL · PARTIDO [GAME]', 'bestof': 5,
    'teams': [{'name': 'PINK CANDY', 'logo': '', 'wins': 0},
              {'name': 'GOLDEN POP', 'logo': '', 'wins': 0}],
    'colors': {'pink': '#fa54b7', 'coral': '#ff8875', 'yellow': '#ffd14c',
               'dark': '#181426', 'text': '#ffffff'},
    'show_logos': True, 'show_players': True, 'show_stats': True, 'stats_style': 'Rectángulo',
    'show_boost': True, 'show_player_actions': True, 'show_events': True, 'show_goal_replay': True,
    'show_stats_camera': False, 'show_players_cameras': False, 'auto_replay_cameras': False, 'cameras': [],
    'design': 'rounded', 'font': 'Verdana', 'scale': 100, 'opacity': 100,
    'x': 360, 'y': 0, 'auto_series': True, 'custom_css': '', 'api_port': 49123,
    'scoreboard_gradient': True, 'brand_logo': '', 'goal_style': 'Torneo Piruleta', 'design_presets': {}, 'rck_layout_revision': 2, 'layout_defaults_revision': 1,
    'panel_colors': {'boost0': 'pink', 'boost1': 'yellow', 'stats0': 'pink', 'stats1': 'yellow',
                     'players0': 'dark', 'players1': 'dark'},
    'panels': {'players0': [0, 180, 100], 'players1': [1635, 180, 100],
               'focus': [0, 1030, 100], 'boost': [1695, 800, 120],
               'banner': [460, 370, 100]},
}


DESIGN_FIELDS = ('colors', 'panels', 'panel_colors', 'x', 'y', 'scale')


MINIMAL_DESIGN = 'Compacto'
LEGACY_MINIMAL_DESIGN = 'Minimalista 0.1'
DESIGNS = ('angular', 'rounded', 'classic', 'RCK', MINIMAL_DESIGN)
DESIGN_GROUPS = ('standard', 'RCK', MINIMAL_DESIGN)


def design_group(design):
    return design if design in DESIGN_GROUPS else 'standard'


def switch_design(raw, previous):
    """Keep independent positions for standard, RCK and minimalist layouts."""
    old_group = design_group(previous)
    new_group = design_group(raw['design'])
    if old_group == new_group:
        return raw
    raw = copy.deepcopy(raw)
    presets = raw.setdefault('design_presets', {})
    presets[old_group] = {key: copy.deepcopy(raw[key]) for key in DESIGN_FIELDS}
    incoming = copy.deepcopy(presets.get(new_group))
    if incoming is None:
        incoming = {key: copy.deepcopy(DEFAULT[key]) for key in DESIGN_FIELDS}
        if new_group == 'RCK':
            incoming['colors'].update(pink='#BEB4E6', yellow='#99C6DA', coral='#d9e0eb', dark='#04174A', text='#ffffff')
            incoming.update(x=500, y=0, scale=100)
            incoming['panels'].update(players0=[0, 190, 100], players1=[1620, 190, 100],
                                      focus=[0, 1030, 100], boost=[1695, 800, 120])
            incoming['panel_colors'].update(players0='dark', players1='dark', stats0='pink', stats1='yellow', boost0='dark', boost1='dark')
        elif new_group == MINIMAL_DESIGN:
            incoming.update(x=640, y=22, scale=100)
            incoming['colors'].update(pink='#ffffff', yellow='#a8a8a8', coral='#525252',
                                      dark='#101010', text='#ffffff')
            incoming['panels'].update(players0=[24, 44, 100], players1=[1616, 44, 100],
                                      focus=[24, 995, 100], boost=[1774, 930, 100])
    raw.update(incoming)
    return raw


def normalize_camera_url(value):
    value = value.strip()
    if not value:
        return ''
    if len(value) > 4096:
        raise ValueError('El enlace de cámara es demasiado largo.')
    url = urlsplit(value)
    parameters = dict(parse_qsl(url.query, keep_blank_values=True))
    if (url.scheme != 'https' or url.hostname not in ('vdo.ninja', 'www.vdo.ninja', 'obs.ninja', 'www.obs.ninja')
            or url.username or url.password or url.port not in (None, 443)
            or not parameters.get('view') or 'push' in parameters or 'director' in parameters):
        raise ValueError('Pega el enlace de visualización de VDO.Ninja / OBS Ninja, con https:// y ?view=...')
    parameters.update(cleanoutput='', noaudio='', autostart='')
    return url._replace(query=urlencode(parameters), fragment='').geturl()


STATS_STYLES = ('Rectángulo', 'Barra compacta')


def normalize_config(raw):
    """Validate profiles before they reach widgets or the overlay."""
    if not isinstance(raw, dict):
        raise ValueError('El perfil debe ser un objeto JSON.')
    c = copy.deepcopy(DEFAULT)
    for key in ('event', 'round', 'font'):
        if key in raw:
            c[key] = str(raw[key])[:120]
    for key, lo, hi in [('bestof', 1, 15), ('scale', 50, 150),
                        ('opacity', 10, 100), ('x', 0, 1900), ('y', 0, 1000), ('api_port', 1, 65535)]:
        c[key] = max(lo, min(hi, int(raw.get(key, c[key]))))
    if c['bestof'] not in SERIES_FORMATS:
        raise ValueError('Elige BO1, BO2, BO3, BO4, BO5 o BO7.')
    for key in c:
        if key.startswith('show_') or key in ('auto_series', 'auto_replay_cameras'):
            c[key] = bool(raw.get(key, c[key]))
    if c['show_stats_camera'] and c['show_players_cameras']:
        c['show_players_cameras'] = False
    design = raw.get('design')
    if design == LEGACY_MINIMAL_DESIGN:
        design = MINIMAL_DESIGN
    if design in DESIGNS:
        c['design'] = design
    if raw.get('goal_style') == 'Original':
        c['goal_style'] = 'Torneo Piruleta'
    if raw.get('goal_style') in ('Torneo Piruleta', 'Bigness League', 'RCS', 'RCK'):
        c['goal_style'] = raw['goal_style']
    if raw.get('stats_style') in STATS_STYLES:
        c['stats_style'] = raw['stats_style']
    elif raw.get('stats_style') == 'Actual':
        c['stats_style'] = 'Rectángulo'
    c['sponsor_interval'] = max(3, min(60, int(raw.get('sponsor_interval', c['sponsor_interval']))))
    sponsors = raw.get('sponsors')
    occupied = [int(slot[8:]) for slot, value in sponsors.items()
                if isinstance(slot, str) and re.fullmatch(r'rotation[1-9][0-9]*', slot)
                and int(slot[8:]) <= MAX_ROTATING_SPONSORS and isinstance(value, dict)
                and (value.get('name') or value.get('logo'))] if isinstance(sponsors, dict) else []
    count = max(MIN_ROTATING_SPONSORS, min(MAX_ROTATING_SPONSORS, int(raw.get('sponsor_rotation_count', 3))), *occupied)
    c['sponsor_rotation_count'] = count
    c['sponsors'] = {slot: {'name': '', 'logo': ''}
                     for slot in (*[f'rotation{i}' for i in range(1, count+1)], 'overtime', 'replay')}
    if isinstance(sponsors, dict):
        for slot in c['sponsors']:
            sponsor = sponsors.get(slot)
            if not isinstance(sponsor, dict):
                continue
            name = sponsor.get('name', '')
            logo = sponsor.get('logo', '')
            c['sponsors'][slot]['name'] = name.strip()[:60] if isinstance(name, str) else ''
            if (isinstance(logo, str) and len(logo) <= MAX_LOGO_DATA_URL_CHARS
                    and logo.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,'))):
                c['sponsors'][slot]['logo'] = logo
    c['scoreboard_gradient'] = bool(raw.get('scoreboard_gradient', True))
    c['brand_logo'] = str(raw.get('brand_logo', ''))[:MAX_LOGO_DATA_URL_CHARS]
    for panel in ('boost', 'stats'):
        legacy = raw.get('panel_colors', {}).get(panel)
        if legacy in c['colors']:
            c['panel_colors'][panel+'0'] = legacy
            c['panel_colors'][panel+'1'] = legacy
    camera_names = set()
    cameras = raw.get('cameras', [])
    if not isinstance(cameras, list) or len(cameras) > 8:
        raise ValueError('Puedes configurar hasta ocho cámaras de jugadores.')
    for camera in cameras:
        if not isinstance(camera, dict):
            raise ValueError('Revisa la configuración de cámaras.')
        name = str(camera.get('name', '')).strip()[:120]
        url = normalize_camera_url(str(camera.get('url', '')))
        if not url:
            continue
        if not name or name.casefold() in camera_names:
            raise ValueError('Cada cámara necesita un nombre de jugador diferente.')
        camera_names.add(name.casefold())
        c['cameras'].append({'name': name, 'url': url})
    c['custom_css'] = str(raw.get('custom_css', ''))[:50000]
    for key, value in raw.get('panel_colors', {}).items():
        if key in c['panel_colors'] and value in c['colors']:
            c['panel_colors'][key] = value
    for key, values in raw.get('panels', {}).items():
        if key in c['panels'] and isinstance(values, list) and len(values) == 3:
            c['panels'][key] = [max(0, min(1920, int(values[0]))),
                                max(0, min(1080, int(values[1]))),
                                max(25, min(200, int(values[2])))]
    for key, value in raw.get('colors', {}).items():
        if key in c['colors'] and isinstance(value, str) and len(value) == 7:
            int(value[1:], 16)
            if value.startswith('#'):
                c['colors'][key] = value
    for i, team in enumerate(raw.get('teams', [])[:2]):
        c['teams'][i] = {'name': str(team.get('name', 'EQUIPO'))[:80],
                         'logo': str(team.get('logo', ''))[:MAX_LOGO_DATA_URL_CHARS],
                         'wins': max(0, min(c['bestof']//2+1, int(team.get('wins', 0))))}
    if sum(t['wins'] for t in c['teams']) > c['bestof']:
        raise ValueError('Las victorias superan los partidos del formato. Reinicia la serie antes de cambiarlo.')
    presets = raw.get('design_presets', {})
    if isinstance(presets, dict):
        for group in DESIGN_GROUPS:
            preset = presets.get(group)
            if group == MINIMAL_DESIGN and not isinstance(preset, dict):
                preset = presets.get(LEGACY_MINIMAL_DESIGN)
            if isinstance(preset, dict):
                # Normalize cached layouts without recursively copying caches.
                saved = normalize_config({'design': 'rounded' if group == 'standard' else group,
                                          'rck_layout_revision': raw.get('rck_layout_revision', 1),
                                          'layout_defaults_revision': raw.get('layout_defaults_revision', 0),
                                          **{key: preset[key] for key in DESIGN_FIELDS if key in preset}})
                c['design_presets'][group] = {key: copy.deepcopy(saved[key]) for key in DESIGN_FIELDS}
    # Early RCK releases overwrote the regular layout in existing profiles.
    # Recognize the exact shipped preset rather than treating user colors as RCK.
    rck_palette = {'pink': '#bdb0e4', 'yellow': '#96c9da', 'coral': '#d9e0eb',
                   'dark': '#071640', 'text': '#ffffff'}
    if (c['design'] != 'RCK' and not c['design_presets']
            and c['colors'] == rck_palette and c['y'] == 36
            and c['panels']['focus'] == [76, 944, 100]
            and c['panels']['boost'] == [1590, 775, 140]):
        c['design_presets']['RCK'] = {key: copy.deepcopy(c[key]) for key in DESIGN_FIELDS}
        for key in DESIGN_FIELDS:
            c[key] = copy.deepcopy(DEFAULT[key])
    if raw.get('rck_layout_revision', 1) != 2:
        layouts = ([c] if c['design'] == 'RCK' else []) + ([c['design_presets']['RCK']] if 'RCK' in c['design_presets'] else [])
        for layout in layouts:
            if layout['x'] == 360 and layout['y'] == 36:
                layout.update(x=500, y=0)
            for key, old, new in [('players0', [60, 125, 100], [24, 190, 100]),
                                  ('players1', [1565, 125, 100], [1601, 190, 100]),
                                  ('focus', [76, 944, 100], [36, 925, 100]),
                                  ('boost', [1590, 775, 140], [1695, 860, 120])]:
                if layout['panels'][key] == old:
                    layout['panels'][key] = new
    if raw.get('layout_defaults_revision', 0) != 1:
        layouts = [c] + list(c['design_presets'].values())
        for layout in layouts:
            panels = layout['panels']
            for key, old_values, new_value in [
                    ('players0', ([24, 180, 100], [24, 190, 100]), None),
                    ('players1', ([1601, 180, 100], [1601, 190, 100]), None),
                    ('focus', ([36, 880, 100], [36, 925, 100]), [0, 1030, 100]),
                    ('boost', ([1695, 860, 120],), [1695, 800, 120])]:
                if panels[key] in old_values:
                    if key == 'players0':
                        panels[key] = [0, panels[key][1], panels[key][2]]
                    elif key == 'players1':
                        panels[key] = [1620 if layout.get('colors', {}).get('dark') == '#04174A' else 1635,
                                       panels[key][1], panels[key][2]]
                    else:
                        panels[key] = list(new_value)
    for layout in [c] + list(c['design_presets'].values()):
        position = layout['panels']['focus']
        if position[:2] == [1280, 1030]:
            layout['panels']['focus'] = [0, 1030, position[2]]
    return c


class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.config = copy.deepcopy(DEFAULT)
        self.match = {'scores': [0, 0], 'time': 300, 'overtime': False,
                      'players': [], 'target': '', 'banner': ''}
        self.status = 'Conexión automática · esperando Rocket League'
        self.finished = set()
        self.banner_until = 0
        self.automatic = False
        self.last_update = 0
        self.playlist_id = None
        self.match_closed = False
        self.history_replay = False
        self.goal_sequence = 0
        self.goal_until = 0
        self.goal_team = 0
        self.goal_armed = True
        self.in_goal_replay = False
        self.overtime_started = False
        self.countdown_started = None
        self.overtime_until = 0
        self.last_goal = None
        self.auto_camera_until = 0
        self.player_actions = {}
        self.action_sequence = 0

    def record_action(self, player, kind, attacker=None):
        if not isinstance(player, dict) or player.get('TeamNum') not in (0, 1) or not player.get('Name'):
            return
        now = time.monotonic()
        until = now + 4.5
        identity = (player['TeamNum'], player.get('Shortcut'), player['Name'])
        # Keep different actions together; a shot followed by a goal shares the goal's display window.
        if kind == 'goal':
            shot = self.player_actions.get(identity + ('shot',))
            if shot and shot['until'] > now:
                shot['until'] = until
        self.action_sequence += 1
        action = {'Name': player['Name'], 'TeamNum': player['TeamNum'],
                  'Shortcut': player.get('Shortcut'), 'kind': kind,
                  'id': self.action_sequence, 'until': until}
        if attacker is not None:
            action['attacker'] = {key: attacker.get(key) for key in ('Name', 'TeamNum', 'Shortcut')}
        self.player_actions[identity + (kind,)] = action

    def update_overtime(self, overtime):
        self.match['overtime'] = overtime
        if overtime and not self.overtime_started and self.countdown_started is not None:
            self.overtime_started = True
            self.overtime_until = self.countdown_started + 3

    def snapshot(self):
        with self.lock:
            if time.monotonic() > self.banner_until:
                self.match['banner'] = ''
            now = time.monotonic()
            self.player_actions = {key: action for key, action in self.player_actions.items() if action['until'] > now}
            actions = [dict(action, remaining=int((action['until']-now)*1000)) for action in self.player_actions.values()]
            goal_remaining = max(0, int((self.goal_until-time.monotonic())*1000))
            replay = (self.last_goal if self.in_goal_replay and not self.history_replay
                      and self.config['show_goal_replay'] else None)
            camera_remaining = (max(0, int((self.auto_camera_until-time.monotonic())*1000))
                                if self.config['auto_replay_cameras'] and not self.match_closed
                                and not self.history_replay and self.playlist_id in PRIVATE_PLAYLISTS else 0)
            overtime_remaining = max(0, int((self.overtime_until - now) * 1000))
            replay_sponsored = (self.in_goal_replay and
                                any(self.config['sponsors']['replay'].values()))
            return copy.deepcopy({'player_actions': actions, 'overtime_remaining': overtime_remaining, 'goal_replay_active': self.in_goal_replay and not self.history_replay,
                                  'auto_camera_remaining': camera_remaining, 'goal_replay': replay, 'goal_effect': {'id': self.goal_sequence, 'remaining': goal_remaining,
                                                 'team': self.goal_team}, 'config': self.config, 'match': self.match,
                                  'overlay_visible': (self.playlist_id in PRIVATE_PLAYLISTS
                                      and (not self.match_closed or replay is not None or replay_sponsored
                                           or (goal_remaining > 0 and self.config['show_events']))
                                      and not self.history_replay
                                      and self.automatic and self.last_update > 0
                                      and time.monotonic()-self.last_update < 5),
                                  'series': series_state(self.config),
                                  'connection': {'automatic': self.automatic,
                                                 'receiving': self.last_update > 0 and time.monotonic()-self.last_update < 5,
                                                 'status': self.status}})

    def ingest(self, packet):
        if not isinstance(packet, dict):
            return False
        event, d = packet.get('Event'), packet.get('Data', {})
        # The live game serializes Data as JSON text; documentation examples
        # also use an embedded object. Accept both transport representations.
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except json.JSONDecodeError:
                return False
        if not isinstance(d, dict):
            return False
        with self.lock:
            m = self.match
            if event == 'UpdateState':
                g = d.get('Game', {})
                if not isinstance(g, dict) or not isinstance(d.get('Players', []), list):
                    return False
                # Missing/unknown playlist must never reveal the overlay.
                value = g.get('PlaylistId')
                self.playlist_id = int(value) if isinstance(value, (int, str)) and str(value).isdigit() else None
                for t in g.get('Teams', []):
                    i = t.get('TeamNum')
                    if i in (0, 1):
                        m['scores'][i] = max(0, int(t.get('Score', 0)))
                m['time'] = int(g.get('TimeSeconds', m['time']))
                if 'bOvertime' in g:
                    self.update_overtime(bool(g['bOvertime']))
                players = []
                for player in d.get('Players', []):
                    if not isinstance(player, dict) or player.get('TeamNum') not in (0, 1):
                        continue
                    player = dict(player)
                    # Live spectator packets omit Boost when it is zero. Only
                    # infer zero if spectator car telemetry is actually present.
                    if player.get('Boost') is None and any(key in player for key in
                            ('bHasCar', 'Speed', 'bBoosting', 'bOnGround', 'bOnWall', 'bDemolished')):
                        player['Boost'] = 0
                    players.append(player)
                m['players'] = players
                m['target'] = (g.get('Target') or {}).get('Name', '')
                self.last_update = time.monotonic()
            elif event == 'MatchCreated':
                self.overtime_started = False
                self.countdown_started = None
                self.overtime_until = 0
                m['overtime'] = False
                self.player_actions.clear()
                self.auto_camera_until = 0
                self.last_goal = None
                self.goal_armed = True
                self.in_goal_replay = False
                self.goal_until = 0
                self.playlist_id = None
                self.match_closed = False
                self.history_replay = False
                m['players'], m['target'], m['banner'] = [], '', ''
            elif event == 'ReplayCreated':
                self.player_actions.clear()
                self.auto_camera_until = 0
                self.last_goal = None
                self.history_replay = True
                self.goal_until = 0
            elif event == 'ClockUpdatedSeconds':
                m['time'] = int(d.get('TimeSeconds', 0))
                if 'bOvertime' in d:
                    self.update_overtime(bool(d['bOvertime']))
            elif event == 'CountdownBegin':
                self.countdown_started = time.monotonic()
                self.update_overtime(m['overtime'])
            elif event == 'GoalReplayStart':
                self.countdown_started = None
                self.overtime_until = 0
                self.player_actions.clear()
                self.in_goal_replay = True
                self.goal_armed = False
            elif event == 'GoalReplayEnd':
                if (self.in_goal_replay and self.last_goal is not None
                        and self.config['auto_replay_cameras'] and not self.match_closed
                        and not self.history_replay and self.playlist_id in PRIVATE_PLAYLISTS):
                    self.auto_camera_until = time.monotonic() + 6.5
                self.in_goal_replay = False
                self.last_goal = None
            elif event == 'PodiumStart':
                self.auto_camera_until = 0
                self.in_goal_replay = False
                self.last_goal = None
            elif event == 'RoundStarted':
                self.countdown_started = None
                self.overtime_until = 0
                self.player_actions.clear()
                self.in_goal_replay = False
                self.goal_armed = True
                self.last_goal = None
            elif event == 'StatfeedEvent':
                if (self.playlist_id in PRIVATE_PLAYLISTS and not self.history_replay and not self.match_closed
                        and not self.in_goal_replay and not d.get('bReplay') and self.config['show_player_actions']):
                    kinds = {'goal': 'goal', 'assist': 'assist', 'save': 'save', 'epicsave': 'save',
                             'shot': 'shot', 'shotongoal': 'shot', 'demolish': 'demo', 'demolition': 'demo'}
                    kind = kinds.get(str(d.get('EventName', '')).replace('_', '').lower())
                    if kind:
                        self.record_action(d.get('MainTarget'), kind)
                        if kind == 'demo' and isinstance(d.get('MainTarget'), dict):
                            self.record_action(d.get('SecondaryTarget'), 'demo-victim', attacker=d['MainTarget'])
            elif event == 'GoalScored':
                self.auto_camera_until = 0
                if (self.playlist_id in PRIVATE_PLAYLISTS and not self.history_replay
                        and not self.match_closed and self.goal_armed and not self.in_goal_replay):
                    self.goal_armed = False
                    scorer = d.get('Scorer')
                    if not isinstance(scorer, dict):
                        scorer = {}
                    if self.config['show_player_actions']:
                        self.record_action(scorer, 'goal')
                    team = scorer.get('TeamNum')
                    self.goal_team = 1 if team == 1 else 0
                    # GoalScored sends the goal speed in km/h in live packets;
                    # do not apply the uu/s conversion used by car/ball telemetry.
                    speed = d.get('GoalSpeed')
                    speed_kmh = (round(speed) if type(speed) in (int, float)
                                 and math.isfinite(speed) and speed >= 0 else None)
                    assister = d.get('Assister')
                    assist_name = assister.get('Name') if isinstance(assister, dict) else None
                    self.last_goal = {'name': scorer.get('Name') or '', 'team': team,
                                      'assist_name': assist_name.strip() if isinstance(assist_name, str) else '',
                                      'speed_kmh': speed_kmh}
                    if self.config['show_events']:
                        self.goal_sequence += 1
                        self.goal_until = time.monotonic() + 3
            elif event == 'MatchEnded':
                self.match_closed = True
                winner, guid = d.get('WinnerTeamNum'), d.get('MatchGuid')
                if winner in (0, 1):
                    m['banner'] = ''
                    if (self.config['auto_series'] and guid and guid not in self.finished
                            and self.playlist_id in PRIVATE_PLAYLISTS and not self.history_replay):
                        self.finished.add(guid)
                        if not series_state(self.config)['complete']:
                            self.config['teams'][winner]['wins'] += 1
            elif event == 'MatchDestroyed':
                self.overtime_started = False
                self.countdown_started = None
                self.overtime_until = 0
                m['overtime'] = False
                self.player_actions.clear()
                self.auto_camera_until = 0
                self.last_goal = None
                self.goal_until = 0
                self.playlist_id = None
                self.match_closed = True
                m['players'], m['target'] = [], ''
            else:
                return False
            return True


class GameConnection:
    """Official TCP Stats API; handles concatenated/fragmented JSON objects."""
    def __init__(self, store):
        self.store = store
        self.stop = threading.Event()
        self.thread = None

    def connect(self, port):
        self.disconnect()
        self.store.automatic = True
        self.store.last_update = 0
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, args=(port, self.stop), daemon=True)
        self.thread.start()

    def disconnect(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=2)
        self.store.status = 'Desconectado'
        self.store.automatic = False
        self.store.last_update = 0

    def run(self, port, stop):
        decoder = json.JSONDecoder()
        while not stop.is_set():
            self.store.status = 'Conectando a Rocket League…'
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1) as sock:
                    sock.settimeout(.5)
                    self.store.status = 'Conectado · esperando datos del partido'
                    buf = b''
                    while not stop.is_set():
                        try:
                            chunk = sock.recv(65536)
                        except socket.timeout:
                            if self.store.last_update and time.monotonic()-self.store.last_update > 5:
                                self.store.status = 'Conectado · sin datos recientes (menú o partido finalizado)'
                            continue
                        if not chunk:
                            break
                        buf += chunk
                        # Decode only complete UTF-8 sequences; JSON can span packets.
                        try:
                            text = buf.decode('utf-8')
                        except UnicodeDecodeError:
                            continue
                        text = text.lstrip('\x00\ufeff\r\n ')
                        while text:
                            try:
                                packet, end = decoder.raw_decode(text)
                            except json.JSONDecodeError:
                                break
                            if isinstance(packet, dict):
                                accepted = self.store.ingest(packet)
                                if accepted and packet.get('Event') == 'UpdateState':
                                    self.store.status = 'En directo · tiempo y goles sincronizados con Rocket League'
                                elif not accepted and packet.get('Event') == 'UpdateState':
                                    self.store.status = 'Conectado · actualización del juego no reconocida'
                            text = text[end:].lstrip('\x00\r\n ')
                        buf = text.encode('utf-8')
                        if len(buf) > 4_000_000:
                            raise ValueError('Formato TCP no reconocido')
            except (OSError, ValueError, TypeError) as exc:
                self.store.status = f'Sin conexión · {exc}'
            if not stop.is_set():
                self.store.last_update = 0
                self.store.status = 'Esperando Rocket League · reconexión automática'
                stop.wait(2)


def preview_snapshot(store, replay=False, overtime=False):
    """Example data for preview only; never writes to the live match or connection."""
    snapshot = store.snapshot()
    snapshot['overlay_visible'] = True
    snapshot['goal_replay_active'] = replay
    snapshot['overtime_remaining'] = 3000 if overtime else 0
    snapshot['goal_replay'] = {'name': 'PIRU', 'assist_name': 'CANDY', 'team': 0, 'speed_kmh': 104} if replay else None
    snapshot['match'] = {
        'scores': [2, 1], 'time': 0 if overtime else 193, 'overtime': overtime, 'target': 'PIRU', 'banner': '',
        'players': [{'Name': name, 'TeamNum': i//3, 'Boost': boost,
                     'Score': 541 if i == 0 else 125+i*32, 'Goals': 2 if i == 0 else i%2,
                     'Shots': 5, 'Assists': 1, 'Saves': 3}
                    for i, (name, boost) in enumerate([('PIRU', 72), ('CANDY', 38), ('FRESA', 100),
                                                      ('MANGO', 54), ('POP', 0), ('LIMÓN', 91)])]}
    for player, camera in zip(snapshot['match']['players'], snapshot['config']['cameras']):
        player['Name'] = camera['name']
    snapshot['match']['target'] = snapshot['match']['players'][0]['Name']
    sample_tick = int(time.monotonic() // 8)
    sample_remaining = max(0, int((4.5 - time.monotonic() % 8) * 1000))
    snapshot['player_actions'] = [dict(player, kind=kind, id=f'preview-{sample_tick}-{i}', remaining=sample_remaining)
                                  for i, (player, kind) in enumerate(zip(snapshot['match']['players'],
                                                                       ('goal', 'assist', 'save', 'shot', 'demo')))] if not replay else []
    if not replay:
        players = snapshot['match']['players']
        snapshot['player_actions'].append(dict(players[0], kind='shot', id=f'preview-{sample_tick}-shot', remaining=sample_remaining))
        snapshot['player_actions'].append(dict(players[2], kind='demo-victim', attacker=players[4],
                                               id=f'preview-{sample_tick}-victim', remaining=sample_remaining))
    if replay:
        snapshot['goal_replay']['name'] = snapshot['match']['target']
        snapshot['goal_replay']['assist_name'] = snapshot['match']['players'][1]['Name']
    return snapshot


def make_server(store, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            route = self.path.split('?')[0]
            if route in ('/state', '/preview-state'):
                query = dict(parse_qsl(urlsplit(self.path).query))
                state = (preview_snapshot(store, replay=query.get('replay') == '1',
                                          overtime=query.get('overtime') == '1')
                         if route == '/preview-state' else store.snapshot())
                for slot, sponsor in state['config']['sponsors'].items():
                    if sponsor['logo']:
                        sponsor['logo'] = f"/sponsor/{slot}?v={hash(sponsor['logo'])}"
                data = json.dumps(state, ensure_ascii=False).encode('utf-8')
                mime = 'application/json; charset=utf-8'
            elif route.startswith('/sponsor/'):
                slot = route.removeprefix('/sponsor/')
                with store.lock:
                    logo = store.config['sponsors'].get(slot, {}).get('logo', '')
                header, separator, content = logo.partition(',')
                if not separator or header not in ('data:image/png;base64', 'data:image/jpeg;base64'):
                    self.send_error(404)
                    return
                try:
                    data = base64.b64decode(content, validate=True)
                except (ValueError, binascii.Error):
                    self.send_error(404)
                    return
                mime = header.removeprefix('data:').split(';', 1)[0]
            elif route in ('/', '/overlay'):
                data = resource_path('overlay.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            elif route.startswith('/fonts/'):
                filename = unquote(route.removeprefix('/fonts/'))
                font = FONT_DIRECTORY / filename
                if (not filename or '/' in filename or '\\' in filename or ':' in filename
                        or font.suffix.lower() not in FONT_TYPES or font.is_symlink()):
                    self.send_error(404)
                    return
                try:
                    with font.open('rb') as file:
                        data = file.read(MAX_FONT_BYTES + 1)
                except OSError:
                    self.send_error(404)
                    return
                mime, signatures = FONT_TYPES[font.suffix.lower()]
                if len(data) > MAX_FONT_BYTES or not data.startswith(signatures):
                    self.send_error(404)
                    return
            elif route == '/assets/montserrat.ttf':
                data = resource_path('assets/montserrat.ttf').read_bytes()
                mime = 'font/ttf'
            elif route == '/boost-animation.js':
                data = resource_path('boost-animation.js').read_bytes()
                mime = 'application/javascript; charset=utf-8'
            elif route in ('/assets/torneo.png', '/assets/discord.png', '/assets/bigness-league.png', '/assets/rcs.png', '/assets/rck.png',
                           '/assets/action-goal.png', '/assets/action-assist.png', '/assets/action-save.png',
                           '/assets/action-shot.png', '/assets/action-demo.png'):
                data = resource_path(route.lstrip('/')).read_bytes()
                mime = 'image/png'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (ConnectionResetError, BrokenPipeError):
                pass
    class OverlayServer(ThreadingHTTPServer):
        allow_reuse_address = False

        def server_bind(self):
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    return OverlayServer(('127.0.0.1', port), Handler)


class App:
    def __init__(self, root):
        self.root, self.store = root, Store()
        self.connection = GameConnection(self.store)
        self.file = ROOT / 'ultimo_perfil.json'
        if self.file.exists():
            try:
                self.store.config = normalize_config(json.loads(self.file.read_text('utf-8')))
            except (ValueError, TypeError, KeyError):
                pass
        try:
            self.server = make_server(self.store, 18765)
        except OSError:
            self.server = make_server(self.store)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}/overlay'
        root.title(f'Piruleta - Overlay {APP_VERSION}')
        root.geometry('1280x850')
        root.minsize(1050, 850)
        root.configure(bg='#12101a')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#201b2c', foreground='#f7effa', font=('Segoe UI', 11))
        style.configure('TEntry', fieldbackground='#30283d', foreground='white', insertcolor='white')
        style.configure('TSpinbox', fieldbackground='#30283d', foreground='white', arrowsize=14)
        style.configure('TCombobox', fieldbackground='#30283d', foreground='white')
        style.map('TCombobox', fieldbackground=[('readonly', '#30283d')], foreground=[('readonly', 'white')])
        for control in ('TEntry', 'TSpinbox', 'TCombobox'):
            style.configure(control, padding=(7, 6))
        style.configure('TButton', padding=(14, 10), background='#3e304a')
        style.configure('Control.TButton', padding=(12, 6))
        style.map('TButton', background=[('active', '#75435d')])
        style.configure('TNotebook.Tab', padding=(15, 12))
        # Keep actual BooleanVars and keyboard-accessible checkbuttons, with a tick instead of clam's X.
        self.check_images = []
        for checked in (False, True):
            indicator = tk.PhotoImage(master=root, width=20, height=20)
            indicator.put('#201b2c', to=(0, 0, 20, 20))
            indicator.put('#fa54b7' if checked else '#796685', to=(1, 1, 19, 19))
            indicator.put('#fa54b7' if checked else '#181426', to=(3, 3, 17, 17))
            if checked:
                for x in range(4, 16):
                    y = x+5 if x < 8 else 20-x
                    indicator.put('white', to=(x, y-1, x+2, y+2))
            self.check_images.append(indicator)
        style.element_create('Piruleta.Check.indicator', 'image', self.check_images[0],
                             ('selected', self.check_images[1]), sticky='')
        style.layout('Piruleta.TCheckbutton', [('Checkbutton.padding', {'sticky': 'nswe', 'children': [
            ('Piruleta.Check.indicator', {'side': 'left', 'sticky': ''}),
            ('Checkbutton.label', {'side': 'left', 'sticky': 'nswe'})]})])
        style.configure('Piruleta.TCheckbutton', padding=(0, 6), background='#201b2c')
        # Blend the inherited hover highlight halfway into the panel background.
        hover = root.winfo_rgb(style.lookup('Piruleta.TCheckbutton', 'background', ('active',)))
        panel = root.winfo_rgb('#201b2c')
        softened_hover = '#' + ''.join(f'{round((a + b) / 2 / 257):02x}' for a, b in zip(hover, panel))
        style.map('Elementos.Piruleta.TCheckbutton', background=[('active', softened_hover)])
        self.vars, self.team_vars = {}, [{}, {}]
        head = tk.Frame(root, bg='#12101a')
        head.pack(fill='x', padx=24, pady=(20, 12))
        tk.Label(head, text='PIRULETA - Overlay', fg='#fa54b7', bg='#12101a', font=('Segoe UI', 23, 'bold')).pack(side='left')
        ttk.Button(head, text='Abrir vista previa', command=self.open_preview).pack(side='right', padx=4)
        ttk.Button(head, text='Copiar URL para OBS', command=self.copy_url).pack(side='right', padx=4)
        body = ttk.Frame(root)
        body.pack(fill='both', expand=True, padx=24)
        left = ttk.Frame(body, padding=12)
        left.pack(side='left', fill='both', expand=True)
        nb = ttk.Notebook(left)
        nb.pack(fill='both', expand=True, pady=(0, 14))
        teams, visibility_page, design_page, cameras, advertising = (
            ttk.Frame(nb, padding=20) for _ in range(5))
        nb.add(teams, text='Ajustes')
        nb.add(visibility_page, text='Elementos')
        nb.add(design_page, text='Diseño')
        nb.add(cameras, text='Cámaras')
        nb.add(advertising, text='Publicidad')
        self.build_advertising_tab(advertising)
        design_page.columnconfigure(0, weight=1, uniform='design-halves')
        design_page.columnconfigure(2, weight=1, uniform='design-halves')
        design_page.rowconfigure(0, weight=1)
        design = ttk.Frame(design_page)
        design.grid(row=0, column=0, sticky='nsew', padx=(0, 18))
        tk.Frame(design_page, bg='white', width=1).grid(row=0, column=1, sticky='ns')
        backgrounds = ttk.Frame(design_page)
        backgrounds.grid(row=0, column=2, sticky='nsew', padx=(18, 0))
        ttk.Label(backgrounds, text='Fondos', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 10))
        visibility = ttk.Frame(visibility_page)
        visibility.pack(fill='x')
        ttk.Label(visibility, text='General', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 10))
        camera_options = ttk.Frame(visibility_page)
        ttk.Label(camera_options, text='Cámaras', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))
        advertising_options = ttk.Frame(visibility_page)
        ttk.Label(advertising_options, text='Publicidad', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))
        for key, title in [('show_sponsor_rotation', 'Publicidad rotativa'),
                           ('show_sponsor_replay', 'Publicidad en repetición'),
                           ('show_sponsor_overtime', 'Publicidad en prórroga')]:
            variable = tk.BooleanVar(value=self.store.config[key])
            self.vars[key] = variable
            ttk.Checkbutton(advertising_options, text='  '+title, variable=variable,
                            command=self.apply, style='Elementos.Piruleta.TCheckbutton').pack(anchor='w', pady=3)
        self.palette_labels = {'dark': 'Fondo principal', 'pink': 'Equipo A', 'coral': 'Color central',
                               'yellow': 'Equipo B', 'text': 'Color del texto'}
        self.panel_color_vars = {}
        ttk.Label(backgrounds, text='Fondos vinculados a la paleta del marcador principal.').pack(anchor='w', pady=(0, 12))
        for key, label in [('boost0', 'Turbo · equipo A'), ('boost1', 'Turbo · equipo B'),
                           ('stats0', 'Estadísticas · equipo A'), ('stats1', 'Estadísticas · equipo B'),
                           ('players0', 'Jugadores equipo A'), ('players1', 'Jugadores equipo B')]:
            row = ttk.Frame(backgrounds)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label, width=23).pack(side='left')
            var = tk.StringVar(value=self.palette_labels[self.store.config['panel_colors'][key]])
            self.panel_color_vars[key] = var
            selector = ttk.Combobox(row, textvariable=var, state='readonly', values=list(self.palette_labels.values()))
            selector.pack(side='left', fill='x', expand=True)
            selector.bind('<<ComboboxSelected>>', lambda event: self.apply())
        self.vars['scoreboard_gradient'] = tk.BooleanVar(value=self.store.config['scoreboard_gradient'])
        ttk.Checkbutton(backgrounds, text='  Fondo del marcador en degradado (desmarcado: plano)',
                        variable=self.vars['scoreboard_gradient'], command=self.apply,
                        style='Elementos.Piruleta.TCheckbutton').pack(anchor='w', pady=6)
        ttk.Label(backgrounds, text='Al cambiar esos colores en Diseño, los fondos elegidos se actualizan también.',
                  wraplength=500, foreground='#b6a4c3').pack(anchor='w', pady=12)
        info_header = ttk.Frame(teams)
        info_header.pack(fill='x', pady=(0, 12))
        ttk.Label(info_header, text='Información del partido', font=('Segoe UI', 16, 'bold')).pack(side='left')
        ttk.Button(info_header, text='Configurar conexión al juego…', style='Control.TButton', command=lambda: self.setup_game_api(manual=True)).pack(side='right')
        match_info = ttk.Frame(teams)
        match_info.pack(fill='x')
        for column, weight in enumerate((1, 3, 4)):
            match_info.columnconfigure(column, weight=weight, uniform='matchinfo' if column > 0 else '')
        format_box = ttk.Frame(match_info)
        format_box.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        ttk.Label(format_box, text='Formato de la serie').pack(anchor='w', pady=(0, 5))
        self.format_var = tk.StringVar(value=f"BO{self.store.config['bestof']}")
        self.format_selector = ttk.Combobox(format_box, textvariable=self.format_var, state='readonly',
                                          values=[f'BO{n}' for n in SERIES_FORMATS], width=7)
        self.format_selector.pack(fill='x')
        self.format_selector.bind('<<ComboboxSelected>>', self.change_format)
        for column, key, title in [(1, 'round', 'Texto de abajo'), (2, 'event', 'Texto de arriba')]:
            box = ttk.Frame(match_info)
            box.grid(row=0, column=column, sticky='nsew', padx=(0, 8) if column == 1 else 0)
            ttk.Label(box, text=title).pack(anchor='w', pady=(0, 5))
            self.vars[key] = tk.StringVar(value=self.store.config[key])
            field = ttk.Entry(box, textvariable=self.vars[key], width=15)
            field.pack(fill='x', expand=True)
            field.bind('<Return>', lambda event: self.apply())
        ttk.Separator(teams).pack(fill='x', pady=10)
        team_actions = ttk.Frame(teams)
        team_actions.pack(fill='x')
        for style_name, color in [('ResetSeries', '#1675bb'), ('SwapTeams', '#198f86'), ('ClearTeams', '#bc0060')]:
            style.configure(style_name+'.TButton', background=color, foreground='white', padding=(12, 12))
            style.map(style_name+'.TButton', background=[('active', color)])
        for column, text, command, button_style in [
                (0, 'Reiniciar serie', self.reset_series, 'ResetSeries.TButton'),
                (1, 'Cambiar equipos de lado', self.swap_teams, 'SwapTeams.TButton'),
                (2, 'Borrar nombres y escudos', self.clear_teams, 'ClearTeams.TButton')]:
            team_actions.columnconfigure(column, weight=1, uniform='teamactions')
            ttk.Button(team_actions, text=text, command=command, style=button_style).grid(
                row=0, column=column, sticky='ew', padx=(0, 10) if column < 2 else 0)
        team_columns = ttk.Frame(teams)
        team_columns.pack(fill='both', expand=True, pady=(53, 0))
        self.score_labels, self.win_labels, self.logo_labels = [], [], []
        self.logo_images, self.logo_sources = {}, {}
        for i, title in enumerate(('Equipo azul', 'Equipo naranja')):
            team_columns.columnconfigure(i, weight=1, uniform='teams')
            card = ttk.LabelFrame(team_columns, text=title.upper(), padding=20)
            card.grid(row=0, column=i, sticky='nsew', padx=(0, 12) if i == 0 else (12, 0))
            series_row = ttk.Frame(card)
            series_row.pack(fill='x', pady=(0, 18))
            score_box = ttk.Frame(series_row)
            score_box.pack(side='left', fill='x', expand=True)
            ttk.Label(score_box, text='Victorias de serie', foreground='#b6a4c3').pack(anchor='w')
            controls = ttk.Frame(score_box)
            controls.pack(anchor='w', pady=(4, 0))
            label = ttk.Label(controls, text='Serie 0', font=('Segoe UI', 15, 'bold'), width=9)
            label.pack(side='left')
            self.win_labels.append(label)
            ttk.Button(controls, text='−', width=3, style='Control.TButton', command=lambda i=i: self.win(i, -1)).pack(side='left', padx=(0, 4))
            ttk.Button(controls, text='+', width=3, style='Control.TButton', command=lambda i=i: self.win(i, 1)).pack(side='left')
            logo_label = ttk.Label(series_row, text='Sin escudo', anchor='center', width=12)
            logo_label.pack(side='right', padx=(12, 0))
            self.logo_labels.append(logo_label)
            ttk.Label(card, text='Nombre del equipo').pack(anchor='w')
            variable = tk.StringVar(value=self.store.config['teams'][i]['name'])
            self.team_vars[i]['name'] = variable
            ttk.Entry(card, textvariable=variable).pack(fill='x', pady=(7, 16))
            logo_actions = ttk.Frame(card)
            logo_actions.pack(fill='x')
            ttk.Button(logo_actions, text='Subir escudo…', command=lambda i=i: self.logo(i)).pack(side='left', fill='x', expand=True, padx=(0, 8))
            ttk.Button(logo_actions, text='Quitar escudo', command=lambda i=i: self.clear_logo(i)).pack(side='left')
            goals = ttk.Frame(card)
            goals.pack(fill='x', pady=(12, 0))
            ttk.Label(goals, text='Goles del partido · API', foreground='#b6a4c3').pack(side='left')
            label = ttk.Label(goals, text='0', font=('Segoe UI', 18, 'bold'))
            label.pack(side='right')
            self.score_labels.append(label)
        self.series_hint = ttk.Label(teams, foreground='#ffce72', anchor='center')
        self.series_hint.pack(fill='x', pady=(14, 4))
        self.series_hint.bind('<Configure>', lambda event: self.series_hint.configure(wraplength=max(100, event.width)))
        ttk.Label(teams, text='[GAME]: partido actual · [SERIE]: formato de la serie. Tiempo y goles sincronizados por la API.',
                  foreground='#b6a4c3', anchor='center').pack(fill='x', pady=(0, 16))
        ttk.Label(design, text='Colores', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 10))
        colorrow = ttk.Frame(design)
        colorrow.pack(fill='x', pady=(0, 10))
        for column in range(3):
            colorrow.columnconfigure(column, weight=1, uniform='palette-buttons')
        for index, (key, title) in enumerate([('pink', 'Equipo azul'), ('coral', 'Coral'),
                                             ('yellow', 'Equipo naranja'), ('dark', 'Fondo'), ('text', 'Texto')]):
            ttk.Button(colorrow, text=title, command=lambda k=key: self.color(k)).grid(
                row=index//3, column=index%3, sticky='ew', padx=3, pady=4)
        ttk.Label(design, text='Estilos, tipografía y escala', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(12, 10))
        self.entry(design, 'Estilo', 'design', choices=DESIGNS)
        self.font_selector = self.entry(design, 'Tipografía', 'font', choices=self.font_choices())
        ttk.Button(self.font_selector.master, text='Importar fuente…', command=self.import_font).pack(side='left', padx=(8, 0))
        self.entry(design, 'Escala (%)', 'scale', numeric=(50, 150))
        for k, label in [('show_logos', 'Escudos de equipos'), ('show_players', 'Turbo de todos los jugadores'), ('show_boost', 'Turbo del jugador en cámara'), ('show_player_actions', 'Iconos de acciones'), ('show_goal_replay', 'Barra de repetición de gol'), ('auto_series', 'Sumar victorias automáticamente (API)')]:
            v = tk.BooleanVar(value=self.store.config[k])
            self.vars[k] = v
            ttk.Checkbutton(visibility, text='  '+label, variable=v, command=self.apply,
                            style='Elementos.Piruleta.TCheckbutton').pack(anchor='w', pady=2)
        for key, label in [('show_stats_camera', 'Cámara estadísticas'),
                           ('show_players_cameras', 'Cámaras turbos'),
                           ('auto_replay_cameras', 'Mostrar cámaras turbos durante 6,5 s al terminar la repetición')]:
            variable = tk.BooleanVar(value=self.store.config[key])
            self.vars[key] = variable
            ttk.Checkbutton(camera_options, text='  '+label, variable=variable,
                            command=lambda key=key: self.change_camera_mode(key),
                            style='Elementos.Piruleta.TCheckbutton').pack(anchor='w', pady=5)
        ttk.Label(cameras, text='Nombre del jugador en Rocket League y enlace de visualización OBS Ninja / VDO.Ninja.',
                  wraplength=600, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))
        camera_fields = ttk.Frame(cameras)
        camera_fields.pack(fill='both', expand=True)
        camera_fields.columnconfigure(1, weight=1)
        ttk.Label(camera_fields, text='Jugador').grid(row=0, column=0, sticky='w')
        ttk.Label(camera_fields, text='Enlace (?view=...)').grid(row=0, column=1, sticky='w')
        self.camera_vars = []
        for index in range(8):
            camera = self.store.config['cameras'][index] if index < len(self.store.config['cameras']) else {}
            name = tk.StringVar(value=camera.get('name', ''))
            url = tk.StringVar(value=camera.get('url', ''))
            ttk.Entry(camera_fields, textvariable=name, width=22).grid(row=index+1, column=0, sticky='ew', padx=(0, 10), pady=5)
            ttk.Entry(camera_fields, textvariable=url, width=35).grid(row=index+1, column=1, sticky='ew', pady=5)
            self.camera_vars.append((name, url))
        stats_row = ttk.Frame(visibility)
        stats_row.pack(fill='x', pady=3)
        self.vars['show_stats'] = tk.BooleanVar(value=self.store.config['show_stats'])
        ttk.Checkbutton(stats_row, text='  Mostrar estadísticas', variable=self.vars['show_stats'],
                        command=self.apply, style='Elementos.Piruleta.TCheckbutton').pack(side='left', padx=(0, 8))
        self.vars['stats_style'] = tk.StringVar(value=self.store.config['stats_style'])
        stats_selector = ttk.Combobox(stats_row, textvariable=self.vars['stats_style'],
                                     values=STATS_STYLES, state='readonly', width=18)
        stats_selector.pack(side='left', fill='x', expand=True)
        stats_selector.bind('<<ComboboxSelected>>', lambda event: self.apply())

        curtain_row = ttk.Frame(visibility)
        curtain_row.pack(fill='x', pady=3)
        self.vars['show_events'] = tk.BooleanVar(value=self.store.config['show_events'])
        ttk.Checkbutton(curtain_row, text='  Cortina de gol', variable=self.vars['show_events'],
                        command=self.apply, style='Elementos.Piruleta.TCheckbutton').pack(side='left', padx=(0, 8))
        self.vars['goal_style'] = tk.StringVar(value=self.store.config['goal_style'])
        curtain_selector = ttk.Combobox(curtain_row, textvariable=self.vars['goal_style'],
                                       values=['Torneo Piruleta', 'Bigness League', 'RCS', 'RCK'], state='readonly', width=18)
        curtain_selector.pack(side='left', fill='x', expand=True)
        curtain_selector.bind('<<ComboboxSelected>>', lambda event: self.apply())
        ttk.Button(curtain_row, text='Probar cortina', style='Control.TButton',
                   command=self.preview_goal).pack(side='left', padx=(5, 0))
        camera_options.pack(fill='x', pady=(18, 0))
        advertising_options.pack(fill='x', pady=(18, 0))
        actions = ttk.Frame(left)
        actions.pack(side='bottom', fill='x', before=nb)
        ttk.Button(actions, text='Aplicar cambios', style='Control.TButton', command=self.apply).pack(side='right')
        ttk.Button(actions, text='Guardar perfil…', style='Control.TButton', command=self.save).pack(side='left', padx=(0, 8))
        ttk.Button(actions, text='Cargar perfil…', style='Control.TButton', command=self.load).pack(side='left')
        footer = tk.Frame(root, bg='#12101a', padx=24, pady=8)
        footer.pack(side='bottom', fill='x', before=body)
        self.credits = tk.Label(footer, text=f'Versión {APP_VERSION}\nAplicación desarrollada por Bruno Reboredo Álvarez',
                                bg='#12101a', fg='#b6a4c3', font=('Segoe UI', 9), justify='right', anchor='e')
        self.credits.pack(side='right', anchor='se', padx=(16, 0))
        self.status = tk.Label(footer, bg='#12101a', fg='#ffce72', anchor='w', justify='left', width=1)
        self.status.pack(side='left', fill='both', expand=True)
        self.status.bind('<Configure>', lambda event: self.status.configure(wraplength=max(100, event.width)))
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        root.update_idletasks()
        available_width = root.winfo_screenwidth() - 40
        available_height = root.winfo_screenheight() - 80
        width = min(1280, available_width)
        height = min(max(940, root.winfo_reqheight()), available_height)
        root.minsize(min(1050, width), min(900, height))
        root.geometry(f'{width}x{height}')
        self.connect()
        self.refresh()
        self.root.after(500, self.setup_game_api)

    def setup_game_api(self, manual=False):
        settings = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'PiruletaOverlay' / 'game-api.json'
        previous = {}
        try:
            previous = json.loads(settings.read_text('utf-8'))
        except (OSError, ValueError):
            pass
        cached = Path(previous.get('path', ''))
        path = cached if cached.is_file() else discover_stats_ini()
        if manual or (path is None and not previous.get('prompted')):
            folder = filedialog.askdirectory(parent=self.root, title='Selecciona la carpeta de instalación de Rocket League para activar los datos del juego')
            if folder:
                path = find_stats_ini(folder)
                if path is None:
                    messagebox.showwarning('Rocket League', 'No se encuentra TAGame/Config/TAStatsAPI.ini ni DefaultStatsAPI.ini en esa carpeta. Puedes volver a intentarlo con Configurar conexión al juego.', parent=self.root)
        try:
            if path:
                backup, port = enable_stats_api(path)
                with self.store.lock:
                    changed_port = self.store.config['api_port'] != port
                    self.store.config['api_port'] = port
                if changed_port:
                    self.connect()
                previous['path'] = str(path)
                if backup or manual:
                    detail = f'\nCopia de seguridad: {backup}' if backup else ''
                    messagebox.showinfo('Conexión preparada', 'La API de Rocket League está activada. Si el juego estaba abierto, ciérralo y vuelve a abrirlo para que aplique la configuración.' + detail, parent=self.root)
            previous['prompted'] = True
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps(previous), 'utf-8')
        except OSError as exc:
            messagebox.showerror('No se pudo preparar la conexión', 'No se ha podido configurar el archivo del juego. Si Windows deniega el acceso, cierra la app y ábrela una vez como administrador. Después pulsa Configurar conexión al juego.\n\n' + str(exc), parent=self.root)

    def build_advertising_tab(self, parent):
        canvas = tk.Canvas(parent, bg='#201b2c', highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        content = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        self.advertising_canvas = canvas
        ttk.Label(content, text='Patrocinadores rotativos', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(12, 8))
        self.entry(content, 'Intervalo de rotación (s)', 'sponsor_interval', numeric=(3, 60))
        self.rotation_fields = ttk.Frame(content)
        self.rotation_fields.pack(fill='x')
        sponsor_buttons = ttk.Frame(content)
        sponsor_buttons.pack(fill='x', pady=(8, 18))
        self.add_sponsor_button = ttk.Button(sponsor_buttons, text='+ Añadir patrocinador rotativo', command=self.add_rotating_sponsor)
        self.add_sponsor_button.pack(side='left', padx=(0, 10))
        self.remove_sponsor_button = ttk.Button(sponsor_buttons, text='− Quitar último patrocinador', command=self.remove_last_sponsor)
        self.remove_sponsor_button.pack(side='left')
        ttk.Label(content, text='Patrocinadores de jugadas', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))
        self.event_sponsor_fields = ttk.Frame(content)
        self.event_sponsor_fields.pack(fill='x')
        self.rebuild_sponsor_rows(self.store.config)
        ttk.Label(content, text='Escribe un nombre, añade un logo o combina ambos. Deja la fila vacía para ocultarla.',
                  wraplength=650).pack(anchor='w', pady=(12, 8))
        previews = ttk.Frame(content)
        previews.pack(anchor='w')
        ttk.Button(previews, text='Vista previa de prórroga',
                   command=lambda: self.preview_sponsor('overtime')).pack(side='left', padx=(0, 8))
        ttk.Button(previews, text='Vista previa de repetición',
                   command=lambda: self.preview_sponsor('replay')).pack(side='left')
        self.bind_advertising_scroll(parent)

    def bind_advertising_scroll(self, widget):
        widget.bind('<MouseWheel>', lambda event: self.advertising_canvas.yview_scroll(-int(event.delta / 120), 'units'))
        for child in widget.winfo_children():
            self.bind_advertising_scroll(child)

    def build_sponsor_row(self, parent, slot, label, sponsor):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=2)
        ttk.Label(row, text=label, width=12).pack(side='left')
        name = tk.StringVar(value=sponsor.get('name', ''))
        logo = tk.StringVar(value=sponsor.get('logo', ''))
        status = tk.StringVar()
        self.sponsor_vars[slot] = (name, logo)
        ttk.Entry(row, textvariable=name, width=20).pack(side='left', fill='x', expand=True)
        ttk.Button(row, textvariable=status, style='Control.TButton',
                   command=lambda: self.choose_sponsor_logo(logo)).pack(side='left', padx=4)
        ttk.Button(row, text='Quitar logo', style='Control.TButton', command=lambda: logo.set('')).pack(side='left')
        def refresh_logo(*_):
            status.set('Cambiar logo…' if logo.get() else 'Añadir logo…')
        logo.trace_add('write', refresh_logo)
        refresh_logo()
        self.bind_advertising_scroll(row)

    def rebuild_sponsor_rows(self, config):
        for parent in (self.rotation_fields, self.event_sponsor_fields):
            for child in parent.winfo_children():
                child.destroy()
        self.sponsor_vars = {}
        self.rotation_count = config['sponsor_rotation_count']
        for i in range(1, self.rotation_count+1):
            slot = f'rotation{i}'
            self.build_sponsor_row(self.rotation_fields, slot, f'Anuncio {i}', config['sponsors'][slot])
        for slot, title in [('overtime', 'Prórroga'), ('replay', 'Repetición')]:
            self.build_sponsor_row(self.event_sponsor_fields, slot, title, config['sponsors'][slot])
        self.add_sponsor_button.configure(state='disabled' if self.rotation_count >= MAX_ROTATING_SPONSORS else 'normal')
        self.remove_sponsor_button.configure(state='disabled' if self.rotation_count <= MIN_ROTATING_SPONSORS else 'normal')

    def add_rotating_sponsor(self):
        if self.rotation_count >= MAX_ROTATING_SPONSORS:
            return
        self.rotation_count += 1
        self.build_sponsor_row(self.rotation_fields, f'rotation{self.rotation_count}', f'Anuncio {self.rotation_count}', {})
        self.add_sponsor_button.configure(state='disabled' if self.rotation_count >= MAX_ROTATING_SPONSORS else 'normal')
        self.remove_sponsor_button.configure(state='disabled' if self.rotation_count <= MIN_ROTATING_SPONSORS else 'normal')

    def remove_last_sponsor(self):
        if self.rotation_count <= MIN_ROTATING_SPONSORS:
            return
        self.sponsor_vars.pop(f'rotation{self.rotation_count}')
        self.rotation_fields.winfo_children()[-1].destroy()
        self.rotation_count -= 1
        self.add_sponsor_button.configure(state='normal')
        self.remove_sponsor_button.configure(state='disabled' if self.rotation_count <= MIN_ROTATING_SPONSORS else 'normal')

    def choose_sponsor_logo(self, variable):
        filename = filedialog.askopenfilename(filetypes=[('Imagen PNG / JPG', '*.png *.jpg *.jpeg')])
        if not filename:
            return
        try:
            path = Path(filename)
            mime = SPONSOR_IMAGE_TYPES.get(path.suffix.lower())
            with path.open('rb') as image:
                data = image.read(MAX_LOGO_BYTES + 1)
            signature = b'\x89PNG\r\n\x1a\n' if mime == 'image/png' else b'\xff\xd8\xff'
            if not mime or not data.startswith(signature) or len(data) > MAX_LOGO_BYTES:
                raise ValueError('Elige un archivo PNG o JPEG de 4 MB como máximo.')
            variable.set(f'data:{mime};base64,' + base64.b64encode(data).decode('ascii'))
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudo cargar el logo', str(exc), parent=self.root)

    def preview_sponsor(self, event):
        if self.apply():
            self.open_browser(f'{self.url}?preview=1&{event}=1&v={time.time_ns()}')

    def entry(self, parent, title, key, numeric=None, choices=None):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=7)
        ttk.Label(row, text=title, width=23).pack(side='left')
        v = tk.StringVar(value=str(self.store.config[key]))
        self.vars[key] = v
        if numeric:
            w = ttk.Spinbox(row, from_=numeric[0], to=numeric[1], textvariable=v, width=10)
        elif choices:
            w = ttk.Combobox(row, values=choices, textvariable=v, state='readonly')
            w.bind('<<ComboboxSelected>>', lambda e: self.apply())
        else:
            w = ttk.Entry(row, textvariable=v)
        w.pack(side='left', fill='x', expand=True)
        w.bind('<Return>', lambda e: self.apply())
        return w

    @staticmethod
    def font_choices():
        imported = sorted(
            CUSTOM_FONT_PREFIX + path.name
            for path in FONT_DIRECTORY.glob('*')
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in FONT_TYPES
        )
        return (*STANDARD_FONTS, *imported)

    def import_font(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title='Importar tipografía',
            filetypes=[('Fuentes', '*.ttf *.otf *.woff *.woff2')],
        )
        if not filename:
            return
        source = Path(filename)
        extension = source.suffix.lower()
        try:
            if extension not in FONT_TYPES:
                raise ValueError('Elige un archivo TTF, OTF, WOFF o WOFF2.')
            with source.open('rb') as file:
                data = file.read(MAX_FONT_BYTES + 1)
            if len(data) > MAX_FONT_BYTES or not data.startswith(FONT_TYPES[extension][1]):
                raise ValueError('La fuente debe tener un formato válido y ocupar como máximo 16 MB.')
            FONT_DIRECTORY.mkdir(parents=True, exist_ok=True)
            stem = source.stem[:80]
            target = FONT_DIRECTORY / (stem + extension)
            number = 2
            while target.exists():
                target = FONT_DIRECTORY / f'{stem} ({number}){extension}'
                number += 1
            with target.open('xb') as file:
                file.write(data)
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudo importar la tipografía', str(exc), parent=self.root)
            return
        self.font_selector.configure(values=self.font_choices())
        self.vars['font'].set(CUSTOM_FONT_PREFIX + target.name)
        self.apply()

    def change_camera_mode(self, key):
        other = {'show_stats_camera': 'show_players_cameras',
                 'show_players_cameras': 'show_stats_camera'}.get(key)
        if other and self.vars[key].get():
            self.vars[other].set(False)
        self.apply()

    def apply(self):
        try:
            with self.store.lock:
                raw = copy.deepcopy(self.store.config)
                for k, v in self.vars.items():
                    raw[k] = v.get()
                for i in range(2):
                    raw['teams'][i]['name'] = self.team_vars[i]['name'].get()
                raw['cameras'] = [{'name': name.get(), 'url': url.get()} for name, url in self.camera_vars]
                raw['sponsor_rotation_count'] = self.rotation_count
                raw['sponsors'] = {slot: {'name': name.get(), 'logo': logo.get()}
                                   for slot, (name, logo) in self.sponsor_vars.items()}
                palette_keys = {label: key for key, label in self.palette_labels.items()}
                raw['panel_colors'] = {key: palette_keys[var.get()] for key, var in self.panel_color_vars.items()}
                changed_layout = design_group(raw['design']) != design_group(self.store.config['design'])
                raw = switch_design(raw, self.store.config['design'])
                self.store.config = normalize_config(raw)
            if changed_layout:
                self.sync()
            self.refresh_match_controls()
            return True
        except (ValueError, TypeError) as exc:
            messagebox.showerror('Revisa el diseño', str(exc))
            return False

    def sync(self):
        c = self.store.config
        self.format_var.set(f"BO{c['bestof']}")
        for k, v in self.vars.items():
            v.set(c[k])
        for key, var in self.panel_color_vars.items():
            var.set(self.palette_labels[c['panel_colors'][key]])
        for i in range(2):
            self.team_vars[i]['name'].set(c['teams'][i]['name'])
        for index, (name, url) in enumerate(self.camera_vars):
            camera = c['cameras'][index] if index < len(c['cameras']) else {}
            name.set(camera.get('name', ''))
            url.set(camera.get('url', ''))
        self.rebuild_sponsor_rows(c)
        self.refresh_match_controls()

    def color(self, key):
        dialog = tk.Toplevel(self.root, bg='#201b2c')
        dialog.title('Elegir color')
        dialog.transient(self.root)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill='both', expand=True)

        value = tk.StringVar(dialog, value=self.store.config['colors'][key])
        ttk.Label(frame, text='Color hexadecimal').pack(anchor='w')
        field = ttk.Entry(frame, textvariable=value, width=22)
        field.pack(fill='x', pady=(5, 8))
        error = ttk.Label(frame, foreground='#ffce72')
        error.pack(anchor='w')

        def apply_color(event=None):
            match = re.fullmatch(r'#?([0-9a-fA-F]{6})', value.get().strip())
            if not match:
                error.configure(text='Escribe seis dígitos, por ejemplo #BEB4E6.')
                field.focus_set()
                return
            with self.store.lock:
                self.store.config['colors'][key] = '#' + match[1].upper()
            dialog.destroy()

        def choose_color():
            initial = value.get().strip()
            if re.fullmatch(r'#?[0-9a-fA-F]{6}', initial):
                initial = '#' + initial.lstrip('#')
            else:
                initial = self.store.config['colors'][key]
            selected = colorchooser.askcolor(initial, parent=dialog)[1]
            if selected:
                value.set(selected)
                error.configure(text='')

        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=(8, 0))
        ttk.Button(buttons, text='Selector visual…', command=choose_color).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Cancelar', command=dialog.destroy).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Aplicar', command=apply_color).pack(side='right')
        dialog.bind('<Return>', apply_color)
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        dialog.wait_visibility()
        dialog.grab_set()
        field.focus_set()
        field.selection_range(0, 'end')

    def logo(self, i):
        import base64
        path = filedialog.askopenfilename(filetypes=[('Imagen PNG / JPG', '*.png *.jpg *.jpeg')])
        if path:
            data = Path(path).read_bytes()
            if len(data) > MAX_LOGO_BYTES:
                messagebox.showerror('Imagen grande', 'El tamaño máximo del escudo es de 4 MB.')
                return
            mime = 'image/png' if Path(path).suffix.lower() == '.png' else 'image/jpeg'
            with self.store.lock:
                self.store.config['teams'][i]['logo'] = f'data:{mime};base64,' + base64.b64encode(data).decode()

    def clear_logo(self, i):
        with self.store.lock:
            self.store.config['teams'][i]['logo'] = ''

    def open_browser(self, url):
        try:
            if os.name == 'nt':
                try:
                    os.startfile(url)
                    return True
                except OSError:
                    pass
            if webbrowser.open(url, new=2):
                return True
        except (OSError, webbrowser.Error):
            pass
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        messagebox.showerror('No se pudo abrir el navegador',
                             'He copiado el enlace de la vista previa. Pégalo en tu navegador para abrirlo.',
                             parent=self.root)
        return False

    def open_preview(self):
        if self.apply():
            revision = time.time_ns()
            self.open_browser(self.url + '?preview=1&v=' + str(revision))

    def preview_goal(self):
        if self.apply():
            style = {'Bigness League': 'bigness', 'RCS': 'rcs', 'RCK': 'rck'}.get(self.store.config['goal_style'], 'original')
            self.open_browser(self.url+'?preview=1&goal=1&curtain='+style)

    def clear_teams(self):
        for team in self.team_vars:
            team['name'].set('')
        with self.store.lock:
            for team in self.store.config['teams']:
                team['logo'] = ''
        self.apply()

    def swap_teams(self):
        if not self.apply():
            return
        with self.store.lock:
            self.store.config = swap_team_sides(self.store.config)
        self.sync()

    def win(self, i, delta):
        with self.store.lock:
            state = series_state(self.store.config)
            if delta > 0 and state['complete']:
                return
            t = self.store.config['teams'][i]
            t['wins'] = max(0, min(self.store.config['bestof']//2+1, t['wins']+delta))
        self.refresh_match_controls()

    def change_format(self, event=None):
        bestof = int(self.format_var.get()[2:])
        with self.store.lock:
            raw = copy.deepcopy(self.store.config)
            raw['bestof'] = bestof
            try:
                if (sum(t['wins'] for t in raw['teams']) > bestof or
                        max(t['wins'] for t in raw['teams']) > bestof//2+1):
                    raise ValueError('El resultado no cabe en este formato.')
                updated = normalize_config(raw)
            except ValueError:
                self.format_var.set(f"BO{self.store.config['bestof']}")
                messagebox.showinfo('Formato de la serie',
                                    'Reinicia la serie antes de elegir un formato menor que el resultado actual.')
                return
            self.store.config = updated
        self.refresh_match_controls()

    def reset_series(self):
        with self.store.lock:
            for team in self.store.config['teams']:
                team['wins'] = 0
        self.refresh_match_controls()

    def connect(self):
        self.connection.connect(self.store.config['api_port'])

    def copy_url(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url)
        messagebox.showinfo('URL copiada', self.url+'\n\nOBS → Fuente de navegador → 1920 × 1080.\nMantén Piruleta - Overlay abierto.')

    def save(self):
        if not self.apply():
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Perfil Piruleta', '*.json')])
        if path:
            Path(path).write_text(json.dumps(self.store.snapshot()['config'], ensure_ascii=False, indent=2), 'utf-8')

    def load(self):
        path = filedialog.askopenfilename(filetypes=[('Perfil Piruleta', '*.json')])
        if path:
            try:
                c = normalize_config(json.loads(Path(path).read_text('utf-8')))
                previous_port = self.store.config['api_port']
                with self.store.lock:
                    self.store.config = c
                self.sync()
                if c['api_port'] != previous_port:
                    self.connect()
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                messagebox.showerror('No se pudo cargar', str(exc))

    def refresh_match_controls(self):
        snapshot = self.store.snapshot()
        c, m = snapshot['config'], snapshot['match']
        for i in range(2):
            source = c['teams'][i]['logo']
            if self.logo_sources.get(i) != source:
                self.logo_sources[i] = source
                self.logo_images.pop(i, None)
                try:
                    image = tk.PhotoImage(master=self.root, data=source.split(',', 1)[1]) if source else None
                    if image:
                        image = image.subsample(max(1, math.ceil(max(image.width(), image.height()) / 64)))
                        self.logo_images[i] = image
                    self.logo_labels[i].configure(image=image or '', text='' if image else 'Sin escudo', width=0 if image else 12)
                except (tk.TclError, IndexError):
                    self.logo_labels[i].configure(image='', text='Escudo cargado', width=14)
            self.score_labels[i].configure(text=str(m['scores'][i]))
            self.win_labels[i].configure(text=f"Serie {c['teams'][i]['wins']}")
        state = snapshot['series']
        hint = f"BO{c['bestof']} · {state['target']} victorias para ganar"
        if c['bestof'] % 2 == 0:
            hint += f" · hasta {c['bestof']} partidos; admite empate"
        if state['complete']:
            hint += ' · EMPATE' if state['tied'] else ' · SERIE FINALIZADA'
        self.series_hint.configure(text=hint)

    def refresh(self):
        self.status.configure(text='● '+self.store.status+'     |     OBS: '+self.url)
        self.refresh_match_controls()
        self.root.after(250, self.refresh)

    def close(self):
        if self.apply():
            self.file.write_text(json.dumps(self.store.snapshot()['config'], ensure_ascii=False, indent=2), 'utf-8')
        self.connection.disconnect()
        self.server.shutdown()
        self.root.destroy()


def main():
    if os.name != 'nt':
        App(tk.Tk()).root.mainloop()
        return

    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create_mutex = kernel.CreateMutexW
    create_mutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    create_mutex.restype = wintypes.HANDLE
    close_handle = kernel.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    handle = create_mutex(None, False, r'Local\PiruletaOverlay')
    already_running = ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if already_running:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo('Piruleta - Overlay', 'La aplicación ya está abierta. Usa esa ventana para aplicar los cambios.', parent=root)
            root.destroy()
            return
        App(tk.Tk()).root.mainloop()
    finally:
        close_handle(handle)


if __name__ == '__main__':
    main()
