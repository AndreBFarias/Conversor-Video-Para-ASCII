import os
import cv2
import numpy as np
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf

from src.core.utils.ascii_converter import LUMINANCE_RAMP_DEFAULT
from src.core.utils.image import sharpen_frame, apply_morphological_refinement


class PreviewActionsMixin:

    def _init_preview(self):
        self._preview_active = False
        self._preview_config_mtime = 0
        self._preview_thread = None

    def on_preview_button_toggled(self, widget):
        if not hasattr(self, 'preview_frame') or not self.preview_frame:
            return

        self._preview_active = widget.get_active()

        if self._preview_active:
            self._refresh_preview()
        else:
            self.preview_frame.set_visible(False)
            self.window.set_size_request(-1, -1)
            self.window.resize(1, 1)

    def _refresh_preview(self):
        if not self._preview_active:
            return

        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            return

        if self._preview_thread and self._preview_thread.is_alive():
            return

        self._preview_thread = threading.Thread(
            target=self._generate_preview_frame,
            daemon=True
        )
        self._preview_thread.start()

    def _generate_preview_frame(self):
        try:
            file_path = self.selected_file_path
            if not file_path or not os.path.exists(file_path):
                return

            from ..constants import VIDEO_EXTENSIONS, IMAGE_EXTENSIONS

            if file_path.lower().endswith(IMAGE_EXTENSIONS):
                frame = cv2.imread(file_path)
            elif file_path.lower().endswith(VIDEO_EXTENSIONS):
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    return
                ret, frame = cap.read()
                cap.release()
                if not ret or frame is None:
                    return
            else:
                return

            result_image = self._render_preview_frame(frame)

            if result_image is not None:
                GLib.idle_add(self._display_static_preview, result_image)

        except Exception as e:
            self.logger.error(f"Erro ao gerar preview: {e}")

    def _render_preview_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        self.reload_config()
        c = self.config

        target_width = c.getint('Conversor', 'target_width', fallback=85)
        target_height = c.getint('Conversor', 'target_height', fallback=44)
        sobel_threshold = c.getint('Conversor', 'sobel_threshold', fallback=10)
        luminance_ramp = c.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
        sharpen_enabled = c.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = c.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        edge_boost_enabled = c.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
        edge_boost_amount = c.getint('Conversor', 'edge_boost_amount', fallback=100)
        use_edge_chars = c.getboolean('Conversor', 'use_edge_chars', fallback=True)

        render_mode_str = c.get('Conversor', 'render_mode', fallback='both').lower()
        RENDER_MODE_USER = 0
        RENDER_MODE_BACKGROUND = 1
        render_mode = {'user': 0, 'background': 1, 'both': 2}.get(render_mode_str, 2)

        if sharpen_enabled:
            frame_bgr = sharpen_frame(frame_bgr, sharpen_amount)

        h_min = c.getint('ChromaKey', 'h_min', fallback=35)
        h_max = c.getint('ChromaKey', 'h_max', fallback=85)
        s_min = c.getint('ChromaKey', 's_min', fallback=40)
        s_max = c.getint('ChromaKey', 's_max', fallback=255)
        v_min = c.getint('ChromaKey', 'v_min', fallback=40)
        v_max = c.getint('ChromaKey', 'v_max', fallback=255)
        erode = c.getint('ChromaKey', 'erode', fallback=2)
        dilate_val = c.getint('ChromaKey', 'dilate', fallback=2)

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv,
                           np.array([h_min, s_min, v_min]),
                           np.array([h_max, s_max, v_max]))
        mask = apply_morphological_refinement(mask, erode, dilate_val)

        target_dims = (target_width, target_height)
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

        canvas_w = 640
        canvas_h = 480
        ascii_image = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        height, width = resized_gray.shape
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
        ramp_len = len(luminance_ramp)

        is_edge = magnitude_norm > sobel_threshold

        if edge_boost_enabled:
            brightness = resized_gray.astype(np.int32)
            edge_boost = is_edge.astype(np.int32) * edge_boost_amount
            brightness = np.clip(brightness + edge_boost, 0, 255)
            lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
        else:
            lum_indices = (resized_gray * (ramp_len - 1) / 255).astype(np.int32)

        for y in range(height):
            py = offset_y + y * char_h + char_h - 3
            for x in range(width):
                is_chroma = resized_mask[y, x] > 127
                if render_mode == RENDER_MODE_USER and is_chroma:
                    continue
                elif render_mode == RENDER_MODE_BACKGROUND and not is_chroma:
                    continue

                mag = magnitude_norm[y, x]
                ang = angle[y, x]

                if use_edge_chars and mag > sobel_threshold:
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
                    cv2.putText(ascii_image, char, (px, py),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                (int(b), int(g), int(r)), 1)
                else:
                    cv2.rectangle(ascii_image, (px, rect_y),
                                  (px + char_w, rect_y + char_h),
                                  (int(b), int(g), int(r)), -1)

        return ascii_image

    def _display_static_preview(self, bgr_image: np.ndarray):
        if not hasattr(self, 'preview_thumbnail') or not self.preview_thumbnail:
            return False
        if not hasattr(self, 'preview_frame') or not self.preview_frame:
            return False

        try:
            h, w = bgr_image.shape[:2]

            max_width = 400
            if w > max_width:
                scale = max_width / w
                new_w = max_width
                new_h = int(h * scale)
                bgr_image = cv2.resize(bgr_image, (new_w, new_h))
                h, w = new_h, new_w

            rgb = bgr_image[:, :, ::-1].copy()
            rgb = np.ascontiguousarray(rgb)

            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                GLib.Bytes.new(rgb.tobytes()),
                GdkPixbuf.Colorspace.RGB,
                False, 8, w, h, w * 3
            )

            self.preview_thumbnail.set_from_pixbuf(pixbuf)
            self.preview_thumbnail.set_visible(True)
            self.preview_frame.set_visible(True)

        except Exception as e:
            self.logger.error(f"Erro ao exibir preview: {e}")

        return False

    def _start_config_watcher(self):
        self._preview_config_mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
        GLib.timeout_add(2000, self._check_config_and_refresh)

    def _check_config_and_refresh(self) -> bool:
        try:
            if not self._preview_active:
                return True

            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._preview_config_mtime:
                self._preview_config_mtime = current_mtime
                self.reload_config()
                self._refresh_preview()
                self.logger.info("Config mudou, preview atualizado")
        except Exception:
            pass

        return True
