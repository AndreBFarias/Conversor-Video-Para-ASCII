#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import cv2
import numpy as np
import time
import os
import sys
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR
from src.core.utils.image import sharpen_frame, apply_morphological_refinement

try:
    from src.core.auto_segmenter import AutoSegmenter, is_available as auto_seg_available
    AUTO_SEG_AVAILABLE = auto_seg_available()
except ImportError:
    AUTO_SEG_AVAILABLE = False
    AutoSegmenter = None

try:
    from src.core.matrix_rain_gpu import MatrixRainGPU
    MATRIX_RAIN_AVAILABLE = True
except Exception:
    MATRIX_RAIN_AVAILABLE = False

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except Exception:
    POSTFX_AVAILABLE = False

RENDER_MODE_USER = 0
RENDER_MODE_BACKGROUND = 1
RENDER_MODE_BOTH = 2


class GtkFullscreenPlayer(Gtk.Window):

    def __init__(self, config, title="Extase em 4R73 - Player", start_maximized=True):
        super().__init__(title=title)

        self.config = config
        self.should_close = False

        self.set_wmclass("extase-em-4r73", "Extase em 4R73")
        self.set_position(Gtk.WindowPosition.CENTER)

        if start_maximized:
            self.maximize()
        else:
            self.set_default_size(1280, 720)

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"window { background-color: #000000; }")
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.aspect_frame = Gtk.AspectFrame(
            xalign=0.5, yalign=0.5, ratio=16/9, obey_child=False
        )
        self.image_widget = Gtk.Image()
        self.aspect_frame.add(self.image_widget)
        self.add(self.aspect_frame)

        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", self._on_destroy)

        self._load_conversion_params()

    def _load_conversion_params(self):
        c = self.config
        self.target_width = c.getint('Conversor', 'target_width', fallback=85)
        self.target_height = c.getint('Conversor', 'target_height', fallback=44)
        self.sobel_threshold = c.getint('Conversor', 'sobel_threshold', fallback=10)
        self.luminance_ramp = c.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
        self.sharpen_enabled = c.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        self.sharpen_amount = c.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        self.edge_boost_enabled = c.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
        self.edge_boost_amount = c.getint('Conversor', 'edge_boost_amount', fallback=100)
        self.use_edge_chars = c.getboolean('Conversor', 'use_edge_chars', fallback=True)
        self.char_aspect_ratio = c.getfloat('Conversor', 'char_aspect_ratio', fallback=1.0)

        render_mode_str = c.get('Conversor', 'render_mode', fallback='both').lower()
        self.render_mode = {'user': RENDER_MODE_USER, 'background': RENDER_MODE_BACKGROUND, 'both': RENDER_MODE_BOTH}.get(render_mode_str, RENDER_MODE_BOTH)

        self.auto_seg_enabled = c.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
        self.temporal_enabled = c.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
        self.temporal_threshold = c.getint('Conversor', 'temporal_threshold', fallback=50)

        self.matrix_enabled = c.getboolean('MatrixRain', 'enabled', fallback=False)
        self.matrix_mode = c.get('MatrixRain', 'mode', fallback='user')
        self.matrix_particles = c.getint('MatrixRain', 'num_particles', fallback=5000)
        self.matrix_charset = c.get('MatrixRain', 'char_set', fallback='katakana')
        self.matrix_speed = c.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)

        self.postfx_enabled = False

        if POSTFX_AVAILABLE:
            bloom = c.getboolean('PostFX', 'bloom_enabled', fallback=False)
            chromatic = c.getboolean('PostFX', 'chromatic_enabled', fallback=False)
            scanlines = c.getboolean('PostFX', 'scanlines_enabled', fallback=False)
            glitch = c.getboolean('PostFX', 'glitch_enabled', fallback=False)
            if bloom or chromatic or scanlines or glitch:
                self.postfx_enabled = True

        self._auto_segmenter = None
        self._matrix_rain = None
        self._postfx_processor = None
        self._prev_gray_frame = None
        self._canvas_w = 0
        self._canvas_h = 0

    def _get_canvas_size(self):
        alloc = self.get_allocation()
        if alloc.width > 200 and alloc.height > 200:
            return alloc.width, alloc.height
        screen = Gdk.Screen.get_default()
        return screen.get_width(), screen.get_height()

    def _init_effects(self):
        c = self.config

        if self.auto_seg_enabled and AUTO_SEG_AVAILABLE and not self._auto_segmenter:
            try:
                self._auto_segmenter = AutoSegmenter(threshold=0.5, use_gpu=False)
            except Exception:
                self._auto_segmenter = None

        if self.matrix_enabled and MATRIX_RAIN_AVAILABLE and not self._matrix_rain:
            try:
                self._matrix_rain = MatrixRainGPU(
                    self.target_width, self.target_height,
                    num_particles=self.matrix_particles,
                    char_set=self.matrix_charset,
                    speed_multiplier=self.matrix_speed
                )
            except Exception:
                self._matrix_rain = None

        if self.postfx_enabled and POSTFX_AVAILABLE and not self._postfx_processor:
            try:
                pconfig = PostFXConfig(
                    bloom_enabled=c.getboolean('PostFX', 'bloom_enabled', fallback=False),
                    bloom_intensity=c.getfloat('PostFX', 'bloom_intensity', fallback=1.2),
                    bloom_radius=c.getint('PostFX', 'bloom_radius', fallback=21),
                    bloom_threshold=c.getint('PostFX', 'bloom_threshold', fallback=80),
                    chromatic_enabled=c.getboolean('PostFX', 'chromatic_enabled', fallback=False),
                    chromatic_shift=c.getint('PostFX', 'chromatic_shift', fallback=12),
                    scanlines_enabled=c.getboolean('PostFX', 'scanlines_enabled', fallback=False),
                    scanlines_intensity=c.getfloat('PostFX', 'scanlines_intensity', fallback=0.7),
                    scanlines_spacing=c.getint('PostFX', 'scanlines_spacing', fallback=2),
                    glitch_enabled=c.getboolean('PostFX', 'glitch_enabled', fallback=False),
                    glitch_intensity=c.getfloat('PostFX', 'glitch_intensity', fallback=0.6),
                    glitch_block_size=c.getint('PostFX', 'glitch_block_size', fallback=8),
                )
                self._postfx_processor = PostFXProcessor(pconfig, use_gpu=False)
            except Exception:
                self._postfx_processor = None

    def render_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        if self.sharpen_enabled:
            frame_bgr = sharpen_frame(frame_bgr, self.sharpen_amount)

        mask = self._compute_mask(frame_bgr)

        target_dims = (self.target_width, self.target_height)
        grayscale = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        resized_gray = cv2.resize(grayscale, target_dims, interpolation=cv2.INTER_AREA)
        resized_color = cv2.resize(frame_bgr, target_dims, interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(mask, target_dims, interpolation=cv2.INTER_NEAREST)

        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        if self.temporal_enabled and self._prev_gray_frame is not None:
            diff = np.abs(resized_gray.astype(np.int32) - self._prev_gray_frame.astype(np.int32))
            temporal_mask = diff < self.temporal_threshold
            resized_gray = np.where(temporal_mask, self._prev_gray_frame, resized_gray).astype(np.uint8)
        self._prev_gray_frame = resized_gray.copy()

        canvas_w, canvas_h = self._get_canvas_size()
        self._canvas_w = canvas_w
        self._canvas_h = canvas_h

        self._init_effects()

        result_image = self._render_ascii_to_image(
            resized_gray, resized_color, resized_mask,
            magnitude_norm, angle, canvas_h, canvas_w
        )

        if self._matrix_rain and self.matrix_enabled:
            result_image = self._apply_matrix_rain(result_image, resized_mask)

        if self._postfx_processor and self.postfx_enabled:
            result_image = self._postfx_processor.process(result_image)

        return result_image

    def _compute_mask(self, frame_bgr: np.ndarray) -> np.ndarray:
        frame_h, frame_w = frame_bgr.shape[:2]

        if self._auto_segmenter:
            try:
                max_size = 320
                if max(frame_h, frame_w) > max_size:
                    scale = max_size / max(frame_h, frame_w)
                    small = cv2.resize(frame_bgr, (int(frame_w * scale), int(frame_h * scale)))
                    small_mask = self._auto_segmenter.process(small)
                    return cv2.resize(small_mask, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)
                return self._auto_segmenter.process(frame_bgr)
            except Exception:
                pass

        c = self.config
        h_min = c.getint('ChromaKey', 'h_min', fallback=35)
        h_max = c.getint('ChromaKey', 'h_max', fallback=85)
        s_min = c.getint('ChromaKey', 's_min', fallback=40)
        s_max = c.getint('ChromaKey', 's_max', fallback=255)
        v_min = c.getint('ChromaKey', 'v_min', fallback=40)
        v_max = c.getint('ChromaKey', 'v_max', fallback=255)
        erode = c.getint('ChromaKey', 'erode', fallback=2)
        dilate = c.getint('ChromaKey', 'dilate', fallback=2)

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max]))
        return apply_morphological_refinement(mask, erode, dilate)

    def _apply_matrix_rain(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        try:
            self._matrix_rain.update(dt=0.05)

            w, h = self.target_width, self.target_height
            canvas_char = np.full((h, w), ord(' '), dtype=np.uint16)
            canvas_color = np.zeros((h, w, 3), dtype=np.uint8)

            self._matrix_rain.render(canvas_char, canvas_color)

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
                        cv2.putText(result, char, (px, py),
                                    cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                    color, 1, cv2.LINE_AA)

            return result
        except Exception:
            return image

    def _render_ascii_to_image(self, resized_gray, resized_color, resized_mask,
                                magnitude_norm, angle, canvas_h, canvas_w) -> np.ndarray:
        height, width = resized_gray.shape

        if height <= 0 or width <= 0 or canvas_h <= 0 or canvas_w <= 0:
            return np.zeros((max(1, canvas_h), max(1, canvas_w), 3), dtype=np.uint8)

        ascii_image = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        char_w_base = 8
        char_h_base = 16

        scale_x = canvas_w / (width * char_w_base)
        scale_y = canvas_h / (height * char_h_base)
        scale = min(scale_x, scale_y)

        char_w = max(1, int(char_w_base * scale))
        char_h = max(1, int(char_h_base * scale))

        total_w = width * char_w
        total_h = height * char_h

        offset_x = (canvas_w - total_w) // 2
        offset_y = (canvas_h - total_h) // 2

        font_scale = max(0.25, 0.35 * scale)

        luminance_ramp = self.luminance_ramp
        ramp_len = len(luminance_ramp)
        sobel_threshold = self.sobel_threshold

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
                    idx = min(max(lum_indices[y, x], 0), ramp_len - 1)
                    char = luminance_ramp[idx]

                b, g, r = resized_color[y, x]
                px = offset_x + x * char_w
                rect_y = offset_y + y * char_h

                if char.strip():
                    cv2.putText(ascii_image, char, (px, py),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                (int(b), int(g), int(r)), 1)
                else:
                    cv2.rectangle(ascii_image, (px, rect_y),
                                  (px + char_w, rect_y + char_h),
                                  (int(b), int(g), int(r)), -1)

        return ascii_image

    def display_frame(self, result_image: np.ndarray):
        if result_image is None or result_image.size == 0:
            return

        h, w = result_image.shape[:2]
        self.aspect_frame.set_property("ratio", w / h)

        rgb = result_image[:, :, ::-1].copy()
        if not rgb.flags['C_CONTIGUOUS']:
            rgb = np.ascontiguousarray(rgb)

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            rgb.tobytes(), GdkPixbuf.Colorspace.RGB,
            False, 8, w, h, w * 3, None, None
        )

        alloc = self.image_widget.get_allocation()
        if alloc.width > 1 and alloc.height > 1:
            if alloc.width != w or alloc.height != h:
                pixbuf = pixbuf.scale_simple(alloc.width, alloc.height, GdkPixbuf.InterpType.BILINEAR)

        self.image_widget.set_from_pixbuf(pixbuf)

    def process_events(self):
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ['q', 'Q', 'Escape']:
            self.should_close = True
            self.destroy()
            return True
        return False

    def _on_destroy(self, widget):
        self.should_close = True
        self.cleanup()

    def cleanup(self):
        if self._auto_segmenter:
            try:
                self._auto_segmenter.close()
            except Exception:
                pass
        self._matrix_rain = None
        self._postfx_processor = None


