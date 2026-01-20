#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import configparser
import argparse
import sys
import os
import time
import subprocess
import signal
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR
from src.core.pixel_art_converter import quantize_colors
from src.app.constants import LUMINANCE_RAMPS, FIXED_PALETTES
from src.utils.terminal_font_detector import detect_terminal_font

try:
    from src.core.matrix_rain_gpu import MatrixRainGPU
    MATRIX_RAIN_AVAILABLE = True
except Exception as e:
    MATRIX_RAIN_AVAILABLE = False
    print(f"Matrix Rain nao disponivel: {e}")

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except Exception as e:
    POSTFX_AVAILABLE = False
    print(f"PostFX nao disponivel: {e}")

try:
    from src.core.style_transfer import StyleTransferProcessor, StyleConfig, STYLE_PRESETS
    STYLE_TRANSFER_AVAILABLE = True
except Exception as e:
    STYLE_TRANSFER_AVAILABLE = False
    STYLE_PRESETS = {}
    print(f"Style Transfer nao disponivel: {e}")

try:
    from src.core.optical_flow import OpticalFlowInterpolator, OpticalFlowConfig
    OPTICAL_FLOW_AVAILABLE = True
except Exception as e:
    OPTICAL_FLOW_AVAILABLE = False
    print(f"Optical Flow nao disponivel: {e}")

try:
    from src.core.audio_analyzer import AudioAnalyzer, AudioConfig, AudioReactiveModulator
    AUDIO_AVAILABLE = True
except Exception as e:
    AUDIO_AVAILABLE = False
    print(f"Audio Reactive nao disponivel: {e}")

try:
    from src.core.auto_segmenter import AutoSegmenter, is_available as auto_seg_available
    AUTO_SEG_AVAILABLE = auto_seg_available()
except Exception as e:
    AUTO_SEG_AVAILABLE = False
    print(f"Auto Segmentation nao disponivel: {e}")


CHROMA_PRESETS = {
    'studio': {'h_min': 35, 'h_max': 85, 's_min': 50, 's_max': 255, 'v_min': 50, 'v_max': 255, 'erode': 2, 'dilate': 2},
    'natural': {'h_min': 35, 'h_max': 90, 's_min': 30, 's_max': 255, 'v_min': 30, 'v_max': 255, 'erode': 2, 'dilate': 2},
    'bright': {'h_min': 40, 'h_max': 80, 's_min': 80, 's_max': 255, 'v_min': 80, 'v_max': 255, 'erode': 2, 'dilate': 2},
}

DEFAULT_VALUES = {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255, 'erode': 2, 'dilate': 2}

QUALITY_PRESETS = {
    'mobile': {'width': 100, 'height': 25},
    'low': {'width': 120, 'height': 30},
    'medium': {'width': 180, 'height': 45},
    'high': {'width': 240, 'height': 60},
    'veryhigh': {'width': 300, 'height': 75},
}

RENDER_MODE_USER = 0
RENDER_MODE_BACKGROUND = 1
RENDER_MODE_BOTH = 2

MODE_ASCII = 'ascii'
MODE_PIXELART = 'pixelart'


