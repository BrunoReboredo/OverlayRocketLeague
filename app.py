"""Piruleta Scoreboard. Python 3.11+, standard library only."""
import copy
import json
from pathlib import Path
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser
from api_config import enable_stats_api

ROOT = Path(__file__).resolve().parent
SERIES_FORMATS = (1, 2, 3, 4, 5, 7)


def series_state(config):
    bestof = config['bestof']
    wins = [team['wins'] for team in config['teams']]
    target = bestof//2 + 1
    complete = max(wins) >= target or sum(wins) >= bestof
    tied = complete and wins[0] == wins[1]
    return {'target': target, 'complete': complete, 'tied': tied,
            'game': min(bestof, sum(wins) + (0 if complete else 1)),
            'slots': target}


DEFAULT = {
    'event': 'TORNEO PIRULETA', 'round': 'GRAN FINAL', 'game': 1, 'bestof': 5,
    'teams': [{'name': 'PINK CANDY', 'logo': '', 'wins': 0},
              {'name': 'GOLDEN POP', 'logo': '', 'wins': 0}],
    'colors': {'pink': '#fa54b7', 'coral': '#ff8875', 'yellow': '#ffd14c',
               'dark': '#181426', 'text': '#ffffff'},
    'show_logos': True, 'show_players': True, 'show_stats': True,
    'show_boost': True, 'show_brand': True, 'show_events': True,
    'design': 'angular', 'font': 'Arial', 'scale': 100, 'opacity': 100,
    'x': 360, 'y': 24, 'auto_series': True, 'custom_css': '',
    'panels': {'players0': [24, 235, 100], 'players1': [1601, 235, 100],
               'focus': [36, 880, 100], 'boost': [1730, 895, 100],
               'brand': [820, 178, 100], 'banner': [460, 370, 100]},
}


