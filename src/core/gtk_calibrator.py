#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

import cv2
import numpy as np
import configparser
import argparse
import sys
import os
import time
import subprocess
import signal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR
from src.core.pixel_art_converter import quantize_colors
from src.app.constants import LUMINANCE_RAMPS, FIXED_PALETTES


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

        self._reload_converter_config()
        self._reload_pixel_art_config()

        self.conversion_mode = self.config.get('Mode', 'conversion_mode', fallback=MODE_ASCII)

    def _reload_converter_config(self):
        try:
            self.converter_config = {
                'target_width': self.config.getint('Conversor', 'target_width', fallback=80),
                'target_height': self.config.getint('Conversor', 'target_height', fallback=22),
                'char_aspect_ratio': self.config.getfloat('Conversor', 'char_aspect_ratio', fallback=1.0),
                'sobel_threshold': self.config.getint('Conversor', 'sobel_threshold', fallback=20),
                'luminance_ramp': self.config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT),
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

    def _init_capture(self):
        capture_source = self.video_path if self.is_video_file else 0
        self.cap = cv2.VideoCapture(capture_source)

        if not self.cap.isOpened():
            print(f"Erro: Nao foi possivel abrir fonte de video: {capture_source}", file=sys.stderr)
            sys.exit(1)

        self.recording_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if h > 0:
            self.source_aspect_ratio = w / h

        self._update_target_dimensions()

    def _update_target_dimensions(self):
        w = self.converter_config['target_width']
        h = self.converter_config['target_height']
        self.target_dimensions = (w, h)

    def _init_ui(self):
        glade_path = os.path.join(BASE_DIR, "src", "gui", "calibrator.glade")

        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_path)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("calibrator_window")

        self.window.set_wmclass("extase-em-4r73", "Extase em 4R73")

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

        for aspect in [self.aspect_original, self.aspect_chroma, self.aspect_ascii]:
            if aspect:
                aspect.set_size_request(200, 150)

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

        self.event_ascii = self.builder.get_object("event_ascii")
        if self.event_ascii:
            self.event_ascii.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.event_ascii.connect("button-press-event", self._on_ascii_button_press)

    def _on_ascii_button_press(self, widget, event):
        if event.button == 1:
            current_time = time.time()
            if current_time - self._last_click_time < 0.4:
                if self.is_video_file:
                    self._open_terminal_preview()
                else:
                    self._set_status("Preview indisponivel: webcam em uso")
                self._last_click_time = 0.0
                return True
            self._last_click_time = current_time
        return False

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
            self.combo_render_mode.set_active(0)

        if self.radio_ascii and self.radio_pixelart:
            if self.conversion_mode == MODE_PIXELART:
                self.radio_pixelart.set_active(True)
            else:
                self.radio_ascii.set_active(True)
            self._update_mode_visibility()

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
            target_w = max(alloc.width - 8, 200)
            target_h = max(alloc.height - 8, 150)

            scale_w = target_w / w
            scale_h = target_h / h
            scale = min(scale_w, scale_h)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

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

    def _render_ascii_to_image(self, resized_gray, resized_color, resized_mask, magnitude_norm, angle, frame_h, frame_w) -> np.ndarray:
        height, width = resized_gray.shape

        ascii_image = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)

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

                if mag > sobel_threshold:
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
                cv2.putText(ascii_image, char, (px, py), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (int(b), int(g), int(r)), 1)

        return ascii_image

    def _render_pixelart_to_image(self, resized_color, resized_mask, frame_h, frame_w) -> np.ndarray:
        n_colors = self.pixel_art_config.get('color_palette_size', 16)
        use_fixed = self.pixel_art_config.get('use_fixed_palette', False)

        height, width = resized_color.shape[:2]

        try:
            quantized = quantize_colors(resized_color, n_colors, use_fixed_palette=use_fixed)
        except Exception:
            quantized = resized_color

        block_w = max(1, frame_w // width)
        block_h = max(1, frame_h // height)

        pixel_image = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)

        for y in range(height):
            for x in range(width):
                if resized_mask[y, x] > 127:
                    if self.render_mode == RENDER_MODE_USER:
                        continue
                else:
                    if self.render_mode == RENDER_MODE_BACKGROUND:
                        continue

                b, g, r = quantized[y, x]
                y1 = y * block_h
                y2 = min((y + 1) * block_h, frame_h)
                x1 = x * block_w
                x2 = min((x + 1) * block_w, frame_w)

                pixel_image[y1:y2, x1:x2] = [int(b), int(g), int(r)]

        return pixel_image

    def _set_status(self, text: str):
        if self.lbl_status:
            prefix = ""
            if self.is_recording_mp4:
                prefix += "[REC MP4] "
            if self.is_recording_ascii:
                prefix += f"[REC: {len(self.ascii_frames)}] "

            self.lbl_status.set_text(prefix + text if prefix else f"Status: {text}")

    def _update_frame(self) -> bool:
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

        self.current_frame = frame.copy()

        frame_h, frame_w = frame.shape[:2]
        self.source_aspect_ratio = frame_w / frame_h

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

        self._frame_counter += 1
        if self._frame_counter % 2 == 0:
            grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized_gray = cv2.resize(grayscale, self.target_dimensions, interpolation=cv2.INTER_AREA)
            resized_color = cv2.resize(frame, self.target_dimensions, interpolation=cv2.INTER_AREA)
            resized_mask = cv2.resize(mask, self.target_dimensions, interpolation=cv2.INTER_NEAREST)

            sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.hypot(sobel_x, sobel_y)
            angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
            angle = (angle + 180) % 180
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            if self.conversion_mode == MODE_PIXELART:
                result_image = self._render_pixelart_to_image(resized_color, resized_mask, frame_h, frame_w)
            else:
                result_image = self._render_ascii_to_image(resized_gray, resized_color, resized_mask, magnitude_norm, angle, frame_h, frame_w)

            self._set_frame_to_image(self.image_ascii, self.aspect_ascii, result_image)

            self._cached_ascii_data = (resized_gray, resized_color, resized_mask, magnitude_norm, angle)

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
                output_format="file"
            )
            self.ascii_frames.append(frame_for_file)

        return True

    def _start_mp4_recording(self):
        if self.is_recording_mp4:
            return

        output_dir = self.config.get('Pastas', 'output_dir', fallback='data_output')
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(BASE_DIR, output_dir)
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.mp4_output_file = os.path.join(output_dir, f"screencast_{timestamp}.mp4")

        display = os.environ.get('DISPLAY', ':0')

        cmd = [
            'ffmpeg', '-y',
            '-f', 'x11grab', '-framerate', '30', '-i', display,
            '-f', 'pulse', '-i', 'default',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            self.mp4_output_file
        ]

        try:
            self.mp4_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.is_recording_mp4 = True
            self._set_status("Gravacao MP4 iniciada")
        except Exception as e:
            self._set_status(f"Erro ffmpeg: {e}")
            self.is_recording_mp4 = False

    def _stop_mp4_recording(self):
        if not self.is_recording_mp4 or not self.mp4_process:
            return

        try:
            self.mp4_process.send_signal(signal.SIGINT)
            self.mp4_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.mp4_process.kill()
        except Exception:
            pass

        self.is_recording_mp4 = False
        self.mp4_process = None
        self._set_status(f"MP4 salvo: {os.path.basename(self.mp4_output_file)}")

    def _start_ascii_recording(self):
        if self.is_recording_ascii:
            return
        self.ascii_frames = []
        self.is_recording_ascii = True
        self._set_status("Gravacao ASCII iniciada")

    def _stop_ascii_recording(self):
        if not self.is_recording_ascii:
            return

        self.is_recording_ascii = False

        if len(self.ascii_frames) == 0:
            self._set_status("Nenhum frame gravado")
            return

        output_dir = self.config.get('Pastas', 'output_dir', fallback='data_output')
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(BASE_DIR, output_dir)
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"gravacao_{timestamp}.txt")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{self.recording_fps}\n")
                f.write("[FRAME]\n".join(self.ascii_frames))

            self._set_status(f"ASCII salvo: {os.path.basename(output_file)} ({len(self.ascii_frames)} frames)")
        except Exception as e:
            self._set_status(f"Erro: {e}")

        self.ascii_frames = []

    def _open_terminal_preview(self):
        realtime_script = os.path.join(BASE_DIR, "src", "core", "realtime_ascii.py")
        python_exec = sys.executable
        cmd_base = [python_exec, realtime_script, "--config", self.config_path]
        title = "Extase em 4R73 - Preview"

        if self.video_path:
            cmd_base.extend(["--video", self.video_path])

        try:
            cmd = ['kitty', '--class=extase-em-4r73', f'--title={title}',
                   '-o', 'font_size=10', '--start-as=maximized', '--'] + cmd_base
            subprocess.Popen(cmd)
            self._set_status("Terminal preview aberto")
        except FileNotFoundError:
            try:
                cmd = ['gnome-terminal', '--maximize', f'--title={title}',
                       '--class=extase-em-4r73', '--'] + cmd_base
                subprocess.Popen(cmd)
                self._set_status("Terminal preview aberto")
            except FileNotFoundError:
                try:
                    cmd = ['xterm', '-maximized', '-title', title, '-e'] + cmd_base
                    subprocess.Popen(cmd)
                    self._set_status("Terminal preview aberto (xterm)")
                except Exception as e:
                    self._set_status(f"Erro terminal: {e}")
            except Exception as e:
                self._set_status(f"Erro terminal: {e}")
        except Exception as e:
            self._set_status(f"Erro terminal: {e}")

    def on_hsv_changed(self, widget):
        pass

    def on_ascii_config_changed(self, widget):
        if self._block_signals:
            return

        self.converter_config['target_width'] = int(self.spin_width.get_value())
        self.converter_config['target_height'] = int(self.spin_height.get_value())
        self.converter_config['sobel_threshold'] = int(self.scale_sobel.get_value())
        self.converter_config['sharpen_amount'] = self.scale_sharpen.get_value()
        self.converter_config['sharpen_enabled'] = self.chk_sharpen.get_active()

        self._update_target_dimensions()

    def on_pixel_art_changed(self, widget):
        if self._block_signals:
            return

        if self.spin_pixel_size:
            self.pixel_art_config['pixel_size'] = int(self.spin_pixel_size.get_value())
        if self.spin_palette_size:
            self.pixel_art_config['color_palette_size'] = int(self.spin_palette_size.get_value())

    def on_fixed_palette_toggled(self, widget):
        if self._block_signals:
            return

        use_fixed = widget.get_active()
        self.pixel_art_config['use_fixed_palette'] = use_fixed

        if self.combo_fixed_palette:
            self.combo_fixed_palette.set_sensitive(use_fixed)

        self._set_status(f"Paleta fixa: {'Ativada' if use_fixed else 'Desativada'}")

    def on_fixed_palette_changed(self, widget):
        if self._block_signals:
            return

        palette_id = widget.get_active_id()
        if palette_id and palette_id in FIXED_PALETTES:
            self.pixel_art_config['fixed_palette_name'] = palette_id
            self._set_status(f"Paleta: {FIXED_PALETTES[palette_id]['name']}")

    def on_ramp_preset_changed(self, widget):
        if self._block_signals:
            return

        preset_id = widget.get_active_id()
        if preset_id and preset_id in LUMINANCE_RAMPS:
            self.converter_config['luminance_ramp'] = LUMINANCE_RAMPS[preset_id]['ramp']
            self._set_status(f"Rampa: {LUMINANCE_RAMPS[preset_id]['name']}")

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
            self._set_status("Render: Background (fundo)")
        else:
            self.render_mode = RENDER_MODE_BOTH
            self._set_status("Render: Ambos")

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

    def on_preview_terminal_clicked(self, widget):
        if self.is_video_file:
            self._open_terminal_preview()
        else:
            self._set_status("Preview indisponivel: webcam em uso")

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
        self.config.set('Conversor', 'luminance_ramp', self.converter_config.get('luminance_ramp', LUMINANCE_RAMP_DEFAULT))

        if self.spin_pixel_size:
            self.config.set('PixelArt', 'pixel_size', str(int(self.spin_pixel_size.get_value())))
        if self.spin_palette_size:
            self.config.set('PixelArt', 'color_palette_size', str(int(self.spin_palette_size.get_value())))
        if self.chk_fixed_palette:
            self.config.set('PixelArt', 'use_fixed_palette', str(self.chk_fixed_palette.get_active()).lower())

        self.config.set('Mode', 'conversion_mode', self.conversion_mode)

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self._set_status("Config salvo!")
        except Exception as e:
            self._set_status(f"Erro: {e}")

    def on_record_mp4_toggled(self, widget):
        if widget.get_active():
            self._start_mp4_recording()
        else:
            self._stop_mp4_recording()

    def on_record_ascii_toggled(self, widget):
        if widget.get_active():
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
            if self.is_video_file:
                self._open_terminal_preview()
            else:
                self._set_status("Preview indisponivel: webcam em uso")
            return True

        return False

    def _cleanup(self):
        if self.is_recording_mp4:
            self._stop_mp4_recording()

        if self.is_recording_ascii and len(self.ascii_frames) > 0:
            self._stop_ascii_recording()

        if self.cap:
            self.cap.release()

    def run(self):
        self.window.maximize()
        self.window.show_all()
        self._update_mode_visibility()

        GLib.timeout_add(50, self._update_frame)

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