def play_file_gtk(arquivo_path: str, config, loop: bool = False):
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' nao encontrado.")

    with open(arquivo_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('\n', 1)
    if len(parts) < 2:
        raise ValueError("Formato de arquivo invalido.")

    fps = float(parts[0].strip())
    frame_content = parts[1]
    if frame_content.startswith("[FRAME]\n"):
        frame_content = frame_content[len("[FRAME]\n"):]
    frames = frame_content.split("[FRAME]\n")

    if not frames or all(not f.strip() for f in frames):
        raise ValueError("Nenhum frame valido encontrado.")

    from src.core.renderer import render_ascii_as_image

    window = GtkFullscreenPlayer(config, title="Extase em 4R73 - Player")
    window.show_all()

    for _ in range(5):
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(0.05)

    is_static = (fps == 0)
    delay = 1.0 / fps if fps > 0 else 0

    window._init_effects()

    def _apply_file_effects(img):
        if img is None:
            return img
        if window._matrix_rain and window.matrix_enabled:
            dummy_mask = np.zeros(
                (window.target_height, window.target_width), dtype=np.uint8
            )
            img = window._apply_matrix_rain(img, dummy_mask)
        if window._postfx_processor and window.postfx_enabled:
            img = window._postfx_processor.process(img)
        return img

    try:
        if is_static:
            img = render_ascii_as_image(frames[0])
            img = _apply_file_effects(img)
            if img is not None:
                window.display_frame(img)
            Gtk.main()
        else:
            while not window.should_close:
                for frame_data in frames:
                    if window.should_close or not frame_data.strip():
                        break

                    img = render_ascii_as_image(frame_data)
                    img = _apply_file_effects(img)
                    if img is not None:
                        window.display_frame(img)

                    window.process_events()
                    if window.should_close:
                        break

                    time.sleep(delay)

                if not loop:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        window.cleanup()


def play_realtime_gtk(config, video_path: str = None):
    capture_source = video_path if video_path else 0
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        source_name = video_path if video_path else "webcam"
        raise IOError(f"Nao foi possivel abrir: {source_name}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    is_video = video_path is not None

    window = GtkFullscreenPlayer(config, title="Extase em 4R73 - Real-Time")
    window.show_all()

    for _ in range(5):
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(0.05)

    try:
        while not window.should_close:
            ret, frame = cap.read()
            if not ret:
                if is_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            if not is_video:
                frame = cv2.flip(frame, 1)

            result = window.render_frame(frame)
            window.display_frame(result)
            window.process_events()

            if window.should_close:
                break

            time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        window.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GTK Fullscreen ASCII Player")
    parser.add_argument("--config", required=True, help="Caminho para config.ini")
    parser.add_argument("--file", default=None, help="Arquivo .txt ASCII para reproduzir")
    parser.add_argument("--video", default=None, help="Arquivo de video para real-time")
    parser.add_argument("--loop", action="store_true", help="Loop na reproducao")
    args = parser.parse_args()

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    if args.file:
        play_file_gtk(args.file, config, args.loop)
    else:
        play_realtime_gtk(config, args.video)

# "A forma segue a funcao." - Louis Sullivan
