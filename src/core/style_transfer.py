# -*- coding: utf-8 -*-
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class StyleConfig:
    style_enabled: bool = False
    style_preset: str = 'none'
    dog_sigma1: float = 0.5
    dog_sigma2: float = 1.6
    dog_tau: float = 0.98
    edge_strength: float = 1.0


STYLE_PRESETS = {
    'none': {
        'name': 'Original',
        'dog_sigma1': 0.5,
        'dog_sigma2': 1.6,
        'dog_tau': 1.0,
        'edge_strength': 0.0
    },
    'sketch': {
        'name': 'Sketch',
        'dog_sigma1': 0.8,
        'dog_sigma2': 2.5,
        'dog_tau': 0.95,
        'edge_strength': 3.0
    },
    'ink': {
        'name': 'Ink',
        'dog_sigma1': 0.6,
        'dog_sigma2': 2.0,
        'dog_tau': 0.92,
        'edge_strength': 4.0
    },
    'comic': {
        'name': 'Comic',
        'dog_sigma1': 1.0,
        'dog_sigma2': 3.0,
        'dog_tau': 0.97,
        'edge_strength': 2.5
    },
    'neon': {
        'name': 'Neon',
        'dog_sigma1': 0.8,
        'dog_sigma2': 2.5,
        'dog_tau': 0.95,
        'edge_strength': 2.5
    },
    'emboss': {
        'name': 'Emboss',
        'dog_sigma1': 0.5,
        'dog_sigma2': 1.5,
        'dog_tau': 0.94,
        'edge_strength': 3.5
    },
    'cyberpunk': {
        'name': 'Cyberpunk',
        'dog_sigma1': 0.7,
        'dog_sigma2': 2.2,
        'dog_tau': 0.93,
        'edge_strength': 3.0
    }
}


class StyleTransferProcessor:

    def __init__(self, config: Optional[StyleConfig] = None):
        self.config = config or StyleConfig()
        self._cyberpunk_cache = {}

    def process(self, frame: np.ndarray) -> np.ndarray:
        if not self.config.style_enabled or self.config.style_preset == 'none':
            return frame

        if self.config.edge_strength <= 0:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        edges = self._compute_edges(gray)

        if self.config.style_preset == 'neon':
            edges_color = cv2.applyColorMap(edges, cv2.COLORMAP_HOT)
            result = cv2.addWeighted(frame, 0.3, edges_color, 0.7, 0)
        elif self.config.style_preset == 'cyberpunk':
            result = self._apply_cyberpunk(frame, edges)
        elif self.config.style_preset in ('sketch', 'ink'):
            edges_inv = 255 - edges
            result = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2BGR)
        elif self.config.style_preset == 'emboss':
            edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            result = cv2.addWeighted(frame, 0.4, edges_3ch, 0.6, 0)
        else:
            edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            result = cv2.addWeighted(frame, 0.5, edges_3ch, 0.5 * self.config.edge_strength, 0)

        return result

    def _compute_edges(self, gray: np.ndarray) -> np.ndarray:
        sigma1 = max(0.1, self.config.dog_sigma1)
        sigma2 = max(sigma1 + 0.1, self.config.dog_sigma2)

        ksize1 = int(sigma1 * 6) | 1
        ksize2 = int(sigma2 * 6) | 1

        blur1 = cv2.GaussianBlur(gray, (ksize1, ksize1), sigma1)
        blur2 = cv2.GaussianBlur(gray, (ksize2, ksize2), sigma2)

        dog = blur1.astype(np.float32) - self.config.dog_tau * blur2.astype(np.float32)

        dog = np.clip(dog * self.config.edge_strength + 128, 0, 255).astype(np.uint8)

        return dog

    def _apply_cyberpunk(self, frame: np.ndarray, edges: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        cache_key = (h, w)

        if cache_key not in self._cyberpunk_cache:
            gradient = np.linspace(0, 1, w, dtype=np.float32).reshape(1, w)
            gradient = np.tile(gradient, (h, 1))

            magenta = np.zeros((h, w, 3), dtype=np.float32)
            magenta[:, :, 0] = 200
            magenta[:, :, 2] = 255

            cyan = np.zeros((h, w, 3), dtype=np.float32)
            cyan[:, :, 0] = 255
            cyan[:, :, 1] = 255

            neon_color = (magenta * (1 - gradient[:, :, np.newaxis]) +
                          cyan * gradient[:, :, np.newaxis])

            self._cyberpunk_cache[cache_key] = neon_color

        neon_color = self._cyberpunk_cache[cache_key]

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.float32) * 1.4, 0, 255).astype(np.uint8)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2].astype(np.float32) * 1.1, 0, 255).astype(np.uint8)
        saturated = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        edge_mask = (edges > 127).astype(np.float32)
        edge_glow = neon_color * edge_mask[:, :, np.newaxis]

        result = saturated.astype(np.float32) * 0.6 + edge_glow * 0.8

        return np.clip(result, 0, 255).astype(np.uint8)

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def set_preset(self, preset_name: str):
        if preset_name in STYLE_PRESETS:
            self.config.style_preset = preset_name
            preset = STYLE_PRESETS[preset_name]
            self.config.dog_sigma1 = preset.get('dog_sigma1', 0.5)
            self.config.dog_sigma2 = preset.get('dog_sigma2', 1.6)
            self.config.dog_tau = preset.get('dog_tau', 0.98)
            self.config.edge_strength = preset.get('edge_strength', 1.0)


def create_style_processor_from_config(config_parser) -> StyleTransferProcessor:
    try:
        style_config = StyleConfig(
            style_enabled=config_parser.getboolean('Style', 'style_enabled', fallback=False),
            style_preset=config_parser.get('Style', 'style_preset', fallback='none'),
        )
        return StyleTransferProcessor(style_config)
    except Exception:
        return StyleTransferProcessor()


# "A simplicidade e a sofisticacao suprema." - Leonardo da Vinci
