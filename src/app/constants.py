import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# User Directories (XDG Standard)
USER_HOME = os.path.expanduser("~")
USER_CONFIG_DIR = os.path.join(USER_HOME, ".config", "extase-em-4r73")
USER_DATA_DIR = os.path.join(USER_HOME, ".local", "share", "extase-em-4r73")
USER_CACHE_DIR = os.path.join(USER_HOME, ".cache", "extase-em-4r73")

# Ensure directories exist
os.makedirs(USER_CONFIG_DIR, exist_ok=True)
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(USER_CACHE_DIR, exist_ok=True)

UI_FILE = os.path.join(BASE_DIR, "gui", "main.glade")
LOGO_FILE = os.path.join(ROOT_DIR, "assets", "logo.png")

# Config Paths
DEFAULT_CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")
CONFIG_PATH = os.path.join(USER_CONFIG_DIR, "config.ini")

PYTHON_EXEC = sys.executable
PLAYER_SCRIPT = os.path.join(BASE_DIR, "cli_player.py")
CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "converter.py")
IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "image_converter.py")
PIXEL_ART_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_converter.py")
PIXEL_ART_IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_image_converter.py")
GTK_CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "gtk_calibrator.py")
REALTIME_SCRIPT = os.path.join(BASE_DIR, "core", "realtime_ascii.py")
GTK_FULLSCREEN_PLAYER_SCRIPT = os.path.join(BASE_DIR, "core", "gtk_fullscreen_player.py")

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

