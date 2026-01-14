import os
import subprocess
import re
from typing import Dict, Optional


def detect_current_terminal() -> str:
    if os.environ.get('KITTY_WINDOW_ID'):
        return 'KITTY'
    elif os.environ.get('GNOME_TERMINAL_SERVICE'):
        return 'GNOME_TERMINAL'
    elif os.environ.get('TERM') and 'xterm' in os.environ.get('TERM', ''):
        return 'XTERM'
    elif os.environ.get('KONSOLE_VERSION'):
        return 'KONSOLE'
    elif os.environ.get('TERM_PROGRAM'):
        return os.environ.get('TERM_PROGRAM', 'UNKNOWN').upper()
    else:
        return 'UNKNOWN'


def read_kitty_font() -> Optional[Dict[str, any]]:
    config_paths = [
        os.path.expanduser('~/.config/kitty/kitty.conf'),
        os.path.expanduser('~/.config/kitty/font.conf'),
    ]

    font_family = None
    font_size = None

    for config_path in config_paths:
        if not os.path.exists(config_path):
            continue

        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue

                    if line.startswith('font_family'):
                        match = re.search(r'font_family\s+(.+)', line)
                        if match:
                            font_family = match.group(1).strip()

                    elif line.startswith('font_size'):
                        match = re.search(r'font_size\s+(\d+(?:\.\d+)?)', line)
                        if match:
                            font_size = float(match.group(1))
        except Exception:
            continue

    if font_family or font_size:
        return {
            'family': font_family or 'monospace',
            'size': int(font_size) if font_size else 12,
            'terminal': 'KITTY'
        }

    return None


def read_gnome_terminal_font() -> Optional[Dict[str, any]]:
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.Terminal.ProfilesList', 'default'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return None

        profile_id = result.stdout.strip().strip("'")

        result = subprocess.run(
            ['gsettings', 'get',
             f'org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{profile_id}/',
             'font'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return None

        font_string = result.stdout.strip().strip("'")

        match = re.search(r'(.+?)\s+(\d+(?:\.\d+)?)$', font_string)
        if match:
            return {
                'family': match.group(1).strip(),
                'size': int(float(match.group(2))),
                'terminal': 'GNOME_TERMINAL'
            }

    except Exception:
        pass

    return None


def read_xterm_font() -> Optional[Dict[str, any]]:
    xresources_path = os.path.expanduser('~/.Xresources')

    if not os.path.exists(xresources_path):
        return None

    face_name = None
    face_size = None

    try:
        with open(xresources_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('!') or not line:
                    continue

                if 'faceName' in line:
                    match = re.search(r'faceName:\s*(.+)', line)
                    if match:
                        face_name = match.group(1).strip()

                elif 'faceSize' in line:
                    match = re.search(r'faceSize:\s*(\d+)', line)
                    if match:
                        face_size = int(match.group(1))

    except Exception:
        return None

    if face_name or face_size:
        return {
            'family': face_name or 'fixed',
            'size': face_size or 10,
            'terminal': 'XTERM'
        }

    return None


def list_monospace_fonts() -> list:
    try:
        result = subprocess.run(
            ['fc-list', ':spacing=100', 'family'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return ['monospace', 'Monospace', 'Courier New', 'DejaVu Sans Mono']

        fonts = set()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split(',')
            for part in parts:
                font_name = part.strip()
                if font_name and len(font_name) < 50:
                    fonts.add(font_name)

        fonts_list = sorted(list(fonts))

        if not fonts_list:
            return ['monospace', 'Monospace', 'Courier New', 'DejaVu Sans Mono']

        return fonts_list

    except Exception:
        return ['monospace', 'Monospace', 'Courier New', 'DejaVu Sans Mono']


def detect_terminal_font() -> Dict[str, any]:
    terminal = detect_current_terminal()

    font_info = None

    if terminal == 'KITTY':
        font_info = read_kitty_font()
    elif terminal == 'GNOME_TERMINAL':
        font_info = read_gnome_terminal_font()
    elif terminal == 'XTERM':
        font_info = read_xterm_font()

    if font_info:
        return font_info

    return {
        'family': 'monospace',
        'size': 12,
        'terminal': terminal
    }
