import logging
import math
import time

import numpy as np
from rich.style import Style
from rich.text import Text
from textual.widgets import Static

import config

logger = logging.getLogger(__name__)

TARGET_FPS = config.UI_CONFIG.get("VIZ_FPS", 24)
MIN_FRAME_INTERVAL = 1.0 / TARGET_FPS


class AudioVisualizer(Static):
    GRADIENT_COLORS = [
        (98, 114, 164),
        (108, 118, 180),
        (139, 92, 246),
        (167, 139, 250),
        (189, 147, 249),
        (200, 160, 255),
        (255, 121, 198),
        (255, 149, 212),
        (255, 184, 108),
        (255, 149, 212),
        (255, 121, 198),
        (200, 160, 255),
        (189, 147, 249),
        (167, 139, 250),
        (139, 92, 246),
        (108, 118, 180),
        (98, 114, 164),
    ]

    BG_COLOR = "#282a36"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.num_bands = 8
        self.smoothed_energies = [0.0] * self.num_bands
        self.smoothed_rms = 0.0
        self.peak_rms = 0.0
        self.time_offset = 0.0
        self.last_update = time.time()
        self._busy = False

    def update_audio(self, audio_chunk: np.ndarray, rate: int):
        if self._busy:
            return

        current_time = time.time()
        elapsed = current_time - self.last_update
        if elapsed < MIN_FRAME_INTERVAL:
            return

        self._busy = True
        try:
            if audio_chunk is None or len(audio_chunk) < 64:
                return

            data = audio_chunk.astype(np.float32) / 32768.0
            rms_val = float(np.sqrt(np.mean(data**2)))

            self.peak_rms = max(self.peak_rms * 0.995, rms_val)
            normalized_rms = rms_val / max(self.peak_rms, 0.001)
            self.smoothed_rms = self.smoothed_rms * 0.7 + normalized_rms * 0.3

            n = len(data)
            window = np.hanning(n)
            fft_data = np.fft.rfft(data * window)
            magnitude = np.abs(fft_data)

            n_bins = len(magnitude)
            if n_bins < 10:
                return

            edges = np.linspace(0, n_bins, self.num_bands + 1, dtype=int)

            new_energies = []
            for i in range(self.num_bands):
                start, end = edges[i], edges[i + 1]
                if end > start:
                    new_energies.append(float(np.mean(magnitude[start:end])))
                else:
                    new_energies.append(0.0)

            max_e = max(new_energies) if new_energies else 1.0
            if max_e > 0:
                new_energies = [e / max_e for e in new_energies]

            for i in range(self.num_bands):
                self.smoothed_energies[i] = self.smoothed_energies[i] * 0.6 + new_energies[i] * 0.4

            self._render_wave()
        except Exception as e:
            logger.debug(f"Visualizer skip: {e}")
        finally:
            self._busy = False

    def _wave_function(self, x: float, t: float, width: float) -> float:
        nx = x / width

        low = self.smoothed_energies[0] if len(self.smoothed_energies) > 0 else 0
        mid_low = self.smoothed_energies[2] if len(self.smoothed_energies) > 2 else 0
        mid = self.smoothed_energies[4] if len(self.smoothed_energies) > 4 else 0
        high = self.smoothed_energies[6] if len(self.smoothed_energies) > 6 else 0

        w1 = math.sin(nx * 8.0 - t * 2.0) * 0.3 * (1.0 + low * 2.0)
        w2 = math.sin(nx * 14.0 - t * 2.5) * 0.2 * (1.0 + mid_low * 1.5)
        w3 = math.sin(nx * 20.0 - t * 1.8) * 0.15 * (1.0 + mid * 1.2)
        w4 = math.sin(nx * 28.0 - t * 3.0) * 0.1 * (1.0 + high * 1.0)

        return w1 + w2 + w3 + w4

    def _render_wave(self):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        self.time_offset += dt * 4.0

        w, h = self.size.width, self.size.height
        if w <= 0 or h <= 0:
            return

        canvas = self._create_silk_wave(w, h)
        self.update(canvas)

    def _create_silk_wave(self, width: int, height: int) -> Text:
        t = self.time_offset
        center_y = height / 2.0

        base_thickness = 0.1
        audio_thickness = self.smoothed_rms * 0.8
        thickness = base_thickness + audio_thickness

        wave_heights = []

        for x in range(width):
            wave_val = self._wave_function(x, t, width)
            amplitude_at_x = self.smoothed_rms * 2.0 + 0.3
            y_center = center_y + wave_val * (height * 0.35) * amplitude_at_x
            half_thickness = thickness * (0.5 + abs(wave_val) * 0.3)
            y_top = y_center - half_thickness
            y_bottom = y_center + half_thickness
            wave_heights.append((y_top, y_bottom, y_center))

        canvas = []
        for y in range(height):
            row = []
            for x in range(width):
                y_top, y_bottom, y_center = wave_heights[x]
                char, color = self._get_pixel(x, y, y_top, y_bottom, y_center, width, height, t)
                row.append((char, color))
            canvas.append(row)

        return self._canvas_to_rich_text(canvas, height)

    def _get_pixel(
        self, x: int, y: int, y_top: float, y_bottom: float, y_center: float, width: int, height: int, t: float
    ) -> tuple[str, str]:
        wave_thickness = y_bottom - y_top
        glow_range = max(1.5, wave_thickness * 1.2)

        if y_top <= y <= y_bottom:
            dist_from_center = abs(y - y_center)
            half_thickness = wave_thickness / 2.0
            if half_thickness > 0:
                core_intensity = 1.0 - (dist_from_center / half_thickness) * 0.15
            else:
                core_intensity = 1.0
            intensity = max(0.85, min(1.0, core_intensity))
        elif y < y_top:
            dist = y_top - y
            if dist < glow_range:
                intensity = 0.6 * (1.0 - dist / glow_range) ** 1.5
            else:
                intensity = 0.0
        else:
            dist = y - y_bottom
            if dist < glow_range:
                intensity = 0.6 * (1.0 - dist / glow_range) ** 1.5
            else:
                intensity = 0.0

        if intensity < 0.02:
            return " ", self.BG_COLOR

        color_pos = (x / width - t * 0.08) % 1.0
        color = self._interpolate_gradient(color_pos, intensity)

        if intensity > 0.9:
            char = "━"
        elif intensity > 0.7:
            char = "─"
        elif intensity > 0.4:
            char = "╌"
        elif intensity > 0.2:
            char = "·"
        else:
            char = " "

        return char, color

    def _interpolate_gradient(self, position: float, intensity: float) -> str:
        idx_float = position * (len(self.GRADIENT_COLORS) - 1)
        idx1 = int(idx_float)
        idx2 = min(idx1 + 1, len(self.GRADIENT_COLORS) - 1)
        blend = idx_float - idx1

        c1 = self.GRADIENT_COLORS[idx1]
        c2 = self.GRADIENT_COLORS[idx2]

        r = int(c1[0] + (c2[0] - c1[0]) * blend)
        g = int(c1[1] + (c2[1] - c1[1]) * blend)
        b = int(c1[2] + (c2[2] - c1[2]) * blend)

        brightness = 0.4 + intensity * 0.6
        r = min(255, int(r * brightness))
        g = min(255, int(g * brightness))
        b = min(255, int(b * brightness))

        return f"#{r:02x}{g:02x}{b:02x}"

    def _canvas_to_rich_text(self, canvas: list[list[tuple[str, str]]], height: int) -> Text:
        rich_text = Text()

        for y, row in enumerate(canvas):
            current_color = None
            current_chars = []

            for char, color in row:
                if color == current_color:
                    current_chars.append(char)
                else:
                    if current_chars and current_color:
                        rich_text.append("".join(current_chars), style=Style(color=current_color))
                    current_chars = [char]
                    current_color = color

            if current_chars and current_color:
                rich_text.append("".join(current_chars), style=Style(color=current_color))

            if y < height - 1:
                rich_text.append("\n")

        return rich_text

    def animate_idle(self):
        self.time_offset += 0.05
        self.smoothed_rms *= 0.95
        self._render_wave()