class GTKCalibrator:

    def __init__(self, config_path: str, video_path: str = None):
        self.config_path = config_path
        self.video_path = video_path
        self.config = None
        self.cap = None
        self.is_video_file = video_path is not None

        self.is_recording_mp4 = False
        self.is_recording_ascii = False
        self.mp4_process = None
        self.mp4_audio_process = None
        self.mp4_output_file = None
        self.mp4_temp_dir = None
        self.mp4_frame_count = 0
        self.mp4_start_time = None
        self.ascii_frames = []
        self.recording_fps = 30

        self.current_frame = None
        self.current_mask = None
        self.source_aspect_ratio = 4/3
        self.converter_config = None
        self.pixel_art_config = None
        self.target_dimensions = (80, 25)
        self.render_mode = RENDER_MODE_USER
        self.conversion_mode = MODE_ASCII
        self._block_signals = False
        self._frame_counter = 0
        self._cached_ascii_data = None
        self._last_click_time = 0.0
        self._last_render_time = 0.0
        self._render_fps = 0.0

        self.braille_enabled = False
        self.braille_threshold = 128
        self.temporal_enabled = False
        self.temporal_threshold = 10
        self._prev_char_grid = None

        self.matrix_enabled = False
        self.matrix_mode = 'user'
        self.matrix_charset = 'katakana'
        self.matrix_particles = 5000
        self.matrix_speed = 1.0
        self.matrix_rain_instance = None
        self._prev_gray = None

        self.auto_seg_enabled = False
        self.auto_segmenter = None

        self.edge_boost_enabled = False
        self.edge_boost_amount = 100
        self.use_edge_chars = True

        self.postfx_enabled = False
        self.postfx_processor = None
        self.postfx_config = None

        self.style_enabled = False
        self.style_preset = 'none'
        self.style_processor = None

        self.optical_flow_enabled = False
        self.optical_flow_interpolator = None

        self.audio_enabled = False
        self.audio_analyzer = None
        self.audio_modulator = None
        self.audio_modulate_bloom = True
        self.audio_modulate_glitch = True
        self.audio_modulate_chromatic = True

        self.terminal_font = None
        self.config_last_load = 0

        self._load_config()
        self._init_capture()
        self._load_css()
        self._init_ui()
        self._load_initial_values()

    def _load_css(self):
        css = b'''
        .island {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 6px 10px;
            margin: 2px;
            background-color: rgba(45, 30, 55, 0.4);
        }
        .island-presets {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 4px 8px;
            margin: 2px;
        }
        .island-actions {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 4px 8px;
            margin: 2px;
        }
        .island-recording {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 4px 8px;
            margin: 2px;
        }
        .island-config {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 4px 8px;
            margin: 2px;
        }
        .island-fx {
            border: 2px solid #7a5a3d;
            border-radius: 15px;
            padding: 4px 8px;
            margin: 2px;
            background-color: rgba(55, 40, 30, 0.3);
        }
        .island-hsv {
            border: 2px solid #5a3d7a;
            border-radius: 15px;
            padding: 8px;
            margin: 4px;
        }
        .video-frame {
            border: 2px solid #5a3d7a;
            border-radius: 10px;
            padding: 4px;
            background-color: rgba(30, 20, 40, 0.6);
        }
        .recording-active {
            border: 3px solid #ff0000;
            background-color: rgba(255, 0, 0, 0.1);
        }
        '''
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _load_config(self):
        if not os.path.exists(self.config_path):
            print(f"Erro: config.ini nao encontrado: {self.config_path}", file=sys.stderr)
            sys.exit(1)

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(self.config_path, encoding='utf-8')
        self.config_last_load = os.path.getmtime(self.config_path)

        self._reload_converter_config()
        self._reload_pixel_art_config()

        self.conversion_mode = self.config.get('Mode', 'conversion_mode', fallback=MODE_ASCII)

        self._detect_terminal_font()

    def _reload_converter_config(self):
        try:
            self.converter_config = {
                'target_width': self.config.getint('Conversor', 'target_width', fallback=80),
                'target_height': self.config.getint('Conversor', 'target_height', fallback=22),
                'char_aspect_ratio': self.config.getfloat('Conversor', 'char_aspect_ratio', fallback=1.0),
                'sobel_threshold': self.config.getint('Conversor', 'sobel_threshold', fallback=20),
                'luminance_ramp': self.config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|'),
                'sharpen_enabled': self.config.getboolean('Conversor', 'sharpen_enabled', fallback=True),
                'sharpen_amount': self.config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
            }
        except Exception as e:
            print(f"Aviso: Erro ao carregar config: {e}")
            self.converter_config = {
                'target_width': 80, 'target_height': 22, 'char_aspect_ratio': 1.0,
                'sobel_threshold': 20, 'luminance_ramp': LUMINANCE_RAMP_DEFAULT,
                'sharpen_enabled': True, 'sharpen_amount': 0.5
            }

    def _reload_pixel_art_config(self):
        try:
            self.pixel_art_config = {
                'pixel_size': self.config.getint('PixelArt', 'pixel_size', fallback=2),
                'color_palette_size': self.config.getint('PixelArt', 'color_palette_size', fallback=256),
                'use_fixed_palette': self.config.getboolean('PixelArt', 'use_fixed_palette', fallback=False),
            }
        except Exception:
            self.pixel_art_config = {'pixel_size': 2, 'color_palette_size': 256, 'use_fixed_palette': False}

    def _detect_terminal_font(self):
        detection_enabled = True
        font_family_override = None
        font_size_override = None

        if self.config.has_section('Preview'):
            detection_enabled = self.config.getboolean('Preview', 'font_detection_enabled', fallback=True)
            font_family_config = self.config.get('Preview', 'font_family', fallback='auto')
            font_size_config = self.config.get('Preview', 'font_size', fallback='auto')

            if font_family_config != 'auto':
                font_family_override = font_family_config

            if font_size_config != 'auto':
                try:
                    font_size_override = int(font_size_config)
                except ValueError:
                    pass

        if detection_enabled and not (font_family_override and font_size_override):
            detected = detect_terminal_font()
            self.terminal_font = {
                'family': font_family_override or detected.get('family', 'monospace'),
                'size': font_size_override or detected.get('size', 12),
                'terminal': detected.get('terminal', 'UNKNOWN')
            }
        elif font_family_override or font_size_override:
            self.terminal_font = {
                'family': font_family_override or 'monospace',
                'size': font_size_override or 12,
                'terminal': 'OVERRIDE'
            }
        else:
            self.terminal_font = {
                'family': 'monospace',
                'size': 12,
                'terminal': 'FALLBACK'
            }

    def _init_capture(self):
        capture_source = self.video_path if self.is_video_file else 0

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            if self.is_video_file:
                self.cap = cv2.VideoCapture(capture_source)
            else:
                self.cap = cv2.VideoCapture(capture_source, cv2.CAP_V4L2)

            if self.cap.isOpened():
                break

            if attempt < max_retries - 1:
                print(f"Tentativa {attempt + 1}/{max_retries}: Aguardando device liberar... ({retry_delay}s)")
                time.sleep(retry_delay)
            else:
                error_msg = f"Nao foi possivel abrir fonte de video: {capture_source}\n\n"
                if not self.is_video_file:
                    error_msg += "A webcam pode estar em uso por outro processo ou ainda nao foi liberada pelo kernel.\n\n"
                    error_msg += "Aguarde 2-3 segundos e tente novamente."

                print(f"[ERRO] {error_msg}")

                def show_error_dialog():
                    dialog = Gtk.MessageDialog(
                        parent=None,
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Erro ao Abrir Fonte de Video"
                    )
                    dialog.format_secondary_text(error_msg)
                    dialog.run()
                    dialog.destroy()
                    Gtk.main_quit()

                GLib.timeout_add(100, show_error_dialog)
                return

        if self.cap and self.cap.isOpened():
            self.recording_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

            w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            if h > 0:
                self.source_aspect_ratio = w / h

        self._update_target_dimensions()

    def _update_target_dimensions(self):
        try:
            w = self.converter_config['target_width']
            h = self.converter_config['target_height']

            w = max(40, min(200, int(w)))

            if h == 0:
                if self.cap:
                    source_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    source_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    char_aspect_ratio = self.converter_config.get('char_aspect_ratio', 1.0)

                    if source_w > 0 and source_h > 0:
                        h = int((w * source_h * char_aspect_ratio) / source_w)
                        h = max(20, min(150, h))
                    else:
                        h = 20
                else:
                    h = 20
            else:
                h = max(20, min(150, int(h)))

            self.target_dimensions = (w, h)
        except Exception as e:
            print(f"[ERRO _update_target_dimensions] {e}")
            import traceback
            traceback.print_exc()
            self.target_dimensions = (85, 48)

    def _init_ui(self):
        glade_path = os.path.join(BASE_DIR, "src", "gui", "calibrator.glade")

        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_path)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("calibrator_window")
        self.window.connect("key-press-event", self.on_key_press)

        logo_path = os.path.join(BASE_DIR, "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 64, 64, True)
                self.window.set_icon(pixbuf)
            except Exception as e:
                print(f"Aviso: Erro ao carregar icone: {e}")

        self.image_original = self.builder.get_object("image_original")
        self.image_chroma = self.builder.get_object("image_chroma")
        self.image_ascii = self.builder.get_object("image_ascii")

        self.aspect_original = self.builder.get_object("aspect_original")
        self.aspect_chroma = self.builder.get_object("aspect_chroma")
        self.aspect_ascii = self.builder.get_object("aspect_ascii")

        self.scale_h_min = self.builder.get_object("scale_h_min")
        self.scale_h_max = self.builder.get_object("scale_h_max")
        self.scale_s_min = self.builder.get_object("scale_s_min")
        self.scale_s_max = self.builder.get_object("scale_s_max")
        self.scale_v_min = self.builder.get_object("scale_v_min")
        self.scale_v_max = self.builder.get_object("scale_v_max")
        self.scale_erode = self.builder.get_object("scale_erode")
        self.scale_dilate = self.builder.get_object("scale_dilate")

        self.spin_width = self.builder.get_object("spin_width")
        self.spin_height = self.builder.get_object("spin_height")
        self.scale_sobel = self.builder.get_object("scale_sobel")
        self.scale_sharpen = self.builder.get_object("scale_sharpen")
        self.chk_sharpen = self.builder.get_object("chk_sharpen")
        self.combo_render_mode = self.builder.get_object("combo_render_mode")

        self.spin_pixel_size = self.builder.get_object("spin_pixel_size")
        self.spin_palette_size = self.builder.get_object("spin_palette_size")
        self.chk_fixed_palette = self.builder.get_object("chk_fixed_palette")
        self.combo_ramp_preset = self.builder.get_object("combo_ramp_preset")
        self.combo_fixed_palette = self.builder.get_object("combo_fixed_palette")

        self.radio_ascii = self.builder.get_object("radio_ascii")
        self.radio_pixelart = self.builder.get_object("radio_pixelart")
        self.box_ascii_options = self.builder.get_object("box_ascii_options")
        self.box_pixelart_options = self.builder.get_object("box_pixelart_options")
        self.frame_ascii_options = self.builder.get_object("frame_ascii_options")
        self.frame_pixelart_options = self.builder.get_object("frame_pixelart_options")

        self.btn_record_mp4 = self.builder.get_object("btn_record_mp4")
        self.btn_record_ascii = self.builder.get_object("btn_record_ascii")
        self.lbl_status = self.builder.get_object("lbl_status")

        self.combo_resolution = self.builder.get_object("combo_resolution")
        self.combo_luminance = self.builder.get_object("combo_luminance")

        self.chk_braille = self.builder.get_object("chk_braille")
        self.scale_braille_threshold = self.builder.get_object("scale_braille_threshold")
        self.chk_temporal = self.builder.get_object("chk_temporal")
        self.scale_temporal_threshold = self.builder.get_object("scale_temporal_threshold")
        self.chk_auto_seg = self.builder.get_object("chk_auto_seg")

        self.chk_edge_boost = self.builder.get_object("chk_edge_boost")
        self.scale_edge_boost_amount = self.builder.get_object("scale_edge_boost_amount")
        self.chk_use_edge_chars = self.builder.get_object("chk_use_edge_chars")

        self.chk_matrix = self.builder.get_object("chk_matrix")
        self.combo_matrix_mode = self.builder.get_object("combo_matrix_mode")
        self.combo_matrix_charset = self.builder.get_object("combo_matrix_charset")
        self.spin_matrix_particles = self.builder.get_object("spin_matrix_particles")
        self.scale_matrix_speed = self.builder.get_object("scale_matrix_speed")

        self.chk_bloom = self.builder.get_object("chk_bloom")
        self.chk_chromatic = self.builder.get_object("chk_chromatic")
        self.chk_scanlines = self.builder.get_object("chk_scanlines")
        self.chk_glitch = self.builder.get_object("chk_glitch")
        self._init_postfx()

        self.chk_style = self.builder.get_object("chk_style")
        self.combo_style_preset = self.builder.get_object("combo_style_preset")
        self._init_style()

        self.chk_optical_flow = self.builder.get_object("chk_optical_flow")
        self.combo_optical_flow_fps = self.builder.get_object("combo_optical_flow_fps")
        self.combo_optical_flow_quality = self.builder.get_object("combo_optical_flow_quality")
        self._init_optical_flow()

        self.chk_audio = self.builder.get_object("chk_audio")
        self.scale_audio_bass = self.builder.get_object("scale_audio_bass")
        self.scale_audio_mids = self.builder.get_object("scale_audio_mids")
        self.scale_audio_treble = self.builder.get_object("scale_audio_treble")
        self.chk_audio_bloom = self.builder.get_object("chk_audio_bloom")
        self.chk_audio_glitch = self.builder.get_object("chk_audio_glitch")
        self.chk_audio_chrom = self.builder.get_object("chk_audio_chrom")
        self._init_audio()

        self.event_ascii = self.builder.get_object("event_ascii")
        if self.event_ascii:
            self.event_ascii.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.event_ascii.connect("button-press-event", self._on_ascii_button_press)

        self.btn_save_config = self.builder.get_object("btn_save_config")
        if self.btn_save_config:
            self.btn_save_config.connect("clicked", self.on_save_config_clicked)

    def _on_ascii_button_press(self, widget, event):
        if event.button == 1:
            current_time = time.time()
            if current_time - self._last_click_time < 0.4:
                self._save_and_open_preview()
                self._last_click_time = 0.0
                return True
            self._last_click_time = current_time
        return False

    def _check_config_reload(self):
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.config_last_load:
                self.config.read(self.config_path, encoding='utf-8')
                self.config_last_load = current_mtime
                self._reload_converter_config()
                self._reload_pixel_art_config()
                self._load_initial_values()
        except Exception as e:
            print(f"Erro ao recarregar config: {e}", file=sys.stderr)

    def _load_initial_values(self):
        self._block_signals = True

        values = DEFAULT_VALUES.copy()
        if 'ChromaKey' in self.config:
            try:
                values['h_min'] = self.config.getint('ChromaKey', 'h_min', fallback=values['h_min'])
                values['h_max'] = self.config.getint('ChromaKey', 'h_max', fallback=values['h_max'])
                values['s_min'] = self.config.getint('ChromaKey', 's_min', fallback=values['s_min'])
                values['s_max'] = self.config.getint('ChromaKey', 's_max', fallback=values['s_max'])
                values['v_min'] = self.config.getint('ChromaKey', 'v_min', fallback=values['v_min'])
                values['v_max'] = self.config.getint('ChromaKey', 'v_max', fallback=values['v_max'])
                values['erode'] = self.config.getint('ChromaKey', 'erode', fallback=values['erode'])
                values['dilate'] = self.config.getint('ChromaKey', 'dilate', fallback=values['dilate'])
            except Exception:
                pass

        self.scale_h_min.set_value(values['h_min'])
        self.scale_h_max.set_value(values['h_max'])
        self.scale_s_min.set_value(values['s_min'])
        self.scale_s_max.set_value(values['s_max'])
        self.scale_v_min.set_value(values['v_min'])
        self.scale_v_max.set_value(values['v_max'])
        self.scale_erode.set_value(values['erode'])
        self.scale_dilate.set_value(values['dilate'])

        self.spin_width.set_value(self.converter_config['target_width'])
        self.spin_height.set_value(self.converter_config['target_height'])
        self.scale_sobel.set_value(self.converter_config['sobel_threshold'])
        self.scale_sharpen.set_value(self.converter_config['sharpen_amount'])
        self.chk_sharpen.set_active(self.converter_config['sharpen_enabled'])

        if self.spin_pixel_size:
            self.spin_pixel_size.set_value(self.pixel_art_config['pixel_size'])
        if self.spin_palette_size:
            self.spin_palette_size.set_value(self.pixel_art_config['color_palette_size'])
        if self.chk_fixed_palette:
            use_fixed = self.pixel_art_config.get('use_fixed_palette', False)
            self.chk_fixed_palette.set_active(use_fixed)
            if self.combo_fixed_palette:
                self.combo_fixed_palette.set_sensitive(use_fixed)

        if self.combo_render_mode:
            saved_render_mode = self.config.get('Conversor', 'render_mode', fallback='user')
            render_mode_map = {'user': RENDER_MODE_USER, 'background': RENDER_MODE_BACKGROUND, 'both': RENDER_MODE_BOTH}
            self.render_mode = render_mode_map.get(saved_render_mode, RENDER_MODE_USER)
            self.combo_render_mode.set_active(self.render_mode)

        if self.radio_ascii and self.radio_pixelart:
            if self.conversion_mode == MODE_PIXELART:
                self.radio_pixelart.set_active(True)
            else:
                self.radio_ascii.set_active(True)
            self._update_mode_visibility()

        if 'Conversor' in self.config:
            self.braille_enabled = self.config.getboolean('Conversor', 'braille_enabled', fallback=False)
            self.braille_threshold = self.config.getint('Conversor', 'braille_threshold', fallback=128)
            self.temporal_enabled = self.config.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
            self.temporal_threshold = self.config.getint('Conversor', 'temporal_threshold', fallback=10)
            self.auto_seg_enabled = self.config.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
            self.edge_boost_enabled = self.config.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
            self.edge_boost_amount = self.config.getint('Conversor', 'edge_boost_amount', fallback=100)
            self.use_edge_chars = self.config.getboolean('Conversor', 'use_edge_chars', fallback=True)

        if self.chk_braille:
            self.chk_braille.set_active(self.braille_enabled)
        if self.scale_braille_threshold:
            self.scale_braille_threshold.set_value(self.braille_threshold)
            self.scale_braille_threshold.set_sensitive(self.braille_enabled)
        if self.chk_temporal:
            self.chk_temporal.set_active(self.temporal_enabled)
        if self.scale_temporal_threshold:
            self.scale_temporal_threshold.set_value(self.temporal_threshold)
            self.scale_temporal_threshold.set_sensitive(self.temporal_enabled)

        if self.chk_auto_seg:
            self.chk_auto_seg.set_active(self.auto_seg_enabled)
            if self.auto_seg_enabled and AUTO_SEG_AVAILABLE:
                try:
                    self.auto_segmenter = AutoSegmenter(threshold=0.5, use_gpu=True)
                except Exception:
                    self.auto_seg_enabled = False
                    self.chk_auto_seg.set_active(False)

        if self.chk_edge_boost:
            self.chk_edge_boost.set_active(self.edge_boost_enabled)
        if self.scale_edge_boost_amount:
            self.scale_edge_boost_amount.set_value(self.edge_boost_amount)
            self.scale_edge_boost_amount.set_sensitive(self.edge_boost_enabled)
        if self.chk_use_edge_chars:
            self.chk_use_edge_chars.set_active(self.use_edge_chars)

        if 'MatrixRain' in self.config:
            self.matrix_enabled = self.config.getboolean('MatrixRain', 'enabled', fallback=False)
            self.matrix_mode = self.config.get('MatrixRain', 'mode', fallback='user')
            self.matrix_charset = self.config.get('MatrixRain', 'char_set', fallback='katakana')
            self.matrix_particles = self.config.getint('MatrixRain', 'num_particles', fallback=5000)
            self.matrix_speed = self.config.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)

        if self.chk_matrix:
            self.chk_matrix.set_active(self.matrix_enabled)
        if self.combo_matrix_mode:
            self.combo_matrix_mode.set_active_id(self.matrix_mode)
        if self.combo_matrix_charset:
            self.combo_matrix_charset.set_active_id(self.matrix_charset)
        if self.spin_matrix_particles:
            self.spin_matrix_particles.set_value(self.matrix_particles)
        if self.scale_matrix_speed:
            self.scale_matrix_speed.set_value(self.matrix_speed)

        if self.matrix_enabled:
            self._reinit_matrix_rain()

        self._block_signals = False

    def _update_mode_visibility(self):
        if self.box_ascii_options and self.box_pixelart_options:
            if self.conversion_mode == MODE_ASCII:
                self.box_ascii_options.set_visible(True)
                self.box_pixelart_options.set_visible(False)
            else:
                self.box_ascii_options.set_visible(False)
                self.box_pixelart_options.set_visible(True)

    def _set_frame_to_image(self, image_widget, aspect_frame, frame):
        if frame is None or frame.size == 0:
            return

        try:
            h, w = frame.shape[:2]
            aspect_ratio = w / h

            aspect_frame.set_property("ratio", aspect_ratio)

            if len(frame.shape) == 2:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            alloc = aspect_frame.get_allocation()
            target_w = max(alloc.width - 4, 10)
            target_h = max(alloc.height - 4, 10)

            scale_w = target_w / w
            scale_h = target_h / h
            scale = min(scale_w, scale_h)
            new_w = max(10, int(w * scale))
            new_h = max(10, int(h * scale))

            resized = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            resized = np.ascontiguousarray(resized)

            rowstride = new_w * 3

            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                resized.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                new_w,
                new_h,
                rowstride,
                None,
                None
            )

            image_widget.set_from_pixbuf(pixbuf.copy())
            image_widget.queue_draw()
        except Exception as e:
            print(f"Erro ao definir frame: {e}")

    def _get_current_hsv_values(self) -> dict:
        return {
            'h_min': int(self.scale_h_min.get_value()),
            'h_max': int(self.scale_h_max.get_value()),
            's_min': int(self.scale_s_min.get_value()),
            's_max': int(self.scale_s_max.get_value()),
            'v_min': int(self.scale_v_min.get_value()),
            'v_max': int(self.scale_v_max.get_value()),
            'erode': int(self.scale_erode.get_value()),
            'dilate': int(self.scale_dilate.get_value()),
        }

    def _set_hsv_values(self, values: dict):
        self._block_signals = True
        self.scale_h_min.set_value(values.get('h_min', 35))
        self.scale_h_max.set_value(values.get('h_max', 85))
        self.scale_s_min.set_value(values.get('s_min', 40))
        self.scale_s_max.set_value(values.get('s_max', 255))
        self.scale_v_min.set_value(values.get('v_min', 40))
        self.scale_v_max.set_value(values.get('v_max', 255))
        self.scale_erode.set_value(values.get('erode', 2))
        self.scale_dilate.set_value(values.get('dilate', 2))
        self._block_signals = False

    def _auto_detect_green(self, frame) -> dict:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_broad = np.array([30, 40, 40])
        upper_broad = np.array([90, 255, 255])
        mask_broad = cv2.inRange(hsv, lower_broad, upper_broad)

        green_pixels = hsv[mask_broad > 0]

        if len(green_pixels) == 0:
            self._set_status("Nenhum verde detectado")
            return CHROMA_PRESETS['studio'].copy()

        h_mean = np.mean(green_pixels[:, 0])
        s_mean = np.mean(green_pixels[:, 1])
        v_mean = np.mean(green_pixels[:, 2])
        h_std = np.std(green_pixels[:, 0])
        s_std = np.std(green_pixels[:, 1])
        v_std = np.std(green_pixels[:, 2])

        result = {
            'h_min': max(0, int(h_mean - 1.5 * h_std)),
            'h_max': min(179, int(h_mean + 1.5 * h_std)),
            's_min': max(0, int(s_mean - 1.5 * s_std)),
            's_max': 255,
            'v_min': max(0, int(v_mean - 1.5 * v_std)),
            'v_max': 255,
            'erode': 2,
            'dilate': 2
        }

        self._set_status(f"Auto: H={result['h_min']}-{result['h_max']}")
        return result

    def _create_chroma_visualization(self, frame, mask):
        result = np.zeros_like(frame)
        mask_inv = cv2.bitwise_not(mask)
        result[mask_inv > 0] = frame[mask_inv > 0]
        return result

    def _convert_to_braille(self, gray_image: np.ndarray, threshold: int) -> np.ndarray:
        h, w = gray_image.shape
        grid_h = h // 4
        grid_w = w // 2

        braille_grid = np.zeros((grid_h, grid_w), dtype=np.int32)

        for cy in range(grid_h):
            for cx in range(grid_w):
                base_x = cx * 2
                base_y = cy * 4

                if base_x + 1 >= w or base_y + 3 >= h:
                    braille_grid[cy, cx] = 0x2800
                    continue

                code = 0x2800

                if gray_image[base_y + 0, base_x + 0] > threshold: code |= 0x01
                if gray_image[base_y + 1, base_x + 0] > threshold: code |= 0x02
                if gray_image[base_y + 2, base_x + 0] > threshold: code |= 0x04
                if gray_image[base_y + 0, base_x + 1] > threshold: code |= 0x08
                if gray_image[base_y + 1, base_x + 1] > threshold: code |= 0x10
                if gray_image[base_y + 2, base_x + 1] > threshold: code |= 0x20
                if gray_image[base_y + 3, base_x + 0] > threshold: code |= 0x40
                if gray_image[base_y + 3, base_x + 1] > threshold: code |= 0x80

                braille_grid[cy, cx] = code

        return braille_grid

    def _apply_temporal_coherence(self, char_grid: np.ndarray, gray: np.ndarray, threshold: int) -> np.ndarray:
        grid_h, grid_w = char_grid.shape

        if gray.shape[0] != grid_h or gray.shape[1] != grid_w:
            gray = cv2.resize(gray, (grid_w, grid_h), interpolation=cv2.INTER_NEAREST)

        if self._prev_char_grid is None or self._prev_gray is None:
            self._prev_char_grid = char_grid.copy()
            self._prev_gray = gray.copy()
            return char_grid

        if self._prev_char_grid.shape != char_grid.shape:
            self._prev_char_grid = char_grid.copy()
            self._prev_gray = gray.copy()
            return char_grid

        diff = np.abs(gray.astype(np.int16) - self._prev_gray.astype(np.int16))
        stable_mask = diff < threshold
        result = np.where(stable_mask, self._prev_char_grid, char_grid)

        self._prev_char_grid = result.copy()
        self._prev_gray = gray.copy()

        return result

    def _render_braille_to_image(self, braille_grid: np.ndarray, resized_color: np.ndarray, resized_mask: np.ndarray, frame_h: int, frame_w: int) -> np.ndarray:
        grid_h, grid_w = braille_grid.shape

        char_w_base = 12
        char_h_base = 20

        scale_x = frame_w / (grid_w * char_w_base)
        scale_y = frame_h / (grid_h * char_h_base)
        scale = min(scale_x, scale_y)

        char_w = max(6, int(char_w_base * scale))
        char_h = max(10, int(char_h_base * scale))

        total_w = grid_w * char_w
        total_h = grid_h * char_h

        offset_x = (frame_w - total_w) // 2
        offset_y = (frame_h - total_h) // 2

        pil_image = Image.new('RGB', (frame_w, frame_h), (0, 0, 0))
        draw = ImageDraw.Draw(pil_image)

        font_size = max(8, int(char_h * 0.9))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", font_size)
            except:
                font = ImageFont.load_default()

        color_h, color_w = resized_color.shape[:2]
        mask_h, mask_w = resized_mask.shape[:2]

        for y in range(grid_h):
            for x in range(grid_w):
                color_y = min(int(y * color_h / grid_h), color_h - 1)
                color_x = min(int(x * color_w / grid_w), color_w - 1)

                mask_y = min(int(y * mask_h / grid_h), mask_h - 1)
                mask_x = min(int(x * mask_w / grid_w), mask_w - 1)

                is_chroma = resized_mask[mask_y, mask_x] > 127

                if self.render_mode == RENDER_MODE_USER and is_chroma:
                    continue
                elif self.render_mode == RENDER_MODE_BACKGROUND and not is_chroma:
                    continue

                braille_code = braille_grid[y, x]
                char = chr(braille_code)

                b, g, r = resized_color[color_y, color_x]
                px = offset_x + x * char_w
                py = offset_y + y * char_h

                draw.text((px, py), char, font=font, fill=(int(r), int(g), int(b)))

        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _render_ascii_to_image(self, resized_gray, resized_color, resized_mask, magnitude_norm, angle, frame_h, frame_w) -> np.ndarray:
        try:
            height, width = resized_gray.shape

            if height <= 0 or width <= 0 or frame_h <= 0 or frame_w <= 0:
                print(f"[ERRO RENDER] Dimensoes invalidas: gray={width}x{height}, canvas={frame_w}x{frame_h}")
                return np.zeros((max(1, frame_h), max(1, frame_w), 3), dtype=np.uint8)

            ascii_image = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        except Exception as e:
            print(f"[ERRO RENDER INIT] {e}")
            import traceback
            traceback.print_exc()
            return np.zeros((480, 640, 3), dtype=np.uint8)

        char_w_base = 8
        char_h_base = 16

        scale_x = frame_w / (width * char_w_base)
        scale_y = frame_h / (height * char_h_base)
        scale = min(scale_x, scale_y)

        char_w = max(1, int(char_w_base * scale))
        char_h = max(1, int(char_h_base * scale))

        total_w = width * char_w
        total_h = height * char_h

        offset_x = (frame_w - total_w) // 2
        offset_y = (frame_h - total_h) // 2

        font_scale = max(0.25, 0.35 * scale)

        luminance_ramp = self.converter_config['luminance_ramp']
        ramp_len = len(luminance_ramp)
        sobel_threshold = self.converter_config['sobel_threshold']

        is_edge = magnitude_norm > sobel_threshold

        if self.edge_boost_enabled:
            brightness = resized_gray.astype(np.int32)
            edge_boost = is_edge.astype(np.int32) * self.edge_boost_amount
            brightness = np.clip(brightness + edge_boost, 0, 255)
            lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
        else:
            lum_indices = (resized_gray * (ramp_len - 1) / 255).astype(np.int32)

        for y in range(height):
            py = offset_y + y * char_h + char_h - 3

            for x in range(width):
                is_chroma = resized_mask[y, x] > 127

                if self.render_mode == RENDER_MODE_USER:
                    if is_chroma:
                        continue
                elif self.render_mode == RENDER_MODE_BACKGROUND:
                    if not is_chroma:
                        continue

                mag = magnitude_norm[y, x]
                ang = angle[y, x]

                if self.use_edge_chars and mag > sobel_threshold:
                    if 22.5 <= ang < 67.5 or 157.5 <= ang < 202.5:
                        char = '/'
                    elif 67.5 <= ang < 112.5 or 247.5 <= ang < 292.5:
                        char = '|'
                    elif 112.5 <= ang < 157.5 or 292.5 <= ang < 337.5:
                        char = '\\'
                    else:
                        char = '-'
                else:
                    char = luminance_ramp[lum_indices[y, x]]

                b, g, r = resized_color[y, x]
                px = offset_x + x * char_w
                rect_y = offset_y + y * char_h

                if char.strip():
                    cv2.putText(ascii_image, char, (px, py), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (int(b), int(g), int(r)), 1)
                else:
                    cv2.rectangle(ascii_image, (px, rect_y), (px + char_w, rect_y + char_h), (int(b), int(g), int(r)), -1)

        return ascii_image

    def _render_pixelart_to_image(self, resized_color, resized_mask, frame_h, frame_w) -> np.ndarray:
        n_colors = self.pixel_art_config.get('color_palette_size', 16)
        use_fixed = self.pixel_art_config.get('use_fixed_palette', False)
        palette_name = self.pixel_art_config.get('fixed_palette_name', None)

        custom_palette = None
        if use_fixed and palette_name and palette_name in FIXED_PALETTES:
            custom_palette = FIXED_PALETTES[palette_name]['colors']

        height, width = resized_color.shape[:2]

        try:
            quantized = quantize_colors(resized_color, n_colors, use_fixed_palette=use_fixed, custom_palette=custom_palette)
        except Exception:
            quantized = resized_color

        if self.render_mode == RENDER_MODE_USER:
            mask_filter = resized_mask <= 127
        elif self.render_mode == RENDER_MODE_BACKGROUND:
            mask_filter = resized_mask > 127
        else:
            mask_filter = np.ones((height, width), dtype=bool)

        filtered = quantized.copy()
        filtered[~mask_filter] = 0

        pixel_image = cv2.resize(filtered, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)

        return pixel_image

    def _set_status(self, text: str):
        if self.lbl_status:
            prefix = ""
            if self.is_recording_mp4:
                prefix += f"[REC MP4: {self.mp4_frame_count}] "
            if self.is_recording_ascii:
                prefix += f"[REC TXT: {len(self.ascii_frames)}] "

            self.lbl_status.set_text(prefix + text if prefix else f"Status: {text}")

    def _update_frame(self) -> bool:
        self._frame_counter += 1

        if self._frame_counter % 30 == 0:
            self._check_config_reload()

        if hasattr(self, '_paused') and self._paused:
            return True

        w, h = self.target_dimensions
        complexity = w * h

        active_effects = 0
        if self.style_enabled and self.style_preset != 'none':
            active_effects += 1
        if self.optical_flow_enabled:
            active_effects += 1
        if self.matrix_enabled:
            active_effects += 1
        if self.postfx_enabled:
            active_effects += 1
        if self.conversion_mode == MODE_PIXELART:
            active_effects += 1

        skip_frames = 1
        if not self.is_recording_mp4:
            if active_effects >= 4:
                skip_frames = 4
            elif active_effects >= 3:
                skip_frames = 3
            elif active_effects >= 2 or complexity > 6000:
                skip_frames = 2
            elif complexity > 4000:
                skip_frames = 2

        if self._frame_counter % skip_frames != 0:
            return True

        if not self.cap or not self.cap.isOpened():
            return False

        ret, frame = self.cap.read()
        if not ret:
            if self.is_video_file:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return True
            return False

        if not self.is_video_file:
            frame = cv2.flip(frame, 1)

        if self.converter_config.get('sharpen_enabled', True):
            frame = sharpen_frame(frame, self.converter_config.get('sharpen_amount', 0.5))

        if self.optical_flow_enabled and self.optical_flow_interpolator:
            if self._frame_counter % 2 == 0:
                frame = self.optical_flow_interpolator.apply_motion_blur(frame)

        self.current_frame = frame.copy()

        frame_h, frame_w = frame.shape[:2]
        self.source_aspect_ratio = frame_w / frame_h

        if self.auto_seg_enabled and self.auto_segmenter:
            try:
                max_autoseg_size = 320
                if max(frame_h, frame_w) > max_autoseg_size:
                    scale = max_autoseg_size / max(frame_h, frame_w)
                    small_h, small_w = int(frame_h * scale), int(frame_w * scale)
                    small_frame = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
                    small_mask = self.auto_segmenter.process(small_frame)
                    mask = cv2.resize(small_mask, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)
                else:
                    mask = self.auto_segmenter.process(frame)
            except Exception as e:
                print(f"[WARN] Auto Seg falhou: {e}. Usando HSV fallback.")
                self.auto_seg_enabled = False
                if self.chk_auto_seg:
                    self.chk_auto_seg.set_active(False)
                values = self._get_current_hsv_values()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower = np.array([values['h_min'], values['s_min'], values['v_min']])
                upper = np.array([values['h_max'], values['s_max'], values['v_max']])
                mask = cv2.inRange(hsv, lower, upper)
                mask = apply_morphological_refinement(mask, values['erode'], values['dilate'])
        else:
            values = self._get_current_hsv_values()
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = np.array([values['h_min'], values['s_min'], values['v_min']])
            upper = np.array([values['h_max'], values['s_max'], values['v_max']])
            mask = cv2.inRange(hsv, lower, upper)
            mask = apply_morphological_refinement(mask, values['erode'], values['dilate'])

        self.current_mask = mask.copy()

        chroma_vis = self._create_chroma_visualization(frame, mask)

        self._set_frame_to_image(self.image_original, self.aspect_original, frame)
        self._set_frame_to_image(self.image_chroma, self.aspect_chroma, chroma_vis)

        try:
            render_start = time.time()

            grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized_gray = cv2.resize(grayscale, self.target_dimensions, interpolation=cv2.INTER_AREA)
            resized_color = cv2.resize(frame, self.target_dimensions, interpolation=cv2.INTER_AREA)
            resized_mask = cv2.resize(mask, self.target_dimensions, interpolation=cv2.INTER_NEAREST)

            if self.style_enabled and self.style_processor:
                resized_color = self.style_processor.process(resized_color)
                resized_gray = cv2.cvtColor(resized_color, cv2.COLOR_BGR2GRAY)

            sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.hypot(sobel_x, sobel_y)
            angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
            angle = (angle + 180) % 180
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            if self.conversion_mode == MODE_PIXELART:
                result_image = self._render_pixelart_to_image(resized_color, resized_mask, frame_h, frame_w)
            elif self.braille_enabled:
                braille_grid = self._convert_to_braille(resized_gray, self.braille_threshold)

                if self.temporal_enabled:
                    braille_gray = resized_gray[::4, ::2]
                    braille_grid = self._apply_temporal_coherence(braille_grid, braille_gray, self.temporal_threshold)

                result_image = self._render_braille_to_image(braille_grid, resized_color, resized_mask, frame_h, frame_w)
            else:
                result_image = self._render_ascii_to_image(resized_gray, resized_color, resized_mask, magnitude_norm, angle, frame_h, frame_w)

            render_time = time.time() - render_start
            if render_time > 0:
                self._render_fps = 1.0 / render_time

            if result_image is None or result_image.size == 0:
                print(f"[ERRO] result_image vazio! dims: {self.target_dimensions}, frame: {frame_h}x{frame_w}")
                return True

            if self.matrix_enabled and not self.matrix_rain_instance:
                self._reinit_matrix_rain()

            if self.matrix_enabled and self.matrix_rain_instance:
                result_image = self._apply_matrix_rain(result_image, resized_mask)

            if self.audio_enabled and self.audio_modulator and self.postfx_processor:
                self._apply_audio_modulation()

            if self.postfx_enabled and self.postfx_processor:
                result_image = self.postfx_processor.process(result_image)

            self._set_frame_to_image(self.image_ascii, self.aspect_ascii, result_image)

            self._cached_ascii_data = (resized_gray, resized_color, resized_mask, magnitude_norm, angle)

            if self.is_recording_mp4 and result_image is not None:
                frame_filename = os.path.join(self.mp4_temp_dir, f"frame_{self.mp4_frame_count:06d}.png")
                cv2.imwrite(frame_filename, result_image)
                self.mp4_frame_count += 1
        except cv2.error as e:
            print(f"[ERRO CV2] Dimensoes: {self.target_dimensions}, Erro: {e}")
            import traceback
            traceback.print_exc()
            return True
        except Exception as e:
            print(f"[ERRO GERAL] Dimensoes: {self.target_dimensions}, Erro: {e}")
            import traceback
            traceback.print_exc()
            return True

        if self.is_recording_ascii and self._cached_ascii_data:
            resized_gray, resized_color, resized_mask, magnitude_norm, angle = self._cached_ascii_data

            mask_for_file = resized_mask.copy()
            if self.render_mode == RENDER_MODE_BACKGROUND:
                mask_for_file = 255 - mask_for_file
            elif self.render_mode == RENDER_MODE_BOTH:
                mask_for_file = np.zeros_like(mask_for_file)

            frame_for_file = converter_frame_para_ascii(
                resized_gray, resized_color, mask_for_file,
                magnitude_norm, angle,
                self.converter_config['sobel_threshold'],
                self.converter_config['luminance_ramp'],
                output_format="file",
                edge_boost_enabled=self.edge_boost_enabled,
                edge_boost_amount=self.edge_boost_amount,
                use_edge_chars=self.use_edge_chars
            )
            self.ascii_frames.append(frame_for_file)

        return True

    def _force_rerender(self):
        if not self._cached_ascii_data or self.current_frame is None:
            return

        resized_gray, resized_color, resized_mask, magnitude_norm, angle = self._cached_ascii_data
        frame_h, frame_w = self.current_frame.shape[:2]

        if self.conversion_mode == MODE_PIXELART:
            result_image = self._render_pixelart_to_image(resized_color, resized_mask, frame_h, frame_w)
        elif self.braille_enabled:
            braille_grid = self._convert_to_braille(resized_gray, self.braille_threshold)
            if self.temporal_enabled:
                braille_gray = resized_gray[::4, ::2]
                braille_grid = self._apply_temporal_coherence(braille_grid, braille_gray, self.temporal_threshold)
            result_image = self._render_braille_to_image(braille_grid, resized_color, resized_mask, frame_h, frame_w)
        else:
            result_image = self._render_ascii_to_image(resized_gray, resized_color, resized_mask, magnitude_norm, angle, frame_h, frame_w)

        if result_image is None or result_image.size == 0:
            return

        if self.matrix_enabled and self.matrix_rain_instance:
            result_image = self._apply_matrix_rain(result_image, resized_mask)

        if self.postfx_enabled and self.postfx_processor:
            result_image = self.postfx_processor.process(result_image)

        self._set_frame_to_image(self.image_ascii, self.aspect_ascii, result_image)

    def _get_ascii_area_geometry(self):
        if not self.aspect_ascii or not self.aspect_ascii.get_window():
            return None

        alloc = self.aspect_ascii.get_allocation()
        window = self.aspect_ascii.get_window()
        x_root, y_root = window.get_root_coords(alloc.x, alloc.y)

        return {
            'x': x_root,
            'y': y_root,
            'width': alloc.width,
            'height': alloc.height
        }

    def _start_mp4_recording(self):
        if self.is_recording_mp4:
            return

        if not self.cap or not self.cap.isOpened():
            self._set_status("Erro: Webcam nao esta aberta")
            return

        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if actual_fps <= 0 or actual_fps > 60:
            actual_fps = 30
        self.recording_fps = actual_fps

        output_dir = os.path.expanduser("~/Vídeos")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.mp4_output_file = os.path.join(output_dir, f"webcam_ascii_{timestamp}.mp4")

        self.mp4_temp_dir = tempfile.mkdtemp(prefix="ascii_webcam_")
        self.mp4_frame_count = 0
        self.mp4_start_time = time.time()
        self.is_recording_mp4 = True

        temp_audio = os.path.join(self.mp4_temp_dir, "audio.aac")
        cmd_audio = [
            'ffmpeg', '-y',
            '-f', 'pulse',
            '-i', 'default',
            '-c:a', 'aac',
            '-b:a', '192k',
            temp_audio
        ]

        try:
            self.mp4_audio_process = subprocess.Popen(
                cmd_audio,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[DEBUG] Captura de audio iniciada (PID: {self.mp4_audio_process.pid})")
        except Exception as e:
            print(f"[DEBUG] Erro ao iniciar captura de audio: {e}")
            self.mp4_audio_process = None

        if self.btn_record_mp4:
            context = self.btn_record_mp4.get_style_context()
            context.add_class("recording-active")

        self._set_status(f"Gravacao iniciada ({actual_fps:.1f} fps)")
        print(f"[DEBUG] Salvando frames em: {self.mp4_temp_dir}")
        print(f"[DEBUG] FPS da webcam: {actual_fps}")

    def _stop_mp4_recording(self):
        if not self.is_recording_mp4:
            return

        self.is_recording_mp4 = False
        recording_duration = time.time() - self.mp4_start_time

        if self.btn_record_mp4:
            context = self.btn_record_mp4.get_style_context()
            context.remove_class("recording-active")

        if self.mp4_audio_process:
            try:
                print("[DEBUG] Parando captura de audio...")
                self.mp4_audio_process.send_signal(signal.SIGINT)
                self.mp4_audio_process.wait(timeout=3)
            except:
                self.mp4_audio_process.kill()
                self.mp4_audio_process.wait()

        self._set_status(f"Processando {self.mp4_frame_count} frames...")
        print(f"[DEBUG] Parando gravacao. Total de frames: {self.mp4_frame_count}")
        print(f"[DEBUG] Duracao da gravacao: {recording_duration:.2f}s")

        actual_fps = self.mp4_frame_count / recording_duration if recording_duration > 0 else self.recording_fps
        print(f"[DEBUG] FPS real calculado: {actual_fps:.2f} (reportado: {self.recording_fps:.2f})")

        self.recording_fps = actual_fps

        if self.mp4_frame_count == 0:
            self._set_status("Erro: Nenhum frame gravado")
            if self.mp4_temp_dir and os.path.exists(self.mp4_temp_dir):
                shutil.rmtree(self.mp4_temp_dir, ignore_errors=True)
            return

        try:
            temp_video = os.path.join(self.mp4_temp_dir, "temp_video.mp4")
            temp_audio = os.path.join(self.mp4_temp_dir, "audio.aac")

            print("[DEBUG] Criando video ASCII...")
            cmd_video = [
                'ffmpeg', '-y',
                '-framerate', str(self.recording_fps),
                '-i', os.path.join(self.mp4_temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                temp_video
            ]

            result = subprocess.run(cmd_video, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                raise RuntimeError(f"Erro ao criar video: {result.stderr}")

            has_audio = os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 1024

            if has_audio:
                print("[DEBUG] Muxando video + audio...")
                cmd_mux = [
                    'ffmpeg', '-y',
                    '-i', temp_video,
                    '-i', temp_audio,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-shortest',
                    self.mp4_output_file
                ]
                result = subprocess.run(cmd_mux, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if result.returncode != 0:
                    print(f"[DEBUG] Erro ao muxar audio: {result.stderr}")
                    shutil.copy(temp_video, self.mp4_output_file)
            else:
                print("[DEBUG] Sem audio capturado, salvando apenas video...")
                shutil.copy(temp_video, self.mp4_output_file)

            self._set_status(f"Video salvo: {os.path.basename(self.mp4_output_file)}")
            print(f"[DEBUG] Video ASCII salvo em: {self.mp4_output_file}")

        except Exception as e:
            self._set_status(f"Erro ao criar MP4: {e}")
            print(f"[DEBUG] Erro: {e}")

        finally:
            if self.mp4_temp_dir and os.path.exists(self.mp4_temp_dir):
                print(f"[DEBUG] Limpando arquivos temporarios...")
                shutil.rmtree(self.mp4_temp_dir, ignore_errors=True)

        if os.path.exists(self.mp4_output_file):
            size = os.path.getsize(self.mp4_output_file)
            print(f"[DEBUG] Arquivo criado: {self.mp4_output_file} ({size} bytes)")
        else:
            print(f"[DEBUG] ERRO: Arquivo nao existe: {self.mp4_output_file}")

        self._show_recording_finished_dialog(self.mp4_output_file, "MP4")

    def _start_ascii_recording(self):
        if self.is_recording_ascii:
            return
        self.ascii_frames = []
        self.is_recording_ascii = True

        if self.btn_record_ascii:
            context = self.btn_record_ascii.get_style_context()
            context.add_class("recording-active")

        self._set_status("Gravacao ASCII iniciada")

    def _stop_ascii_recording(self):
        if not self.is_recording_ascii:
            return

        self.is_recording_ascii = False

        if self.btn_record_ascii:
            context = self.btn_record_ascii.get_style_context()
            context.remove_class("recording-active")

        if len(self.ascii_frames) == 0:
            self._set_status("Nenhum frame gravado")
            return

        output_dir = os.path.expanduser("~/Vídeos")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"gravacao_{timestamp}.txt")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{self.recording_fps}\n")
                f.write("[FRAME]\n".join(self.ascii_frames))

            self.ascii_frames = []
            self._show_recording_finished_dialog(output_file, "ASCII")
        except Exception as e:
            self._set_status(f"Erro: {e}")
            self.ascii_frames = []

    def _show_recording_finished_dialog(self, filepath, file_type):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Gravacao {file_type} Finalizada!"
        )

        filename = os.path.basename(filepath)
        dialog.format_secondary_text(
            f"Arquivo salvo com sucesso:\n\n{filename}\n\n"
            f"Local: {os.path.dirname(filepath)}"
        )

        dialog.add_button("Ver Pasta", 1)
        dialog.add_button("Reproduzir", 2)
        dialog.add_button("Fechar", Gtk.ResponseType.CLOSE)

        response = dialog.run()
        dialog.destroy()

        if response == 1:
            subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
            self._set_status("Pasta aberta")
        elif response == 2:
            subprocess.Popen(["xdg-open", filepath])
            self._set_status("Reproduzindo arquivo")
        else:
            self._set_status(f"{file_type} salvo: {filename}")

    def _save_and_open_preview(self):
        self.on_save_config_clicked(None)

        GLib.timeout_add(100, self._delayed_open_preview)

    def _delayed_open_preview(self):
        self._open_terminal_preview()

        GLib.timeout_add(200, self._close_window)
        return False

    def _close_window(self):
        self._cleanup()
        self.window.hide()

        GLib.timeout_add(500, self._quit_application)
        return False

    def _quit_application(self):
        self.window.destroy()
        if Gtk.main_level() > 0:
            Gtk.main_quit()
        return False

    def _open_terminal_preview(self):
        realtime_script = os.path.join(BASE_DIR, "src", "core", "realtime_ascii.py")
        python_exec = sys.executable
        cmd_base = [python_exec, realtime_script, "--config", self.config_path]
        title = "Extase em 4R73 - Preview"

        if self.video_path:
            cmd_base.extend(["--video", self.video_path])

        font_family = self.terminal_font.get('family', 'monospace') if self.terminal_font else 'monospace'
        font_size = self.terminal_font.get('size', 12) if self.terminal_font else 12

        try:
            cmd = ['kitty', '--class=extase-em-4r73', f'--title={title}',
                   '-o', f'font_family={font_family}',
                   '-o', f'font_size={font_size}',
                   '--start-as=maximized', '--'] + cmd_base
            subprocess.Popen(cmd)
            self._set_status(f"Preview: {font_family} {font_size}pt")
        except FileNotFoundError:
            try:
                cmd = ['gnome-terminal', '--maximize', f'--title={title}',
                       '--class=extase-em-4r73', '--'] + cmd_base
                subprocess.Popen(cmd)
                self._set_status(f"Preview: {font_family} {font_size}pt (gnome)")
            except FileNotFoundError:
                try:
                    xft_font = f'{font_family}:size={font_size}'
                    cmd = ['xterm', '-maximized', '-title', title,
                           '-fa', font_family, '-fs', str(font_size),
                           '-e'] + cmd_base
                    subprocess.Popen(cmd)
                    self._set_status(f"Preview: {font_family} {font_size}pt (xterm)")
                except Exception as e:
                    self._set_status(f"Erro terminal: {e}")
            except Exception as e:
                self._set_status(f"Erro terminal: {e}")
        except Exception as e:
            self._set_status(f"Erro terminal: {e}")

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_q or event.keyval == Gdk.KEY_Q:
            self._cleanup()
            Gtk.main_quit()
            return True
        elif event.keyval == Gdk.KEY_space:
            self._toggle_pause()
            return True
        return False

    def _toggle_pause(self):
        if hasattr(self, '_paused'):
            self._paused = not self._paused
        else:
            self._paused = True
        status = "PAUSADO" if self._paused else "Capturando..."
        self._set_status(status)

    def on_hsv_changed(self, widget):
        if self._block_signals:
            return

        self._block_signals = True
        try:
            # Enforce Min <= Max constraints
            h_min = self.scale_h_min.get_value()
            h_max = self.scale_h_max.get_value()
            if h_min > h_max:
                if widget == self.scale_h_min:
                    self.scale_h_max.set_value(h_min)
                else:
                    self.scale_h_min.set_value(h_max)

            s_min = self.scale_s_min.get_value()
            s_max = self.scale_s_max.get_value()
            if s_min > s_max:
                if widget == self.scale_s_min:
                    self.scale_s_max.set_value(s_min)
                else:
                    self.scale_s_min.set_value(s_max)

            v_min = self.scale_v_min.get_value()
            v_max = self.scale_v_max.get_value()
            if v_min > v_max:
                if widget == self.scale_v_min:
                    self.scale_v_max.set_value(v_min)
                else:
                    self.scale_v_min.set_value(v_max)
        finally:
            self._block_signals = False

        values = self._get_current_hsv_values()
        status_text = f"H:{values['h_min']}-{values['h_max']} S:{values['s_min']}-{values['s_max']} V:{values['v_min']}-{values['v_max']}"
        self._set_status(status_text)

    def on_ascii_config_changed(self, widget):
        if self._block_signals:
            return

        try:
            w = int(self.spin_width.get_value())
            h = int(self.spin_height.get_value())

            if w < 40:
                w = 40
                self._block_signals = True
                self.spin_width.set_value(40)
                self._block_signals = False
            elif w > 150:
                w = 150
                self._block_signals = True
                self.spin_width.set_value(150)
                self._block_signals = False

            if 0 < h < 20:
                h = 20
                self._block_signals = True
                self.spin_height.set_value(20)
                self._block_signals = False
            elif h > 125:
                h = 125
                self._block_signals = True
                self.spin_height.set_value(125)
                self._block_signals = False

            self.converter_config['target_width'] = w
            self.converter_config['target_height'] = h
            self.converter_config['sobel_threshold'] = int(self.scale_sobel.get_value())
            self.converter_config['sharpen_amount'] = self.scale_sharpen.get_value()
            self.converter_config['sharpen_enabled'] = self.chk_sharpen.get_active()

            self._update_target_dimensions()

            complexity = w * h if h > 0 else w * 48
            fps_info = f" | {self._render_fps:.1f} FPS" if self._render_fps > 0 else ""
            self._set_status(f"{w}x{h if h > 0 else 'AUTO'} ({complexity} chars){fps_info}")
        except Exception as e:
            print(f"[ERRO on_ascii_config_changed] {e}")
            import traceback
            traceback.print_exc()

    def on_pixel_art_changed(self, widget):
        if self._block_signals:
            return

        if self.spin_pixel_size:
            self.pixel_art_config['pixel_size'] = int(self.spin_pixel_size.get_value())
        if self.spin_palette_size:
            self.pixel_art_config['color_palette_size'] = int(self.spin_palette_size.get_value())
        self._force_rerender()

    def on_fixed_palette_toggled(self, widget):
        if self._block_signals:
            return

        use_fixed = widget.get_active()
        self.pixel_art_config['use_fixed_palette'] = use_fixed

        if self.combo_fixed_palette:
            self.combo_fixed_palette.set_sensitive(use_fixed)

        self._set_status(f"Paleta fixa: {'Ativada' if use_fixed else 'Desativada'}")
        self._force_rerender()

    def on_fixed_palette_changed(self, widget):
        if self._block_signals:
            return

        palette_id = widget.get_active_id()
        if palette_id and palette_id in FIXED_PALETTES:
            self.pixel_art_config['fixed_palette_name'] = palette_id
            self._set_status(f"Paleta: {FIXED_PALETTES[palette_id]['name']}")
            self._force_rerender()

    def on_ramp_preset_changed(self, widget):
        if self._block_signals:
            return

        preset_id = widget.get_active_id()
        if preset_id and preset_id in LUMINANCE_RAMPS:
            self.converter_config['luminance_ramp'] = LUMINANCE_RAMPS[preset_id]['ramp']
            self.converter_config['luminance_preset'] = preset_id
            self._set_status(f"Rampa: {LUMINANCE_RAMPS[preset_id]['name']}")
            self._force_rerender()

    def on_mode_toggled(self, widget):
        if self._block_signals:
            return

        if not widget.get_active():
            return

        if widget == self.radio_ascii:
            self.conversion_mode = MODE_ASCII
            self._set_status("Modo: ASCII")
        else:
            self.conversion_mode = MODE_PIXELART
            self._set_status("Modo: Pixel Art")

        self._update_mode_visibility()

    def on_render_mode_changed(self, widget):
        active = widget.get_active()
        if active == 0:
            self.render_mode = RENDER_MODE_USER
            self._set_status("Render: User (frente)")
        elif active == 1:
            self.render_mode = RENDER_MODE_BACKGROUND
            self._set_status("Render: BG (fundo)")
        else:
            self.render_mode = RENDER_MODE_BOTH
            self._set_status("Render: Ambos")
        self._force_rerender()

    def on_gpu_settings_changed(self, widget):
        if self._block_signals:
            return

        self.braille_enabled = self.chk_braille.get_active() if self.chk_braille else False
        self.braille_threshold = int(self.scale_braille_threshold.get_value()) if self.scale_braille_threshold else 128
        self.temporal_enabled = self.chk_temporal.get_active() if self.chk_temporal else False
        self.temporal_threshold = int(self.scale_temporal_threshold.get_value()) if self.scale_temporal_threshold else 10

        if self.scale_braille_threshold:
            self.scale_braille_threshold.set_sensitive(self.braille_enabled)
        if self.scale_temporal_threshold:
            self.scale_temporal_threshold.set_sensitive(self.temporal_enabled)

        if not self.temporal_enabled:
            self._prev_char_grid = None
            self._prev_gray = None

        status_parts = []
        if self.braille_enabled:
            status_parts.append(f"Braille:{self.braille_threshold}")
        if self.temporal_enabled:
            status_parts.append(f"Temporal:{self.temporal_threshold}")

        if status_parts:
            self._set_status(f"GPU: {' | '.join(status_parts)}")
        else:
            self._set_status("GPU: Desativado")
        self._force_rerender()

    def on_auto_seg_changed(self, widget):
        if self._block_signals:
            return

        prev_enabled = self.auto_seg_enabled
        self.auto_seg_enabled = self.chk_auto_seg.get_active() if self.chk_auto_seg else False

        if self.auto_seg_enabled and not prev_enabled:
            if AUTO_SEG_AVAILABLE:
                try:
                    if self.auto_segmenter:
                        self.auto_segmenter.close()
                    self.auto_segmenter = AutoSegmenter(threshold=0.5, use_gpu=True)
                    self._set_status("Auto Seg: Ativado (MediaPipe)")
                except Exception as e:
                    self.auto_seg_enabled = False
                    if self.chk_auto_seg:
                        self.chk_auto_seg.set_active(False)
                    self._set_status(f"Auto Seg: Erro - {e}")
            else:
                self.auto_seg_enabled = False
                if self.chk_auto_seg:
                    self.chk_auto_seg.set_active(False)
                self._set_status("Auto Seg: MediaPipe nao disponivel")
        elif not self.auto_seg_enabled and prev_enabled:
            if self.auto_segmenter:
                self.auto_segmenter.close()
                self.auto_segmenter = None
            self._set_status("Auto Seg: Desativado")

        hsv_sensitive = not self.auto_seg_enabled
        for scale_name in ['scale_h_min', 'scale_h_max', 'scale_s_min', 'scale_s_max',
                           'scale_v_min', 'scale_v_max', 'scale_erode', 'scale_dilate']:
            scale = getattr(self, scale_name, None)
            if scale:
                scale.set_sensitive(hsv_sensitive)

    def on_edge_boost_changed(self, widget):
        if self._block_signals:
            return

        self.edge_boost_enabled = self.chk_edge_boost.get_active() if self.chk_edge_boost else False
        self.edge_boost_amount = int(self.scale_edge_boost_amount.get_value()) if self.scale_edge_boost_amount else 100
        self.use_edge_chars = self.chk_use_edge_chars.get_active() if self.chk_use_edge_chars else True

        if self.scale_edge_boost_amount:
            self.scale_edge_boost_amount.set_sensitive(self.edge_boost_enabled)

        status = "Edge Boost: Ativado" if self.edge_boost_enabled else "Edge Boost: Desativado"
        if self.edge_boost_enabled:
            status += f" ({self.edge_boost_amount})"
        self._set_status(status)
        self._force_rerender()

    def on_matrix_settings_changed(self, widget):
        if self._block_signals:
            return

        prev_enabled = self.matrix_enabled
        self.matrix_enabled = self.chk_matrix.get_active() if self.chk_matrix else False

        if self.combo_matrix_mode:
            mode_id = self.combo_matrix_mode.get_active_id()
            if mode_id:
                self.matrix_mode = mode_id

        if self.combo_matrix_charset:
            charset_id = self.combo_matrix_charset.get_active_id()
            if charset_id:
                self.matrix_charset = charset_id

        if self.spin_matrix_particles:
            self.matrix_particles = int(self.spin_matrix_particles.get_value())
            self.spin_matrix_particles.set_sensitive(self.matrix_enabled)

        if self.scale_matrix_speed:
            self.matrix_speed = self.scale_matrix_speed.get_value()
            self.scale_matrix_speed.set_sensitive(self.matrix_enabled)

        if self.combo_matrix_mode:
            self.combo_matrix_mode.set_sensitive(self.matrix_enabled)
        if self.combo_matrix_charset:
            self.combo_matrix_charset.set_sensitive(self.matrix_enabled)

        if self.matrix_enabled and self.matrix_rain_instance:
            self.matrix_rain_instance.change_char_set(self.matrix_charset)
            self.matrix_rain_instance.set_speed(self.matrix_speed)

        if self.matrix_enabled and not self.matrix_rain_instance:
            self._reinit_matrix_rain()
        elif not self.matrix_enabled and self.matrix_rain_instance:
            self.matrix_rain_instance = None

        if self.matrix_enabled:
            charset_label = {
                'katakana': 'Katakana',
                'binary': 'Binary',
                'hex': 'Hex',
                'ascii': 'ASCII',
                'math': 'Math'
            }.get(self.matrix_charset, self.matrix_charset)
            self._set_status(f"Matrix: {self.matrix_mode.capitalize()} | {charset_label} | {self.matrix_particles}p | {self.matrix_speed:.1f}x")
        else:
            self._set_status("Matrix: Desativado")
        self._force_rerender()

    def _reinit_matrix_rain(self):
        if self.matrix_rain_instance:
            del self.matrix_rain_instance
            self.matrix_rain_instance = None

        if self.matrix_enabled and MATRIX_RAIN_AVAILABLE:
            try:
                w, h = self.target_dimensions
                self.matrix_rain_instance = MatrixRainGPU(
                    w, h,
                    num_particles=self.matrix_particles,
                    char_set=self.matrix_charset,
                    speed_multiplier=self.matrix_speed
                )
                print(f"[Matrix Rain] Inicializado: {w}x{h}, {self.matrix_particles} particulas")
            except Exception as e:
                print(f"[ERRO] Falha ao inicializar Matrix Rain: {e}")
                self.matrix_rain_instance = None

    def _apply_matrix_rain(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        try:
            self.matrix_rain_instance.update(dt=0.05)

            w, h = self.target_dimensions
            canvas_char = np.full((h, w), ord(' '), dtype=np.uint16)
            canvas_color = np.zeros((h, w, 3), dtype=np.uint8)

            self.matrix_rain_instance.render(canvas_char, canvas_color)

            non_zero_grid = (canvas_color.sum(axis=2) > 0)

            if not non_zero_grid.any():
                return image

            result = image.copy()
            img_h, img_w = image.shape[:2]

            char_w_base = 8
            char_h_base = 16

            scale_x = img_w / (w * char_w_base)
            scale_y = img_h / (h * char_h_base)
            scale = min(scale_x, scale_y)

            char_w = max(1, int(char_w_base * scale))
            char_h = max(1, int(char_h_base * scale))

            total_w = w * char_w
            total_h = h * char_h

            offset_x = (img_w - total_w) // 2
            offset_y = (img_h - total_h) // 2

            font_scale = max(0.3, 0.4 * scale)

            ys, xs = np.where(non_zero_grid)

            for i in range(len(ys)):
                grid_y, grid_x = ys[i], xs[i]
                r, g, b = canvas_color[grid_y, grid_x]
                char_code = canvas_char[grid_y, grid_x]

                px = offset_x + grid_x * char_w
                py = offset_y + grid_y * char_h + char_h - 3

                if 0 <= px < img_w and 0 <= py < img_h:
                    char = chr(char_code)
                    color = (int(b), int(g), int(r))

                    should_draw = False

                    if self.matrix_mode == 'overlay':
                        should_draw = True
                    elif self.matrix_mode == 'background':
                        if mask is not None and grid_y < mask.shape[0] and grid_x < mask.shape[1]:
                            should_draw = (mask[grid_y, grid_x] == 0)
                        else:
                            should_draw = True
                    elif self.matrix_mode == 'user':
                        if mask is not None and grid_y < mask.shape[0] and grid_x < mask.shape[1]:
                            should_draw = (mask[grid_y, grid_x] > 0)
                    else:
                        should_draw = True

                    if should_draw:
                        cv2.putText(result, char, (px, py), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)

            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return image

    def _init_postfx(self):
        if not POSTFX_AVAILABLE:
            if self.chk_bloom:
                self.chk_bloom.set_sensitive(False)
            if self.chk_chromatic:
                self.chk_chromatic.set_sensitive(False)
            if self.chk_scanlines:
                self.chk_scanlines.set_sensitive(False)
            if self.chk_glitch:
                self.chk_glitch.set_sensitive(False)
            return

        if 'PostFX' in self.config:
            bloom_enabled = self.config.getboolean('PostFX', 'bloom_enabled', fallback=False)
            chromatic_enabled = self.config.getboolean('PostFX', 'chromatic_enabled', fallback=False)
            scanlines_enabled = self.config.getboolean('PostFX', 'scanlines_enabled', fallback=False)
            glitch_enabled = self.config.getboolean('PostFX', 'glitch_enabled', fallback=False)

            if self.chk_bloom:
                self.chk_bloom.set_active(bloom_enabled)
            if self.chk_chromatic:
                self.chk_chromatic.set_active(chromatic_enabled)
            if self.chk_scanlines:
                self.chk_scanlines.set_active(scanlines_enabled)
            if self.chk_glitch:
                self.chk_glitch.set_active(glitch_enabled)

            self.postfx_enabled = any([bloom_enabled, chromatic_enabled, scanlines_enabled, glitch_enabled])

            if self.postfx_enabled:
                self.postfx_config = PostFXConfig(
                    bloom_enabled=bloom_enabled,
                    bloom_intensity=self.config.getfloat('PostFX', 'bloom_intensity', fallback=0.6),
                    bloom_radius=self.config.getint('PostFX', 'bloom_radius', fallback=15),
                    bloom_threshold=self.config.getint('PostFX', 'bloom_threshold', fallback=150),
                    chromatic_enabled=chromatic_enabled,
                    chromatic_shift=self.config.getint('PostFX', 'chromatic_shift', fallback=5),
                    scanlines_enabled=scanlines_enabled,
                    scanlines_intensity=self.config.getfloat('PostFX', 'scanlines_intensity', fallback=0.5),
                    scanlines_spacing=self.config.getint('PostFX', 'scanlines_spacing', fallback=3),
                    glitch_enabled=glitch_enabled,
                    glitch_intensity=self.config.getfloat('PostFX', 'glitch_intensity', fallback=0.3),
                    glitch_block_size=self.config.getint('PostFX', 'glitch_block_size', fallback=16)
                )
                self.postfx_processor = PostFXProcessor(self.postfx_config)

    def _init_style(self):
        if not STYLE_TRANSFER_AVAILABLE:
            if self.chk_style:
                self.chk_style.set_sensitive(False)
            if self.combo_style_preset:
                self.combo_style_preset.set_sensitive(False)
            return

        if self.combo_style_preset:
            self.combo_style_preset.remove_all()
            for preset_id, preset_data in STYLE_PRESETS.items():
                self.combo_style_preset.append(preset_id, preset_data['name'])
            self.combo_style_preset.set_active_id('none')
            self.combo_style_preset.set_sensitive(False)

        if 'Style' in self.config:
            style_enabled = self.config.getboolean('Style', 'style_enabled', fallback=False)
            style_preset = self.config.get('Style', 'style_preset', fallback='none')

            if self.chk_style:
                self.chk_style.set_active(style_enabled)
            if self.combo_style_preset:
                self.combo_style_preset.set_active_id(style_preset)
                self.combo_style_preset.set_sensitive(style_enabled)

            self.style_enabled = style_enabled and style_preset != 'none'
            self.style_preset = style_preset

            if self.style_enabled:
                self.style_processor = StyleTransferProcessor()
                self.style_processor.config.style_enabled = True
                self.style_processor.set_preset(self.style_preset)

    def on_postfx_changed(self, widget):
        if self._block_signals:
            return

        bloom = self.chk_bloom.get_active() if self.chk_bloom else False
        chromatic = self.chk_chromatic.get_active() if self.chk_chromatic else False
        scanlines = self.chk_scanlines.get_active() if self.chk_scanlines else False
        glitch = self.chk_glitch.get_active() if self.chk_glitch else False

        self.postfx_enabled = any([bloom, chromatic, scanlines, glitch])

        if self.postfx_enabled and POSTFX_AVAILABLE:
            if self.postfx_config is None:
                self.postfx_config = PostFXConfig()

            self.postfx_config.bloom_enabled = bloom
            self.postfx_config.chromatic_enabled = chromatic
            self.postfx_config.scanlines_enabled = scanlines
            self.postfx_config.glitch_enabled = glitch

            if self.postfx_processor is None:
                self.postfx_processor = PostFXProcessor(self.postfx_config)
            else:
                self.postfx_processor.config = self.postfx_config

        effects = []
        if bloom:
            effects.append("Bloom")
        if chromatic:
            effects.append("Chrom")
        if scanlines:
            effects.append("Scan")
        if glitch:
            effects.append("Glitch")

        if effects:
            self._set_status(f"FX: {' | '.join(effects)}")
        else:
            self._set_status("FX: Desativado")
        self._force_rerender()

    def on_style_changed(self, widget):
        if self._block_signals:
            return

        style_enabled = self.chk_style.get_active() if self.chk_style else False
        preset_id = None

        if self.combo_style_preset:
            preset_id = self.combo_style_preset.get_active_id()

        self.style_enabled = style_enabled and preset_id and preset_id != 'none'
        self.style_preset = preset_id or 'none'

        if self.style_enabled and STYLE_TRANSFER_AVAILABLE:
            if self.style_processor is None:
                self.style_processor = StyleTransferProcessor()

            self.style_processor.config.style_enabled = True
            self.style_processor.set_preset(self.style_preset)

            if preset_id in STYLE_PRESETS:
                self._set_status(f"Style: {STYLE_PRESETS[preset_id]['name']}")
        else:
            if self.style_processor:
                self.style_processor.config.style_enabled = False
            self._set_status("Style: Desativado")

        if self.combo_style_preset:
            self.combo_style_preset.set_sensitive(style_enabled)

    def _init_optical_flow(self):
        if not OPTICAL_FLOW_AVAILABLE:
            if self.chk_optical_flow:
                self.chk_optical_flow.set_sensitive(False)
            if self.combo_optical_flow_fps:
                self.combo_optical_flow_fps.set_sensitive(False)
            if self.combo_optical_flow_quality:
                self.combo_optical_flow_quality.set_sensitive(False)
            return

        if self.combo_optical_flow_fps:
            self.combo_optical_flow_fps.set_sensitive(False)
        if self.combo_optical_flow_quality:
            self.combo_optical_flow_quality.set_sensitive(False)

        if 'OpticalFlow' in self.config:
            of_enabled = self.config.getboolean('OpticalFlow', 'enabled', fallback=False)
            of_fps = self.config.get('OpticalFlow', 'target_fps', fallback='30')
            of_quality = self.config.get('OpticalFlow', 'quality', fallback='medium')

            if self.chk_optical_flow:
                self.chk_optical_flow.set_active(of_enabled)
            if self.combo_optical_flow_fps:
                self.combo_optical_flow_fps.set_active_id(of_fps)
                self.combo_optical_flow_fps.set_sensitive(of_enabled)
            if self.combo_optical_flow_quality:
                self.combo_optical_flow_quality.set_active_id(of_quality)
                self.combo_optical_flow_quality.set_sensitive(of_enabled)

            self.optical_flow_enabled = of_enabled
            if of_enabled:
                of_config = OpticalFlowConfig(
                    enabled=True,
                    target_fps=int(of_fps),
                    quality=of_quality
                )
                self.optical_flow_interpolator = OpticalFlowInterpolator(of_config)

    def on_optical_flow_changed(self, widget):
        if self._block_signals:
            return

        of_enabled = self.chk_optical_flow.get_active() if self.chk_optical_flow else False
        of_fps = self.combo_optical_flow_fps.get_active_id() if self.combo_optical_flow_fps else '30'
        of_quality = self.combo_optical_flow_quality.get_active_id() if self.combo_optical_flow_quality else 'medium'

        self.optical_flow_enabled = of_enabled

        if of_enabled and OPTICAL_FLOW_AVAILABLE:
            of_config = OpticalFlowConfig(
                enabled=True,
                target_fps=int(of_fps) if of_fps else 30,
                quality=of_quality or 'fast',
                motion_blur_enabled=True,
                motion_blur_intensity=0.5,
                motion_blur_samples=3
            )
            self.optical_flow_interpolator = OpticalFlowInterpolator(of_config)
            self._set_status(f"Motion Blur: ON")
        else:
            self.optical_flow_interpolator = None
            self._set_status("Optical Flow: Desativado")

        if self.combo_optical_flow_fps:
            self.combo_optical_flow_fps.set_sensitive(of_enabled)
        if self.combo_optical_flow_quality:
            self.combo_optical_flow_quality.set_sensitive(of_enabled)

    def _init_audio(self):
        if not AUDIO_AVAILABLE:
            if self.chk_audio:
                self.chk_audio.set_sensitive(False)
            return

        widgets = [self.scale_audio_bass, self.scale_audio_mids, self.scale_audio_treble,
                   self.chk_audio_bloom, self.chk_audio_glitch, self.chk_audio_chrom]
        for w in widgets:
            if w:
                w.set_sensitive(False)

        if self.chk_audio_bloom:
            self.chk_audio_bloom.set_active(True)
        if self.chk_audio_glitch:
            self.chk_audio_glitch.set_active(True)
        if self.chk_audio_chrom:
            self.chk_audio_chrom.set_active(True)

        if 'Audio' in self.config:
            audio_enabled = self.config.getboolean('Audio', 'enabled', fallback=False)
            bass_sens = self.config.getfloat('Audio', 'bass_sensitivity', fallback=1.0)
            mids_sens = self.config.getfloat('Audio', 'mids_sensitivity', fallback=1.0)
            treble_sens = self.config.getfloat('Audio', 'treble_sensitivity', fallback=1.0)

            if self.chk_audio:
                self.chk_audio.set_active(audio_enabled)
            if self.scale_audio_bass:
                self.scale_audio_bass.set_value(bass_sens)
            if self.scale_audio_mids:
                self.scale_audio_mids.set_value(mids_sens)
            if self.scale_audio_treble:
                self.scale_audio_treble.set_value(treble_sens)

            if audio_enabled:
                self._start_audio_analyzer()

    def _start_audio_analyzer(self):
        if not AUDIO_AVAILABLE:
            return

        bass_sens = self.scale_audio_bass.get_value() if self.scale_audio_bass else 1.0
        mids_sens = self.scale_audio_mids.get_value() if self.scale_audio_mids else 1.0
        treble_sens = self.scale_audio_treble.get_value() if self.scale_audio_treble else 1.0

        audio_config = AudioConfig(
            enabled=True,
            bass_sensitivity=bass_sens,
            mids_sensitivity=mids_sens,
            treble_sensitivity=treble_sens
        )

        self.audio_analyzer = AudioAnalyzer(audio_config)
        self.audio_modulator = AudioReactiveModulator(self.audio_analyzer)

        if self.audio_analyzer.start():
            self.audio_enabled = True
            self._set_status("Audio Reactive: Ativado")
        else:
            self.audio_enabled = False
            self._set_status("Audio Reactive: Falha ao iniciar")

    def _stop_audio_analyzer(self):
        if self.audio_analyzer:
            self.audio_analyzer.stop()
            self.audio_analyzer = None
        self.audio_modulator = None
        self.audio_enabled = False

    def on_audio_settings_changed(self, widget):
        if self._block_signals:
            return

        audio_enabled = self.chk_audio.get_active() if self.chk_audio else False

        widgets = [self.scale_audio_bass, self.scale_audio_mids, self.scale_audio_treble,
                   self.chk_audio_bloom, self.chk_audio_glitch, self.chk_audio_chrom]
        for w in widgets:
            if w:
                w.set_sensitive(audio_enabled)

        self.audio_modulate_bloom = self.chk_audio_bloom.get_active() if self.chk_audio_bloom else True
        self.audio_modulate_glitch = self.chk_audio_glitch.get_active() if self.chk_audio_glitch else True
        self.audio_modulate_chromatic = self.chk_audio_chrom.get_active() if self.chk_audio_chrom else True

        if audio_enabled and not self.audio_enabled:
            self._start_audio_analyzer()
            if POSTFX_AVAILABLE:
                if self.postfx_processor is None:
                    self.postfx_config = PostFXConfig()
                    self.postfx_processor = PostFXProcessor(self.postfx_config)
                self.postfx_config.bloom_enabled = self.audio_modulate_bloom
                self.postfx_config.chromatic_enabled = self.audio_modulate_chromatic
                self.postfx_config.glitch_enabled = self.audio_modulate_glitch
                self.postfx_enabled = True
        elif not audio_enabled and self.audio_enabled:
            self._stop_audio_analyzer()
            self._set_status("Audio Reactive: Desativado")

        if self.audio_analyzer and self.audio_analyzer.config:
            if self.scale_audio_bass:
                self.audio_analyzer.config.bass_sensitivity = self.scale_audio_bass.get_value()
            if self.scale_audio_mids:
                self.audio_analyzer.config.mids_sensitivity = self.scale_audio_mids.get_value()
            if self.scale_audio_treble:
                self.audio_analyzer.config.treble_sensitivity = self.scale_audio_treble.get_value()

        if self.audio_enabled and self.postfx_config:
            self.postfx_config.bloom_enabled = self.audio_modulate_bloom
            self.postfx_config.chromatic_enabled = self.audio_modulate_chromatic
            self.postfx_config.glitch_enabled = self.audio_modulate_glitch

    def _apply_audio_modulation(self):
        if not self.audio_modulator or not self.postfx_processor:
            return

        if self.audio_modulate_bloom and self.postfx_processor.config:
            bloom_intensity = self.audio_modulator.get_bloom_intensity()
            self.postfx_processor.config.bloom_intensity = bloom_intensity * 1.5

        if self.audio_modulate_chromatic and self.postfx_processor.config:
            chrom_intensity = self.audio_modulator.get_chromatic_intensity()
            self.postfx_processor.config.chromatic_shift = int(chrom_intensity * 3)

        if self.audio_modulate_glitch and self.postfx_processor.config:
            glitch_prob = self.audio_modulator.get_glitch_probability()
            if glitch_prob > 0.05:
                self.postfx_processor.config.glitch_enabled = True
                self.postfx_processor.config.glitch_intensity = glitch_prob * 2
            else:
                if not self.chk_glitch.get_active():
                    self.postfx_processor.config.glitch_enabled = False

        if self.postfx_processor.config:
            brightness = self.audio_modulator.get_brightness_multiplier()
            self.postfx_processor.config.brightness_enabled = True
            self.postfx_processor.config.brightness_multiplier = brightness

            r_shift, g_shift, b_shift = self.audio_modulator.get_color_shift()
            if abs(r_shift) > 0.05 or abs(g_shift) > 0.05 or abs(b_shift) > 0.05:
                self.postfx_processor.config.color_shift_enabled = True
                self.postfx_processor.config.color_shift_r = r_shift * 2
                self.postfx_processor.config.color_shift_g = g_shift * 2
                self.postfx_processor.config.color_shift_b = b_shift * 2
            else:
                self.postfx_processor.config.color_shift_enabled = False

    def on_resolution_changed(self, widget):
        if self._block_signals:
            return

        active = widget.get_active()
        preset_names = ['mobile', 'low', 'medium', 'high', 'veryhigh']

        if 0 <= active < len(preset_names):
            preset = QUALITY_PRESETS[preset_names[active]]
            self.spin_width.set_value(preset['width'])
            self.spin_height.set_value(preset['height'])
            self.converter_config['target_width'] = preset['width']
            self.converter_config['target_height'] = preset['height']
            self._update_target_dimensions()
            self._set_status(f"Resolucao: {preset_names[active].title()}")

    def on_luminance_changed(self, widget):
        if self._block_signals:
            return

        active = widget.get_active()
        preset_names = list(LUMINANCE_RAMPS.keys())

        if 0 <= active < len(preset_names):
            preset_id = preset_names[active]
            self.converter_config['luminance_ramp'] = LUMINANCE_RAMPS[preset_id]['ramp']
            self._set_status(f"Luminancia: {LUMINANCE_RAMPS[preset_id]['name']}")
            self._force_rerender()

    def on_preview_terminal_clicked(self, widget):
        self._save_and_open_preview()

    def on_preset_studio_clicked(self, widget):
        self._set_hsv_values(CHROMA_PRESETS['studio'])
        self._set_status("Preset Studio")

    def on_preset_natural_clicked(self, widget):
        self._set_hsv_values(CHROMA_PRESETS['natural'])
        self._set_status("Preset Natural")

    def on_preset_bright_clicked(self, widget):
        self._set_hsv_values(CHROMA_PRESETS['bright'])
        self._set_status("Preset Bright")

    def on_auto_detect_clicked(self, widget):
        if self.current_frame is not None:
            values = self._auto_detect_green(self.current_frame)
            self._set_hsv_values(values)

    def on_reset_clicked(self, widget):
        self._set_hsv_values(DEFAULT_VALUES)
        self._set_status("Valores resetados")

    def on_save_config_clicked(self, widget):
        hsv = self._get_current_hsv_values()

        if 'ChromaKey' not in self.config:
            self.config.add_section('ChromaKey')
        if 'Conversor' not in self.config:
            self.config.add_section('Conversor')
        if 'PixelArt' not in self.config:
            self.config.add_section('PixelArt')
        if 'Mode' not in self.config:
            self.config.add_section('Mode')

        self.config.set('ChromaKey', 'h_min', str(hsv['h_min']))
        self.config.set('ChromaKey', 'h_max', str(hsv['h_max']))
        self.config.set('ChromaKey', 's_min', str(hsv['s_min']))
        self.config.set('ChromaKey', 's_max', str(hsv['s_max']))
        self.config.set('ChromaKey', 'v_min', str(hsv['v_min']))
        self.config.set('ChromaKey', 'v_max', str(hsv['v_max']))
        self.config.set('ChromaKey', 'erode', str(hsv['erode']))
        self.config.set('ChromaKey', 'dilate', str(hsv['dilate']))

        self.config.set('Conversor', 'target_width', str(int(self.spin_width.get_value())))
        self.config.set('Conversor', 'target_height', str(int(self.spin_height.get_value())))
        self.config.set('Conversor', 'sobel_threshold', str(int(self.scale_sobel.get_value())))
        self.config.set('Conversor', 'sharpen_amount', str(self.scale_sharpen.get_value()))
        self.config.set('Conversor', 'sharpen_enabled', str(self.chk_sharpen.get_active()).lower())
        self.config.set('Conversor', 'char_aspect_ratio', str(self.converter_config.get('char_aspect_ratio', 1.0)))

        luminance_ramp = self.converter_config.get('luminance_ramp', LUMINANCE_RAMP_DEFAULT)
        self.config.set('Conversor', 'luminance_ramp', luminance_ramp + '|')

        self.config.set('Conversor', 'luminance_preset', self.converter_config.get('luminance_preset', 'standard'))

        if self.spin_pixel_size:
            self.config.set('PixelArt', 'pixel_size', str(int(self.spin_pixel_size.get_value())))
        if self.spin_palette_size:
            self.config.set('PixelArt', 'color_palette_size', str(int(self.spin_palette_size.get_value())))
        if self.chk_fixed_palette:
            self.config.set('PixelArt', 'use_fixed_palette', str(self.chk_fixed_palette.get_active()).lower())
        if self.combo_fixed_palette:
            palette_id = self.combo_fixed_palette.get_active_id()
            if palette_id:
                self.config.set('PixelArt', 'fixed_palette_name', palette_id)

        self.config.set('Mode', 'conversion_mode', self.conversion_mode)

        render_mode_names = {RENDER_MODE_USER: 'user', RENDER_MODE_BACKGROUND: 'background', RENDER_MODE_BOTH: 'both'}
        self.config.set('Conversor', 'render_mode', render_mode_names.get(self.render_mode, 'user'))

        self.config.set('Conversor', 'braille_enabled', str(self.braille_enabled).lower())
        self.config.set('Conversor', 'braille_threshold', str(self.braille_threshold))
        self.config.set('Conversor', 'temporal_coherence_enabled', str(self.temporal_enabled).lower())
        self.config.set('Conversor', 'temporal_threshold', str(self.temporal_threshold))
        self.config.set('Conversor', 'edge_boost_enabled', str(self.edge_boost_enabled).lower())
        self.config.set('Conversor', 'edge_boost_amount', str(self.edge_boost_amount))
        self.config.set('Conversor', 'use_edge_chars', str(self.use_edge_chars).lower())

        if not self.config.has_section('MatrixRain'):
            self.config.add_section('MatrixRain')
        self.config.set('MatrixRain', 'enabled', str(self.matrix_enabled).lower())
        self.config.set('MatrixRain', 'mode', self.matrix_mode)
        self.config.set('MatrixRain', 'char_set', self.matrix_charset)
        self.config.set('MatrixRain', 'num_particles', str(self.matrix_particles))
        self.config.set('MatrixRain', 'speed_multiplier', str(self.matrix_speed))

        if not self.config.has_section('PostFX'):
            self.config.add_section('PostFX')
        bloom = self.chk_bloom.get_active() if self.chk_bloom else False
        chromatic = self.chk_chromatic.get_active() if self.chk_chromatic else False
        scanlines = self.chk_scanlines.get_active() if self.chk_scanlines else False
        glitch = self.chk_glitch.get_active() if self.chk_glitch else False
        self.config.set('PostFX', 'bloom_enabled', str(bloom).lower())
        self.config.set('PostFX', 'chromatic_enabled', str(chromatic).lower())
        self.config.set('PostFX', 'scanlines_enabled', str(scanlines).lower())
        self.config.set('PostFX', 'glitch_enabled', str(glitch).lower())

        if not self.config.has_section('Style'):
            self.config.add_section('Style')
        style_enabled = self.chk_style.get_active() if self.chk_style else False
        style_preset = self.combo_style_preset.get_active_id() if self.combo_style_preset else 'none'
        self.config.set('Style', 'style_enabled', str(style_enabled).lower())
        self.config.set('Style', 'style_preset', style_preset or 'none')

        if not self.config.has_section('OpticalFlow'):
            self.config.add_section('OpticalFlow')
        of_enabled = self.chk_optical_flow.get_active() if self.chk_optical_flow else False
        of_fps = self.combo_optical_flow_fps.get_active_id() if self.combo_optical_flow_fps else '30'
        of_quality = self.combo_optical_flow_quality.get_active_id() if self.combo_optical_flow_quality else 'medium'
        self.config.set('OpticalFlow', 'enabled', str(of_enabled).lower())
        self.config.set('OpticalFlow', 'target_fps', of_fps or '30')
        self.config.set('OpticalFlow', 'quality', of_quality or 'medium')

        if not self.config.has_section('Audio'):
            self.config.add_section('Audio')
        audio_enabled = self.chk_audio.get_active() if self.chk_audio else False
        bass_sens = self.scale_audio_bass.get_value() if self.scale_audio_bass else 1.0
        mids_sens = self.scale_audio_mids.get_value() if self.scale_audio_mids else 1.0
        treble_sens = self.scale_audio_treble.get_value() if self.scale_audio_treble else 1.0
        self.config.set('Audio', 'enabled', str(audio_enabled).lower())
        self.config.set('Audio', 'bass_sensitivity', str(bass_sens))
        self.config.set('Audio', 'mids_sensitivity', str(mids_sens))
        self.config.set('Audio', 'treble_sensitivity', str(treble_sens))

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.config_last_load = os.path.getmtime(self.config_path)
            self._set_status("Config salvo!")
            GLib.timeout_add(300, self._close_after_save)
        except Exception as e:
            self._set_status(f"Erro: {e}")

    def _close_after_save(self):
        self._cleanup()
        Gtk.main_quit()
        return False

    def on_record_mp4_toggled(self, widget):
        if widget.get_active():
            if self.is_recording_ascii:
                self._set_status("Erro: Ja esta gravando ASCII")
                widget.set_active(False)
                return
            self._start_mp4_recording()
        else:
            self._stop_mp4_recording()

    def on_record_ascii_toggled(self, widget):
        if widget.get_active():
            if self.is_recording_mp4:
                self._set_status("Erro: Ja esta gravando MP4")
                widget.set_active(False)
                return
            self._start_ascii_recording()
        else:
            self._stop_ascii_recording()

    def on_window_destroy(self, widget):
        self._cleanup()
        Gtk.main_quit()

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)

        if keyname in ['q', 'Q', 'Escape']:
            self._cleanup()
            Gtk.main_quit()
            return True

        if keyname == 's':
            self.on_save_config_clicked(None)
            return True

        if keyname == 'r':
            self.on_reset_clicked(None)
            return True

        if keyname == 'a':
            self.on_auto_detect_clicked(None)
            return True

        if keyname == 't':
            self._save_and_open_preview()
            return True

        return False

    def _cleanup(self):
        if self.is_recording_mp4:
            self._stop_mp4_recording()

        if self.is_recording_ascii and len(self.ascii_frames) > 0:
            self._stop_ascii_recording()

        if self.auto_segmenter:
            self.auto_segmenter.close()
            self.auto_segmenter = None

        if hasattr(self, 'matrix_rain') and self.matrix_rain:
            self.matrix_rain = None

        if self.audio_analyzer:
            self._stop_audio_analyzer()

        if self.cap:
            self.cap.release()
            self.cap = None

        self.current_frame = None
        self.current_mask = None

        import gc
        gc.collect()

    def run(self):
        self.window.maximize()
        self.window.show_all()
        self._update_mode_visibility()

        GLib.timeout_add(33, self._update_frame)

        Gtk.main()


def main():
    parser = argparse.ArgumentParser(description="Calibrador GTK de Chroma Key")
    parser.add_argument('--config', required=True, help="Caminho para o config.ini")
    parser.add_argument('--video', required=False, default=None, help="Caminho opcional para um video")
    args = parser.parse_args()

    calibrator = GTKCalibrator(args.config, args.video)
    calibrator.run()


if __name__ == "__main__":
    main()

# "A maior conquista do mundo foi conseguida por gente que nao era inteligente o suficiente para saber que era impossivel." - Thomas Edison
