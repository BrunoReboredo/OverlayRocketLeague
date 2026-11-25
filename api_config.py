"""Enable the official Stats API in a user-selected INI, preserving other settings."""
from pathlib import Path
import re
import json
import os
import shutil
import time


def enable_stats_api(path):
    path = Path(path)
    if path.name.lower() not in ('tastatsapi.ini', 'defaultstatsapi.ini'):
        raise ValueError('Selecciona TAStatsAPI.ini o DefaultStatsAPI.ini de TAGame/Config.')
    data = path.read_bytes()
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig' if data.startswith(b'\xef\xbb\xbf') else 'utf-8'
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError:
        encoding = 'cp1252'
        text = data.decode(encoding)
    newline = '\r\n' if '\r\n' in text else '\n'
    section = re.compile(r'^\s*\[TAGame\.MatchStatsExporter_TA\]\s*$', re.I)
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if section.fullmatch(line)), None)
    if start is None:
        lines.extend(['', '[TAGame.MatchStatsExporter_TA]'])
        start = len(lines)-1
    end = next((i for i in range(start+1, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
    block = lines[start+1:end]
    settings = {}
    for line in block:
        match = re.match(r'^\s*(Port|WebPort)\s*=\s*(\d+)', line, re.I)
        if match:
            settings[match[1].lower()] = int(match[2])
    port = settings.get('port', 49123)
    if not 1 <= port <= 65535:
        port = 49123
    web = settings.get('webport', 49124)
    if not 0 <= web <= 65535 or web == port:
        web = 49124 if port != 49124 else 49125
    values = {'packetsendrate': ('PacketSendRate', 10), 'port': ('Port', port), 'webport': ('WebPort', web)}
    output, seen = [], set()
    for line in block:
        match = re.match(r'^\s*(PacketSendRate|Port|WebPort)\s*=', line, re.I)
        if match:
            key = match[1].lower()
            if key not in seen:
                name, value = values[key]
                output.append(f'{name}={value}')
                seen.add(key)
        else:
            output.append(line)
    for key, (name, value) in values.items():
        if key not in seen:
            output.append(f'{name}={value}')
    updated = (newline.join(lines[:start+1]+output+lines[end:])+newline).encode(encoding)
    if updated == data:
        return None, port
    backup = path.with_name(path.name+f'.piruleta-{time.time_ns()}.bak')
    shutil.copy2(path, backup)
    path.write_bytes(updated)
    return backup, port


def find_stats_ini(folder):
    """Accept the installation folder, TAGame or its Config directory."""
    folder = Path(folder)
    for directory in (folder / 'TAGame' / 'Config', folder / 'Config', folder):
        for name in ('TAStatsAPI.ini', 'DefaultStatsAPI.ini'):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def discover_stats_ini():
    """Read launcher manifests; never recursively scan the user's drives."""
    candidates = []
    manifests = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'Epic/EpicGamesLauncher/Data/Manifests'
    for manifest in manifests.glob('*.item'):
        try:
            item = json.loads(manifest.read_text('utf-8-sig'))
            if 'rocket' in (item.get('DisplayName', '') + item.get('AppName', '')).lower():
                candidates.append(Path(item['InstallLocation']))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    steam_roots = [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Steam']
    if os.name == 'nt':
        import winreg
        for hive, key, value in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                 (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    steam_roots.append(Path(winreg.QueryValueEx(handle, value)[0]))
            except OSError:
                pass
    libraries = list(steam_roots)
    for steam in steam_roots:
        try:
            vdf = (steam / 'steamapps/libraryfolders.vdf').read_text('utf-8-sig')
            libraries.extend(Path(value.replace('\\\\', '\\')) for value in re.findall(r'"path"\s*"([^"\n]+)"', vdf))
        except OSError:
            pass
    for library in libraries:
        base = library / 'steamapps'
        try:
            manifest = (base / 'appmanifest_252950.acf').read_text('utf-8-sig')
            match = re.search(r'"installdir"\s*"([^"\n]+)"', manifest)
            if match:
                candidates.append(base / 'common' / match[1])
        except OSError:
            pass
        candidates.append(base / 'common/rocketleague')
    candidates.append(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Epic Games/rocketleague')
    for candidate in candidates:
        found = find_stats_ini(candidate)
        if found:
            return found
    return None
