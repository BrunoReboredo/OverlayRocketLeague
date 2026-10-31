"""Enable the official Stats API in a user-selected INI, preserving other settings."""
from pathlib import Path
import re
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
    backup = path.with_name(path.name+f'.piruleta-{time.time_ns()}.bak')
    shutil.copy2(path, backup)
    path.write_bytes((newline.join(lines[:start+1]+output+lines[end:])+newline).encode(encoding))
    return backup, port