def normalize_config(raw):
    """Validate profiles before they reach widgets or the overlay."""
    if not isinstance(raw, dict):
        raise ValueError('El perfil debe ser un objeto JSON.')
    c = copy.deepcopy(DEFAULT)
    for key in ('event', 'round', 'font'):
        if key in raw:
            c[key] = str(raw[key])[:120]
    for key, lo, hi in [('game', 1, 99), ('bestof', 1, 15), ('scale', 50, 150),
                        ('opacity', 10, 100), ('x', 0, 1900), ('y', 0, 1000)]:
        c[key] = max(lo, min(hi, int(raw.get(key, c[key]))))
    if c['bestof'] not in SERIES_FORMATS:
        raise ValueError('Elige BO1, BO2, BO3, BO4, BO5 o BO7.')
    c['game'] = min(c['game'], c['bestof'])
    for key in c:
        if key.startswith('show_') or key == 'auto_series':
            c[key] = bool(raw.get(key, c[key]))
    if raw.get('design') in ('angular', 'rounded', 'classic'):
        c['design'] = raw['design']
    c['custom_css'] = str(raw.get('custom_css', ''))[:50000]
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
                         'logo': str(team.get('logo', ''))[:2000000],
                         'wins': max(0, min(c['bestof']//2+1, int(team.get('wins', 0))))}
    if sum(t['wins'] for t in c['teams']) > c['bestof']:
        raise ValueError('Las victorias superan los partidos del formato. Reinicia la serie antes de cambiarlo.')
    return c


class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.config = copy.deepcopy(DEFAULT)
        self.match = {'scores': [0, 0], 'time': 300, 'overtime': False,
                      'players': [], 'target': '', 'banner': ''}
        self.status = 'Manual · sin conexión al juego'
        self.finished = set()
        self.banner_until = 0
        self.automatic = False
        self.last_update = 0

    def snapshot(self):
        with self.lock:
            if time.monotonic() > self.banner_until:
                self.match['banner'] = ''
            return copy.deepcopy({'config': self.config, 'match': self.match,
                                  'series': series_state(self.config),
                                  'connection': {'automatic': self.automatic,
                                                 'receiving': self.last_update > 0 and time.monotonic()-self.last_update < 5,
                                                 'status': self.status}})

    def ingest(self, packet):
        event, d = packet.get('Event'), packet.get('Data', {})
        if not isinstance(d, dict):
            return
        with self.lock:
            m = self.match
            if event == 'UpdateState':
                self.last_update = time.monotonic()
                g = d.get('Game', {})
                for t in g.get('Teams', []):
                    i = t.get('TeamNum')
                    if i in (0, 1):
                        m['scores'][i] = max(0, int(t.get('Score', 0)))
                m['time'] = int(g.get('TimeSeconds', m['time']))
                m['overtime'] = bool(g.get('bOvertime', False))
                m['players'] = [p for p in d.get('Players', []) if p.get('TeamNum') in (0, 1)]
                m['target'] = g.get('Target', {}).get('Name', '')
            elif event == 'ClockUpdatedSeconds':
                m['time'] = int(d.get('TimeSeconds', 0))
                m['overtime'] = bool(d.get('bOvertime', False))
            elif event == 'GoalScored':
                m['banner'] = '¡GOL! · ' + d.get('Scorer', {}).get('Name', '')
                self.banner_until = time.monotonic() + 4
            elif event == 'MatchEnded':
                winner, guid = d.get('WinnerTeamNum'), d.get('MatchGuid')
                if winner in (0, 1):
                    m['banner'] = 'VICTORIA · ' + self.config['teams'][winner]['name']
                    self.banner_until = time.monotonic() + 12
                    if self.config['auto_series'] and guid and guid not in self.finished:
                        self.finished.add(guid)
                        if not series_state(self.config)['complete']:
                            self.config['teams'][winner]['wins'] += 1
                            self.config['game'] = series_state(self.config)['game']
            elif event == 'MatchDestroyed':
                m['players'], m['target'] = [], ''


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
        self.store.status = 'Manual · sin conexión al juego'
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
                                self.store.ingest(packet)
                                if packet.get('Event') == 'UpdateState':
                                    self.store.status = 'En directo · tiempo y goles sincronizados con Rocket League'
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


def preview_snapshot(store):
    """Example data for preview only; never writes to the live match or connection."""
    snapshot = store.snapshot()
    snapshot['match'] = {
        'scores': [2, 1], 'time': 193, 'overtime': False, 'target': 'PIRU', 'banner': '',
        'players': [{'Name': name, 'TeamNum': i//3, 'Boost': boost,
                     'Score': 541 if i == 0 else 125+i*32, 'Goals': 2 if i == 0 else i%2,
                     'Shots': 5, 'Assists': 1, 'Saves': 3}
                    for i, (name, boost) in enumerate([('PIRU', 72), ('CANDY', 38), ('FRESA', 100),
                                                      ('MANGO', 54), ('POP', 8), ('LIMÓN', 91)])]}
    return snapshot


def make_server(store, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            route = self.path.split('?')[0]
            if route in ('/state', '/preview-state'):
                state = preview_snapshot(store) if route == '/preview-state' else store.snapshot()
                data = json.dumps(state, ensure_ascii=False).encode('utf-8')
                mime = 'application/json; charset=utf-8'
            elif route in ('/', '/overlay'):
                data = (ROOT / 'overlay.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            elif route in ('/assets/torneo.png', '/assets/discord.png'):
                data = (ROOT / route.lstrip('/')).read_bytes()
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
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


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
        root.title('Piruleta Studio · Marcador Rocket League')
        root.geometry('1280x850')
        root.minsize(1050, 850)
        root.configure(bg='#12101a')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#201b2c', foreground='#f7effa', font=('Segoe UI', 10))
        style.configure('TEntry', fieldbackground='#30283d', foreground='white', insertcolor='white')
        style.configure('TSpinbox', fieldbackground='#30283d', foreground='white', arrowsize=14)
        style.configure('TCombobox', fieldbackground='#30283d', foreground='white')
        style.map('TCombobox', fieldbackground=[('readonly', '#30283d')], foreground=[('readonly', 'white')])
        style.configure('TButton', padding=(12, 8), background='#3e304a')
        style.configure('Control.TButton', padding=(10, 2))
        style.map('TButton', background=[('active', '#75435d')])
        style.configure('TNotebook.Tab', padding=(14, 10))
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
        style.configure('Piruleta.TCheckbutton', padding=(0, 3), background='#201b2c')
        self.vars, self.team_vars = {}, [{}, {}]
        self.last_game = self.store.config['game']
        head = tk.Frame(root, bg='#12101a')
        head.pack(fill='x', padx=24, pady=(20, 12))
        tk.Label(head, text='PIRULETA / STUDIO', fg='#fa54b7', bg='#12101a', font=('Segoe UI', 23, 'bold')).pack(side='left')
        ttk.Button(head, text='Abrir vista previa', command=lambda: webbrowser.open(self.url+'?preview=1')).pack(side='right', padx=4)
        ttk.Button(head, text='Copiar URL para OBS', command=self.copy_url).pack(side='right', padx=4)
        body = ttk.Frame(root)
        body.pack(fill='both', expand=True, padx=24)
        left = ttk.Frame(body, padding=12)
        left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(body, padding=12, width=395)
        right.pack(side='right', fill='y')
        ttk.Label(left, text='DISEÑO EN DIRECTO', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.canvas = tk.Canvas(left, bg='#141720', height=240, highlightthickness=0)
        self.canvas.pack(fill='x', pady=(10, 12))
        self.canvas.bind('<Configure>', lambda e: self.draw())
        ttk.Label(left, text='Esquema del marcador · abre la vista previa para ver el diseño completo', font=('Segoe UI', 9)).pack(anchor='w')
        nb = ttk.Notebook(left)
        nb.pack(fill='both', expand=True, pady=12)
        teams, design, visibility, layout, advanced = (ttk.Frame(nb, padding=15) for _ in range(5))
        nb.add(teams, text='Textos')
        nb.add(design, text='Diseño')
        nb.add(visibility, text='Elementos')
        nb.add(layout, text='Posiciones')
        nb.add(advanced, text='CSS libre')
        self.panel_vars = {}
        ttk.Label(layout, text='Panel                       X               Y          Escala %').pack(anchor='w')
        for key, label in [('players0', 'Jugadores A'), ('players1', 'Jugadores B'), ('focus', 'Estadísticas'), ('boost', 'Turbo'), ('brand', 'Marca'), ('banner', 'Avisos')]:
            row = ttk.Frame(layout)
            row.pack(fill='x', pady=5)
            ttk.Label(row, text=label, width=20).pack(side='left')
            values = []
            for j, value in enumerate(self.store.config['panels'][key]):
                var = tk.StringVar(value=str(value))
                ttk.Spinbox(row, from_=25 if j == 2 else 0, to=200 if j == 2 else 1920, width=7, textvariable=var).pack(side='left', padx=5)
                values.append(var)
            self.panel_vars[key] = values
        ttk.Label(advanced, text='Estilos propios para cualquier detalle del overlay (opcional).').pack(anchor='w')
        self.css = tk.Text(advanced, height=9, bg='#181426', fg='white', insertbackground='white', font=('Consolas', 10), wrap='word')
        self.css.pack(fill='both', expand=True, pady=8)
        self.css.insert('1.0', self.store.config['custom_css'])
        self.entry(teams, 'Nombre del torneo', 'event')
        self.entry(teams, 'Fase / ronda', 'round')
        self.entry(teams, 'Partido de la serie', 'game', numeric=(1, 99))
        for i in range(2):
            row = ttk.Frame(teams)
            row.pack(fill='x', pady=7)
            ttk.Label(row, text=f'Equipo {i+1}', width=20).pack(side='left')
            v = tk.StringVar(value=self.store.config['teams'][i]['name'])
            self.team_vars[i]['name'] = v
            ttk.Entry(row, textvariable=v).pack(side='left', fill='x', expand=True)
            ttk.Button(row, text='Escudo…', command=lambda i=i: self.logo(i)).pack(side='left', padx=4)
            ttk.Button(row, text='Quitar', command=lambda i=i: self.clear_logo(i)).pack(side='left')
        colorrow = ttk.Frame(design)
        colorrow.pack(fill='x', pady=5)
        for key, title in [('pink', 'Rosa / A'), ('coral', 'Coral'), ('yellow', 'Dorado / B'), ('dark', 'Fondo'), ('text', 'Texto')]:
            ttk.Button(colorrow, text=title, command=lambda k=key: self.color(k)).pack(side='left', padx=2)
        self.entry(design, 'Estilo', 'design', choices=['angular', 'rounded', 'classic'])
        self.entry(design, 'Tipografía', 'font', choices=['Arial', 'Segoe UI', 'Verdana', 'Trebuchet MS', 'Impact'])
        self.entry(design, 'Escala (%)', 'scale', numeric=(50, 150))
        self.entry(design, 'Opacidad (%)', 'opacity', numeric=(10, 100))
        self.entry(design, 'Posición horizontal', 'x', numeric=(0, 1900))
        self.entry(design, 'Posición vertical', 'y', numeric=(0, 1000))
        for k, label in [('show_logos', 'Escudos de equipos'), ('show_players', 'Jugadores y barras de turbo'), ('show_stats', 'Estadísticas del jugador en cámara'), ('show_boost', 'Turbo del jugador en cámara'), ('show_brand', 'Marca del torneo'), ('show_events', 'Avisos de gol y victoria'), ('auto_series', 'Sumar victorias automáticamente (API)')]:
            v = tk.BooleanVar(value=self.store.config[k])
            self.vars[k] = v
            ttk.Checkbutton(visibility, text='  '+label, variable=v, command=self.apply,
                            style='Piruleta.TCheckbutton').pack(anchor='w', pady=5)
        ttk.Button(left, text='Aplicar diseño', style='Control.TButton', command=self.apply).pack(anchor='e')
        ttk.Label(right, text='CONTROL DEL PARTIDO', font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 10))
        ttk.Label(right, text='Formato de la serie', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.format_var = tk.StringVar(value=f"BO{self.store.config['bestof']}")
        self.format_selector = ttk.Combobox(right, textvariable=self.format_var, state='readonly',
                                            values=[f'BO{n}' for n in SERIES_FORMATS])
        self.format_selector.pack(fill='x', pady=(6, 4))
        self.format_selector.bind('<<ComboboxSelected>>', self.change_format)
        self.series_hint = ttk.Label(right, wraplength=340, foreground='#ffce72')
        self.series_hint.pack(anchor='w', pady=(0, 10))
        self.score_labels, self.win_labels, self.manual_controls = [], [], []
        for i in range(2):
            ttk.Label(right, text=f'EQUIPO {i+1} · GOLES / SERIE').pack(anchor='w', pady=(12, 4))
            row = ttk.Frame(right)
            row.pack(fill='x')
            button = ttk.Button(row, text='−', width=3, style='Control.TButton', command=lambda i=i: self.goal(i, -1))
            button.pack(side='left')
            self.manual_controls.append(button)
            label = ttk.Label(row, text='0', font=('Segoe UI', 25, 'bold'), width=3, anchor='center')
            label.pack(side='left', padx=8)
            self.score_labels.append(label)
            button = ttk.Button(row, text='+', width=3, style='Control.TButton', command=lambda i=i: self.goal(i, 1))
            button.pack(side='left')
            self.manual_controls.append(button)
            label = ttk.Label(row, text='Serie 0', width=7, anchor='center')
            label.pack(side='left', padx=4)
            self.win_labels.append(label)
            ttk.Button(row, text='−', width=3, style='Control.TButton', command=lambda i=i: self.win(i, -1)).pack(side='left')
            ttk.Button(row, text='+', width=3, style='Control.TButton', command=lambda i=i: self.win(i, 1)).pack(side='left')
        ttk.Label(right, text='Tiempo y prórroga: sincronizados por la API.',
                  wraplength=340, foreground='#b6a4c3').pack(anchor='w', pady=(14, 8))
        ttk.Button(right, text='Reiniciar serie', style='Control.TButton', command=self.reset_series).pack(fill='x', pady=3)
        ttk.Button(right, text='Ver estadísticas y turbo', style='Control.TButton', command=self.demo).pack(fill='x', pady=3)
        ttk.Separator(right).pack(fill='x', pady=10)
        ttk.Label(right, text='DATOS DE ROCKET LEAGUE', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        row = ttk.Frame(right)
        row.pack(fill='x', pady=10)
        ttk.Label(row, text='Puerto TCP').pack(side='left')
        self.port = tk.StringVar(value='49123')
        ttk.Entry(row, textvariable=self.port, width=8).pack(side='left', padx=8)
        ttk.Button(row, text='Conectar', style='Control.TButton', command=self.connect).pack(side='left')
        ttk.Button(right, text='Desconectar / modo manual', style='Control.TButton', command=self.disconnect).pack(fill='x')
        ttk.Button(right, text='Activar API en el juego…', style='Control.TButton', command=self.configure_api).pack(fill='x', pady=3)
        ttk.Button(right, text='Cómo conectar el juego y OBS', style='Control.TButton', command=self.help).pack(fill='x', pady=4)
        ttk.Separator(right).pack(fill='x', pady=10)
        ttk.Button(right, text='Guardar perfil…', style='Control.TButton', command=self.save).pack(fill='x', pady=3)
        ttk.Button(right, text='Cargar perfil…', style='Control.TButton', command=self.load).pack(fill='x', pady=3)
        self.status = tk.Label(root, bg='#12101a', fg='#ffce72', anchor='w', padx=24, pady=13)
        self.status.pack(side='bottom', fill='x', before=body)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.connect()
        self.refresh()

    def entry(self, parent, title, key, numeric=None, choices=None):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=4)
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

    def apply(self):
        try:
            with self.store.lock:
                raw = copy.deepcopy(self.store.config)
                for k, v in self.vars.items():
                    raw[k] = v.get()
                for i in range(2):
                    raw['teams'][i]['name'] = self.team_vars[i]['name'].get()
                raw['panels'] = {k: [v.get() for v in values] for k, values in self.panel_vars.items()}
                raw['custom_css'] = self.css.get('1.0', 'end-1c')
                self.store.config = normalize_config(raw)
            self.draw()
            return True
        except (ValueError, TypeError) as exc:
            messagebox.showerror('Revisa el diseño', str(exc))
            return False

    def sync(self):
        c = self.store.config
        self.format_var.set(f"BO{c['bestof']}")
        for k, v in self.vars.items():
            v.set(c[k])
        for i in range(2):
            self.team_vars[i]['name'].set(c['teams'][i]['name'])
        for k, values in self.panel_vars.items():
            for j, v in enumerate(values):
                v.set(c['panels'][k][j])
        self.css.delete('1.0', 'end')
        self.css.insert('1.0', c['custom_css'])
        self.draw()

    def color(self, key):
        color = colorchooser.askcolor(self.store.config['colors'][key], parent=self.root)[1]
        if color:
            with self.store.lock:
                self.store.config['colors'][key] = color
            self.draw()

    def logo(self, i):
        import base64
        path = filedialog.askopenfilename(filetypes=[('Imagen PNG / JPG', '*.png *.jpg *.jpeg')])
        if path:
            data = Path(path).read_bytes()
            if len(data) > 1_400_000:
                messagebox.showerror('Imagen grande', 'Utiliza un escudo de menos de 1,4 MB.')
                return
            mime = 'image/png' if Path(path).suffix.lower() == '.png' else 'image/jpeg'
            with self.store.lock:
                self.store.config['teams'][i]['logo'] = f'data:{mime};base64,' + base64.b64encode(data).decode()

    def clear_logo(self, i):
        with self.store.lock:
            self.store.config['teams'][i]['logo'] = ''

    def goal(self, i, delta):
        if self.store.automatic:
            return
        with self.store.lock:
            self.store.match['scores'][i] = max(0, self.store.match['scores'][i]+delta)
        self.draw()

    def win(self, i, delta):
        with self.store.lock:
            state = series_state(self.store.config)
            if delta > 0 and state['complete']:
                return
            t = self.store.config['teams'][i]
            t['wins'] = max(0, min(self.store.config['bestof']//2+1, t['wins']+delta))
            self.store.config['game'] = series_state(self.store.config)['game']
            self.vars['game'].set(str(self.store.config['game']))
        self.draw()

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
            self.vars['game'].set(str(updated['game']))
        self.draw()

    def reset_series(self):
        with self.store.lock:
            for team in self.store.config['teams']:
                team['wins'] = 0
            self.store.config['game'] = 1
        self.vars['game'].set('1')
        self.draw()

    def demo(self):
        webbrowser.open(self.url+'?preview=1&details=1')

    def connect(self):
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror('Puerto', 'Introduce un puerto entre 1 y 65535.')
            return
        self.connection.connect(port)

    def disconnect(self):
        self.connection.disconnect()

    def configure_api(self):
        path = filedialog.askopenfilename(title='Con Rocket League cerrado: selecciona TAStatsAPI.ini o DefaultStatsAPI.ini',
                                          filetypes=[('Configuración de Stats API', '*StatsAPI.ini')])
        if not path:
            return
        try:
            backup, port = enable_stats_api(Path(path))
            self.port.set(str(port))
            self.connect()
            messagebox.showinfo('API activada', f'Configuración guardada.\nCopia de seguridad: {backup}\n\n'
                                'Inicia o reinicia Rocket League. La aplicación se conectará automáticamente.')
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudo activar la API', str(exc))

    def copy_url(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url)
        messagebox.showinfo('URL copiada', self.url+'\n\nOBS → Fuente de navegador → 1920 × 1080.\nMantén Piruleta Studio abierto.')

    def help(self):
        messagebox.showinfo('Juego y OBS',
            '1. Cierra Rocket League.\n2. En la carpeta del juego abre TAGame\\Config\\TAStatsAPI.ini '
            '(o DefaultStatsAPI.ini si no existe).\n3. En [TAGame.MatchStatsExporter_TA] configura:\n\n'
            'PacketSendRate=10\nPort=49123\nWebPort=49124\n\n4. Abre el juego y pulsa Conectar. '
            'Las barras de turbo requieren modo espectador.\n\n5. OBS: añade una Fuente de navegador con '
            'la URL copiada, ancho 1920 y alto 1080. El fondo es transparente.\n\n'
            'Guía completa: LÉEME.md en la carpeta de la aplicación.')

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
                with self.store.lock:
                    self.store.config = c
                self.sync()
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                messagebox.showerror('No se pudo cargar', str(exc))

    def draw(self):
        if not hasattr(self, 'canvas'):
            return
        canvas = self.canvas
        canvas.delete('all')
        w = max(600, canvas.winfo_width())
        s = self.store.snapshot()
        c, m = s['config'], s['match']
        a, b = c['colors']['pink'], c['colors']['yellow']
        canvas.create_text(w/2, 30, text=c['event'], fill='#b6a4c3', font=('Segoe UI', 10, 'bold'))
        canvas.create_rectangle(25, 57, w/2-48, 115, fill=a, outline='')
        canvas.create_rectangle(w/2+48, 57, w-25, 115, fill=b, outline='')
        canvas.create_rectangle(w/2-48, 57, w/2+48, 115, fill='white', outline='')
        for i in range(2):
            x = 40 if i == 0 else w-40
            canvas.create_text(x, 85, text=c['teams'][i]['name'][:19], fill='#181426', anchor='w' if i==0 else 'e', font=('Segoe UI', 12, 'bold'))
            canvas.create_text(w/2 + (-75 if i==0 else 75), 85, text=m['scores'][i], fill='#181426', font=('Segoe UI', 24, 'bold'))
        sec = abs(int(m['time']))
        clock = ('+' if m['overtime'] else '')+f'{sec//60}:{sec%60:02}'
        canvas.create_text(w/2, 85, text=clock, fill='#181426', font=('Segoe UI', 19, 'bold'))
        canvas.create_text(w/2, 136, text=f"{c['round']} · PARTIDO {c['game']} · BO{c['bestof']}", fill='white', font=('Segoe UI', 9))
        canvas.create_text(w/2, 220, text='PIRULETA', fill='#fa54b7', font=('Segoe UI', 27, 'bold'))
        for i in range(2):
            self.score_labels[i].configure(text=str(m['scores'][i]))
            self.win_labels[i].configure(text=f"Serie {c['teams'][i]['wins']}")
        state = series_state(c)
        hint = f"BO{c['bestof']} · {state['target']} victorias para ganar"
        if c['bestof'] % 2 == 0:
            hint += f" · hasta {c['bestof']} partidos; admite empate"
        if state['complete']:
            hint += ' · EMPATE' if state['tied'] else ' · SERIE FINALIZADA'
        self.series_hint.configure(text=hint)

    def refresh(self):
        automatic = self.store.automatic
        for control in self.manual_controls:
            control.state(['disabled'] if automatic else ['!disabled'])
        if self.store.config['game'] != self.last_game:
            self.last_game = self.store.config['game']
            self.vars['game'].set(str(self.last_game))
        self.status.configure(text='● '+self.store.status+'     |     OBS: '+self.url)
        self.draw()
        self.root.after(250, self.refresh)

    def close(self):
        if self.apply():
            self.file.write_text(json.dumps(self.store.snapshot()['config'], ensure_ascii=False, indent=2), 'utf-8')
        self.connection.disconnect()
        self.server.shutdown()
        self.root.destroy()


if __name__ == '__main__':
    App(tk.Tk()).root.mainloop()