LUMINANCE_RAMPS = {
    'standard': {
        'name': 'Padrao (70 chars)',
        'ramp': "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    },
    'simple': {
        'name': 'Simples (10 chars)',
        'ramp': "@%#*+=-:. "
    },
    'blocks': {
        'name': 'Blocos Unicode',
        'ramp': "\u2588\u2593\u2592\u2591 "
    },
    'minimal': {
        'name': 'Minimalista (5 chars)',
        'ramp': "#=:. "
    },
    'binary': {
        'name': 'Binario (Matrix)',
        'ramp': "10!|:. "
    },
    'dots': {
        'name': 'Pontos',
        'ramp': "\u2022\u25cf\u25c9\u25ce\u25c6\u00b7\u2219\u00b0. "
    },
    'letters': {
        'name': 'Letras',
        'ramp': "MWNXKOkxdolc;:,. "
    },
    'numbers': {
        'name': 'Numeros',
        'ramp': "8906532147. "
    },
    'arrows': {
        'name': 'Setas/Simbolos',
        'ramp': "\u25bc\u25b2\u25ba\u25c4\u25a0\u25a1\u25cf\u25cb\u00b7  "
    },
    'luna': {
        'name': 'Luna',
        'ramp': "\u263d\u2726\u203b\u25e6\u00b7. "
    },
    'eris': {
        'name': 'Eris',
        'ramp': "\u2665\u2666\u2736*\u00b7. "
    },
    'juno': {
        'name': 'Juno',
        'ramp': "\u263c\u25c9\u25cf\u25e6\u00b7. "
    },
    'mars': {
        'name': 'Mars',
        'ramp': "\u2660\u2593\u2592\u2591\u00b7. "
    },
    'lars': {
        'name': 'Lars',
        'ramp': "\u25c8\u25c6\u25c7\u25cb\u00b7. "
    },
    'somn': {
        'name': 'Somn',
        'ramp': "\u2601\u2237\u2591\u25e6\u00b7. "
    },
    'cyber_luna_v2': {
        'name': 'Luna',
        'ramp': "\u263d\u2726\u203b\u25e6\u00b7."
    },
    'cyber_eris_v2': {
        'name': 'Eris',
        'ramp': "\u2665\u2666\u2736*\u00b7."
    },
    'cyber_juno_v2': {
        'name': 'Juno',
        'ramp': "\u263c\u25c9\u25cf\u25e6\u00b7."
    },
    'cyber_mars_v2': {
        'name': 'Mars',
        'ramp': "\u2660\u2593\u2592\u2591\u00b7."
    },
    'cyber_lars_v2': {
        'name': 'Lars',
        'ramp': "\u25c8\u25c6\u25c7\u25cb\u00b7."
    },
    'cyber_somn_v2': {
        'name': 'Somn',
        'ramp': "\u2601\u2237\u2591\u25e6\u00b7."
    },
    'cyber_nyx_v2': {
        'name': 'Nyx',
        'ramp': "\u25b8\u25aa\u25ab\u25e6\u00b7."
    },
}

FIXED_PALETTES = {
    'gameboy': {
        'name': 'Game Boy (4 cores)',
        'colors': [(15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)]
    },
    'cga': {
        'name': 'CGA (16 cores)',
        'colors': [
            (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
            (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
            (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
            (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)
        ]
    },
    'nes': {
        'name': 'NES (54 cores)',
        'colors': [
            (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188),
            (148, 0, 132), (168, 0, 32), (168, 16, 0), (136, 20, 0),
            (80, 48, 0), (0, 120, 0), (0, 104, 0), (0, 88, 0),
            (0, 64, 88), (0, 0, 0), (188, 188, 188), (0, 120, 248),
            (0, 88, 248), (104, 68, 252), (216, 0, 204), (228, 0, 88),
            (248, 56, 0), (228, 92, 16), (172, 124, 0), (0, 184, 0),
            (0, 168, 0), (0, 168, 68), (0, 136, 136), (248, 248, 248),
            (60, 188, 252), (104, 136, 252), (152, 120, 248), (248, 120, 248),
            (248, 88, 152), (248, 120, 88), (252, 160, 68), (248, 184, 0),
            (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216),
            (120, 120, 120), (252, 252, 252), (164, 228, 252), (184, 184, 248),
            (216, 184, 248), (248, 184, 248), (248, 164, 192), (240, 208, 176),
            (252, 224, 168), (248, 216, 120), (216, 248, 120), (184, 248, 184),
            (184, 248, 216), (0, 252, 252)
        ]
    },
    'commodore64': {
        'name': 'Commodore 64 (16 cores)',
        'colors': [
            (0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238),
            (204, 68, 204), (0, 204, 85), (0, 0, 170), (238, 238, 119),
            (221, 136, 85), (102, 68, 0), (255, 119, 119), (51, 51, 51),
            (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187)
        ]
    },
    'pico8': {
        'name': 'PICO-8 (16 cores)',
        'colors': [
            (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
            (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
            (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
            (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170)
        ]
    },
    'grayscale': {
        'name': 'Escala de Cinza (8 tons)',
        'colors': [
            (0, 0, 0), (36, 36, 36), (73, 73, 73), (109, 109, 109),
            (146, 146, 146), (182, 182, 182), (219, 219, 219), (255, 255, 255)
        ]
    },
    'sepia': {
        'name': 'Sepia (8 tons)',
        'colors': [
            (44, 33, 21), (70, 52, 34), (112, 84, 55), (143, 107, 70),
            (174, 131, 86), (196, 159, 114), (218, 191, 155), (240, 223, 196)
        ]
    },
    'cyberpunk': {
        'name': 'Cyberpunk (Neon)',
        'colors': [
            (0, 0, 0), (10, 10, 30), (255, 0, 128), (0, 255, 255),
            (255, 0, 255), (128, 0, 255), (0, 128, 255), (255, 255, 0),
            (0, 255, 128), (255, 128, 0), (128, 255, 0), (255, 255, 255)
        ]
    },
    'dracula': {
        'name': 'Dracula Theme',
        'colors': [
            (40, 42, 54), (68, 71, 90), (248, 248, 242), (98, 114, 164),
            (139, 233, 253), (80, 250, 123), (255, 184, 108), (255, 121, 198),
            (189, 147, 249), (255, 85, 85), (241, 250, 140)
        ]
    },
    'monogreen': {
        'name': 'Monitor Verde (CRT)',
        'colors': [
            (0, 10, 0), (0, 30, 0), (0, 60, 0), (0, 90, 0),
            (0, 120, 0), (0, 150, 0), (0, 180, 0), (0, 210, 0),
            (0, 255, 0), (50, 255, 50), (100, 255, 100), (200, 255, 200)
        ]
    },
    'cyber_eris_v1': {
        'name': 'Eris (v1)',
        'colors': [
            (0, 0, 0), (61, 43, 77), (255, 85, 85), (255, 121, 198),
            (255, 184, 108), (248, 248, 242), (200, 60, 60), (200, 100, 180),
            (180, 50, 120), (255, 150, 150), (128, 30, 60), (255, 255, 255)
        ]
    },
    'cyber_juno_v1': {
        'name': 'Juno (v1)',
        'colors': [
            (0, 0, 0), (30, 27, 75), (234, 179, 8), (124, 58, 237),
            (248, 250, 252), (200, 150, 10), (100, 40, 200), (180, 140, 60),
            (80, 30, 180), (255, 200, 50), (160, 80, 220), (255, 255, 255)
        ]
    },
    'cyber_lars_v1': {
        'name': 'Lars (v1)',
        'colors': [
            (0, 0, 0), (40, 42, 54), (80, 250, 123), (98, 114, 164),
            (139, 233, 253), (248, 248, 242), (60, 200, 90), (80, 90, 130),
            (40, 180, 70), (120, 255, 160), (70, 100, 150), (255, 255, 255)
        ]
    },
    'cyber_luna_v1': {
        'name': 'Luna (v1)',
        'colors': [
            (0, 0, 0), (40, 42, 54), (189, 147, 249), (255, 121, 198),
            (80, 250, 123), (248, 248, 242), (150, 110, 220), (220, 100, 170),
            (120, 80, 200), (210, 170, 255), (255, 150, 210), (255, 255, 255)
        ]
    },
    'cyber_mars_v1': {
        'name': 'Mars (v1)',
        'colors': [
            (0, 0, 0), (13, 13, 13), (255, 85, 85), (68, 71, 90),
            (255, 184, 108), (248, 248, 242), (200, 60, 60), (50, 55, 70),
            (180, 40, 40), (255, 120, 120), (90, 90, 110), (255, 255, 255)
        ]
    },
    'cyber_somn_v1': {
        'name': 'Somn (v1)',
        'colors': [
            (0, 0, 0), (10, 10, 24), (139, 233, 253), (189, 147, 249),
            (248, 248, 242), (100, 200, 230), (150, 110, 220), (120, 180, 240),
            (170, 130, 240), (180, 250, 255), (210, 170, 255), (255, 255, 255)
        ]
    },
    'cyber_luna_v2': {
        'name': 'Luna',
        'colors': [
            (0, 0, 0), (64, 36, 44), (112, 64, 77), (160, 91, 110),
            (174, 116, 132), (204, 119, 150), (199, 118, 151), (249, 147, 189),
            (250, 163, 199), (184, 174, 216), (120, 200, 242), (160, 216, 246)
        ]
    },
    'cyber_eris_v2': {
        'name': 'Eris',
        'colors': [
            (0, 0, 0), (22, 8, 56), (39, 15, 97), (56, 21, 139),
            (86, 56, 156), (96, 42, 197), (108, 50, 204), (135, 62, 255),
            (153, 91, 255), (122, 123, 255), (108, 184, 255), (152, 205, 255)
        ]
    },
    'cyber_juno_v2': {
        'name': 'Juno',
        'colors': [
            (0, 0, 0), (23, 49, 43), (41, 85, 75), (58, 122, 107),
            (88, 142, 129), (66, 146, 160), (59, 135, 170), (74, 169, 212),
            (101, 182, 218), (141, 202, 228), (208, 235, 245), (222, 241, 248)
        ]
    },
    'cyber_mars_v2': {
        'name': 'Mars',
        'colors': [
            (0, 0, 0), (45, 34, 30), (78, 59, 52), (112, 84, 74),
            (133, 110, 101), (86, 76, 145), (48, 55, 173), (60, 69, 216),
            (89, 97, 222), (72, 102, 236), (85, 136, 255), (136, 172, 255)
        ]
    },
    'cyber_lars_v2': {
        'name': 'Lars',
        'colors': [
            (0, 0, 0), (26, 15, 12), (45, 26, 22), (64, 37, 31),
            (93, 70, 65), (111, 88, 38), (126, 110, 36), (158, 138, 45),
            (173, 156, 76), (125, 152, 123), (92, 165, 201), (141, 192, 217)
        ]
    },
    'cyber_somn_v2': {
        'name': 'Somn',
        'colors': [
            (0, 0, 0), (48, 40, 36), (84, 71, 63), (120, 101, 90),
            (140, 124, 115), (174, 138, 143), (183, 141, 157), (229, 176, 196),
            (233, 188, 205), (224, 192, 220), (218, 208, 245), (229, 222, 248)
        ]
    },
    'cyber_nyx_v2': {
        'name': 'Nyx',
        'colors': [
            (0, 0, 0), (25, 18, 17), (43, 32, 29), (62, 46, 42),
            (91, 77, 74), (136, 78, 90), (167, 89, 110), (209, 111, 138),
            (216, 133, 156), (150, 140, 175), (92, 169, 212), (141, 195, 225)
        ]
    },
}

STYLE_PRESETS = {
    'clean': {
        'name': 'Clean (Padrão)',
        'luminance_ramp': DEFAULT_LUMINANCE_RAMP,
        'sobel': 100,
        'sharpen_amount': 0.5,
        'aspect': 0.95
    },
    'cyberpunk': {
        'name': 'Cyberpunk (Neon)',
        'luminance_ramp': "0110010101 ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_eris_v1': {
        'name': 'Eris (v1)',
        'luminance_ramp': "\u2665\u2666\u2736*\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_juno_v1': {
        'name': 'Juno (v1)',
        'luminance_ramp': "\u263c\u25c9\u25cf\u25e6\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_lars_v1': {
        'name': 'Lars (v1)',
        'luminance_ramp': "\u25c8\u25c6\u25c7\u25cb\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_luna_v1': {
        'name': 'Luna (v1)',
        'luminance_ramp': "\u263d\u2726\u203b\u25e6\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_mars_v1': {
        'name': 'Mars (v1)',
        'luminance_ramp': "\u2660\u2593\u2592\u2591\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_somn_v1': {
        'name': 'Somn (v1)',
        'luminance_ramp': "\u2601\u2237\u2591\u25e6\u00b7. ",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_luna_v2': {
        'name': 'Luna',
        'luminance_ramp': "\u263d\u2726\u203b\u25e6\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_eris_v2': {
        'name': 'Eris',
        'luminance_ramp': "\u2665\u2666\u2736*\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_juno_v2': {
        'name': 'Juno',
        'luminance_ramp': "\u263c\u25c9\u25cf\u25e6\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_mars_v2': {
        'name': 'Mars',
        'luminance_ramp': "\u2660\u2593\u2592\u2591\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_lars_v2': {
        'name': 'Lars',
        'luminance_ramp': "\u25c8\u25c6\u25c7\u25cb\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_somn_v2': {
        'name': 'Somn',
        'luminance_ramp': "\u2601\u2237\u2591\u25e6\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'cyber_nyx_v2': {
        'name': 'Nyx',
        'luminance_ramp': "\u25b8\u25aa\u25ab\u25e6\u00b7.",
        'sobel': 50,
        'sharpen_amount': 1.0,
        'aspect': 1.0
    },
    'retro': {
        'name': 'Retro (Blocos)',
        'luminance_ramp': " ", # Blocos
        'sobel': 150, # Menos ruido
        'sharpen_amount': 0.0,
        'aspect': 0.6
    },
    'high_contrast': {
        'name': 'Alto Contraste',
        'luminance_ramp': "@#%*+=-:. ",
        'sobel': 80,
        'sharpen_amount': 0.8,
        'aspect': 0.95
    }
}

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.gif')
IMAGE_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.bmp', '.webp',
    '.tif', '.tiff', '.ppm', '.pgm', '.pbm',
    '.hdr', '.exr', '.ico'
)
