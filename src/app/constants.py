import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

UI_FILE = os.path.join(BASE_DIR, "gui", "main.glade")
LOGO_FILE = os.path.join(ROOT_DIR, "assets", "logo.png")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")

PYTHON_EXEC = sys.executable
PLAYER_SCRIPT = os.path.join(BASE_DIR, "cli_player.py")
CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "converter.py")
IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "image_converter.py")
PIXEL_ART_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_converter.py")
PIXEL_ART_IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_image_converter.py")
CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "calibrator.py")
GTK_CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "gtk_calibrator.py")
REALTIME_SCRIPT = os.path.join(BASE_DIR, "core", "realtime_ascii.py")

QUALITY_PRESETS = {
    'mobile': {'width': 100, 'height': 25, 'aspect': 0.50, 'zoom': 1.0},
    'low': {'width': 120, 'height': 30, 'aspect': 0.50, 'zoom': 0.9},
    'medium': {'width': 180, 'height': 45, 'aspect': 0.48, 'zoom': 0.7},
    'high': {'width': 240, 'height': 60, 'aspect': 0.45, 'zoom': 0.6},
    'veryhigh': {'width': 300, 'height': 75, 'aspect': 0.42, 'zoom': 0.5},
}

BIT_PRESETS = {
    '8bit_low': {'pixel_size': 6, 'palette_size': 16},
    '8bit_high': {'pixel_size': 5, 'palette_size': 16},
    '16bit_low': {'pixel_size': 3, 'palette_size': 128},
    '16bit_high': {'pixel_size': 2, 'palette_size': 128},
    '32bit': {'pixel_size': 2, 'palette_size': 256},
    '64bit': {'pixel_size': 1, 'palette_size': 256},
}

DEFAULT_LUMINANCE_RAMP = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.gif')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
