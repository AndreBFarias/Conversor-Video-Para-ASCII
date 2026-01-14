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
        'dog_sigma1': 0.5,
        'dog_sigma2': 1.5,
        'dog_tau': 0.98,
        'edge_strength': 1.5
    },
    'ink': {
        'name': 'Ink',
        'dog_sigma1': 0.4,
        'dog_sigma2': 1.2,
        'dog_tau': 0.95,
        'edge_strength': 2.0
    },
    'comic': {
        'name': 'Comic',
        'dog_sigma1': 0.6,
        'dog_sigma2': 2.0,
        'dog_tau': 0.99,
        'edge_strength': 1.2
    },
    'neon': {
        'name': 'Neon',
        'dog_sigma1': 0.5,
        'dog_sigma2': 1.5,
        'dog_tau': 0.98,
        'edge_strength': 1.0
    },
    'emboss': {
        'name': 'Emboss',
        'dog_sigma1': 0.3,
        'dog_sigma2': 1.0,
        'dog_tau': 0.97,
        'edge_strength': 1.8
    }
}


class StyleTransferProcessor:

    def __init__(self, config: Optional[StyleConfig] = None):
        self.config = config or StyleConfig()

    def process(self, frame: np.ndarray) -> np.ndarray:
        if not self.config.style_enabled or self.config.style_preset == 'none':
            return frame

        if self.config.edge_strength <= 0:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        edges = self._compute_edges(gray)

        if self.config.style_preset == 'neon':
            edges_color = cv2.applyColorMap(edges, cv2.COLORMAP_HOT)
            result = cv2.addWeighted(frame, 0.5, edges_color, 0.5, 0)
        elif self.config.style_preset in ('sketch', 'ink'):
            result = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        else:
            edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            result = cv2.addWeighted(frame, 0.7, edges_3ch, 0.3 * self.config.edge_strength, 0)

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
