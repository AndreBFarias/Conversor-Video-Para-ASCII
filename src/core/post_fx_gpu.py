# -*- coding: utf-8 -*-
import numpy as np
import cv2
from typing import Optional
from dataclasses import dataclass

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None


@dataclass
class PostFXConfig:
    bloom_enabled: bool = False
    bloom_intensity: float = 0.6
    bloom_radius: int = 15
    bloom_threshold: int = 150

    chromatic_enabled: bool = False
    chromatic_shift: int = 5

    scanlines_enabled: bool = False
    scanlines_intensity: float = 0.5
    scanlines_spacing: int = 3

    glitch_enabled: bool = False
    glitch_intensity: float = 0.3
    glitch_block_size: int = 16


class PostFXProcessor:

    def __init__(self, config: Optional[PostFXConfig] = None, use_gpu: bool = True):
        self.config = config or PostFXConfig()
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self._scanline_mask = None
        self._scanline_mask_gpu = None
        self._scanline_shape = None
        self._gpu_bloom_failed = False

    def process(self, frame: np.ndarray) -> np.ndarray:
        if not any([
            self.config.bloom_enabled,
            self.config.chromatic_enabled,
            self.config.scanlines_enabled,
            self.config.glitch_enabled
        ]):
            return frame

        result = frame.copy()

        if self.config.glitch_enabled:
            result = self._apply_glitch(result)

        if self.config.chromatic_enabled:
            result = self._apply_chromatic_aberration(result)

        if self.config.bloom_enabled:
            result = self._apply_bloom(result)

        if self.config.scanlines_enabled:
            result = self._apply_scanlines(result)

        return result

    def _apply_bloom(self, frame: np.ndarray) -> np.ndarray:
        if self.use_gpu and not self._gpu_bloom_failed:
            try:
                return self._bloom_gpu(frame)
            except Exception as e:
                print(f"[PostFX] Bloom GPU falhou, usando CPU: {e}")
                self._gpu_bloom_failed = True
        return self._bloom_cpu(frame)

    def _bloom_cpu(self, frame: np.ndarray) -> np.ndarray:
        if len(frame.shape) == 2:
            gray = frame
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        _, bright_mask = cv2.threshold(gray, self.config.bloom_threshold, 255, cv2.THRESH_BINARY)
        bright_areas = cv2.bitwise_and(frame, frame, mask=bright_mask)

        ksize = max(3, self.config.bloom_radius * 2 + 1)
        if ksize % 2 == 0:
            ksize += 1

        blurred = cv2.GaussianBlur(bright_areas, (ksize, ksize), 0)
        blurred = cv2.GaussianBlur(blurred, (ksize, ksize), 0)

        intensity = self.config.bloom_intensity
        result = cv2.addWeighted(frame, 1.0, blurred, intensity, 0)

        return np.clip(result, 0, 255).astype(np.uint8)

    def _bloom_gpu(self, frame: np.ndarray) -> np.ndarray:
        if len(frame.shape) == 2:
            gray = frame
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        _, bright_mask = cv2.threshold(gray, self.config.bloom_threshold, 255, cv2.THRESH_BINARY)
        bright_areas = cv2.bitwise_and(frame, frame, mask=bright_mask)

        ksize = max(3, self.config.bloom_radius * 2 + 1)
        if ksize % 2 == 0:
            ksize += 1

        blurred = cv2.GaussianBlur(bright_areas, (ksize, ksize), 0)
        blurred = cv2.GaussianBlur(blurred, (ksize, ksize), 0)

        frame_gpu = cp.asarray(frame, dtype=cp.float32)
        blurred_gpu = cp.asarray(blurred, dtype=cp.float32)

        intensity = self.config.bloom_intensity
        result = frame_gpu + blurred_gpu * intensity

        result = cp.clip(result, 0, 255).astype(cp.uint8)
        return cp.asnumpy(result)

    def _apply_chromatic_aberration(self, frame: np.ndarray) -> np.ndarray:
        if len(frame.shape) == 2:
            return frame

        if self.use_gpu:
            try:
                return self._chromatic_gpu(frame)
            except Exception:
                pass
        return self._chromatic_cpu(frame)

    def _chromatic_cpu(self, frame: np.ndarray) -> np.ndarray:
        b, g, r = cv2.split(frame)
        shift = self.config.chromatic_shift
        h, w = frame.shape[:2]

        M_left = np.float32([[1, 0, -shift], [0, 1, 0]])
        M_right = np.float32([[1, 0, shift], [0, 1, 0]])

        r_shifted = cv2.warpAffine(r, M_right, (w, h), borderMode=cv2.BORDER_REPLICATE)
        b_shifted = cv2.warpAffine(b, M_left, (w, h), borderMode=cv2.BORDER_REPLICATE)

        return cv2.merge([b_shifted, g, r_shifted])

    def _chromatic_gpu(self, frame: np.ndarray) -> np.ndarray:
        frame_gpu = cp.asarray(frame)
        shift = self.config.chromatic_shift

        result = cp.zeros_like(frame_gpu)
        result[:, :, 1] = frame_gpu[:, :, 1]

        if shift > 0:
            result[:, shift:, 2] = frame_gpu[:, :-shift, 2]
            result[:, :shift, 2] = frame_gpu[:, 0:1, 2]

            result[:, :-shift, 0] = frame_gpu[:, shift:, 0]
            result[:, -shift:, 0] = frame_gpu[:, -1:, 0]

        return cp.asnumpy(result)

    def _apply_scanlines(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]

        if self._scanline_mask is None or self._scanline_shape != (h, w):
            self._create_scanline_mask(h, w)

        if self.use_gpu and self._scanline_mask_gpu is not None:
            try:
                return self._scanlines_gpu(frame)
            except Exception:
                pass
        return self._scanlines_cpu(frame)

    def _create_scanline_mask(self, h: int, w: int):
        self._scanline_shape = (h, w)
        mask = np.ones((h, w), dtype=np.float32)

        spacing = max(1, self.config.scanlines_spacing)
        intensity = 1.0 - self.config.scanlines_intensity

        for y in range(0, h, spacing):
            if y < h:
                mask[y, :] = intensity

        self._scanline_mask = mask
        if self.use_gpu and GPU_AVAILABLE:
            try:
                self._scanline_mask_gpu = cp.asarray(mask)
            except Exception:
                self._scanline_mask_gpu = None

    def _scanlines_cpu(self, frame: np.ndarray) -> np.ndarray:
        if len(frame.shape) == 2:
            result = frame.astype(np.float32) * self._scanline_mask
            return np.clip(result, 0, 255).astype(np.uint8)

        result = frame.astype(np.float32)
        for i in range(3):
            result[:, :, i] *= self._scanline_mask
        return np.clip(result, 0, 255).astype(np.uint8)

    def _scanlines_gpu(self, frame: np.ndarray) -> np.ndarray:
        frame_gpu = cp.asarray(frame).astype(cp.float32)

        if len(frame.shape) == 2:
            result = frame_gpu * self._scanline_mask_gpu
        else:
            for i in range(3):
                frame_gpu[:, :, i] *= self._scanline_mask_gpu
            result = frame_gpu

        result = cp.clip(result, 0, 255).astype(cp.uint8)
        return cp.asnumpy(result)

    def _apply_glitch(self, frame: np.ndarray) -> np.ndarray:
        if np.random.random() > self.config.glitch_intensity:
            return frame

        if self.use_gpu:
            try:
                return self._glitch_gpu(frame)
            except Exception:
                pass
        return self._glitch_cpu(frame)

    def _glitch_cpu(self, frame: np.ndarray) -> np.ndarray:
        result = frame.copy()
        h, w = frame.shape[:2]
        block_size = max(4, self.config.glitch_block_size)

        num_glitches = np.random.randint(2, 8)

        for _ in range(num_glitches):
            if h <= block_size:
                continue

            y = np.random.randint(0, h - block_size)
            block_h = np.random.randint(block_size // 2, block_size * 3)
            block_h = min(block_h, h - y)

            shift = np.random.randint(-w // 3, w // 3)

            if shift > 0 and w > shift:
                result[y:y+block_h, shift:] = frame[y:y+block_h, :w-shift]
                result[y:y+block_h, :shift] = frame[y:y+block_h, w-shift:]
            elif shift < 0:
                shift = abs(shift)
                if w > shift:
                    result[y:y+block_h, :w-shift] = frame[y:y+block_h, shift:]
                    result[y:y+block_h, w-shift:] = frame[y:y+block_h, :shift]

        if np.random.random() < 0.5 and len(frame.shape) == 3:
            channel = np.random.randint(0, 3)
            y = np.random.randint(0, max(1, h - block_size))
            block_h = np.random.randint(block_size, block_size * 4)
            block_h = min(block_h, h - y)
            color_shift = np.random.randint(-50, 50)
            result[y:y+block_h, :, channel] = np.clip(
                result[y:y+block_h, :, channel].astype(np.int16) + color_shift,
                0, 255
            ).astype(np.uint8)

        return result

    def _glitch_gpu(self, frame: np.ndarray) -> np.ndarray:
        frame_gpu = cp.asarray(frame)
        result = frame_gpu.copy()
        h, w = frame.shape[:2]
        block_size = max(4, self.config.glitch_block_size)

        num_glitches = np.random.randint(2, 8)

        for _ in range(num_glitches):
            if h <= block_size:
                continue

            y = np.random.randint(0, h - block_size)
            block_h = np.random.randint(block_size // 2, block_size * 3)
            block_h = min(block_h, h - y)

            shift = np.random.randint(-w // 3, w // 3)

            if shift > 0 and w > shift:
                result[y:y+block_h, shift:] = frame_gpu[y:y+block_h, :w-shift]
                result[y:y+block_h, :shift] = frame_gpu[y:y+block_h, w-shift:]
            elif shift < 0:
                shift = abs(shift)
                if w > shift:
                    result[y:y+block_h, :w-shift] = frame_gpu[y:y+block_h, shift:]
                    result[y:y+block_h, w-shift:] = frame_gpu[y:y+block_h, :shift]

        if np.random.random() < 0.5 and len(frame.shape) == 3:
            channel = np.random.randint(0, 3)
            y = np.random.randint(0, max(1, h - block_size))
            block_h = np.random.randint(block_size, block_size * 4)
            block_h = min(block_h, h - y)
            color_shift = np.random.randint(-50, 50)
            result[y:y+block_h, :, channel] = cp.clip(
                result[y:y+block_h, :, channel].astype(cp.int16) + color_shift,
                0, 255
            ).astype(cp.uint8)

        return cp.asnumpy(result)

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        if 'scanlines_spacing' in kwargs or 'scanlines_intensity' in kwargs:
            self._scanline_mask = None
            self._scanline_mask_gpu = None


def create_postfx_from_config(config_parser) -> PostFXProcessor:
    try:
        fx_config = PostFXConfig(
            bloom_enabled=config_parser.getboolean('PostFX', 'bloom_enabled', fallback=False),
            bloom_intensity=config_parser.getfloat('PostFX', 'bloom_intensity', fallback=0.6),
            bloom_radius=config_parser.getint('PostFX', 'bloom_radius', fallback=15),
            bloom_threshold=config_parser.getint('PostFX', 'bloom_threshold', fallback=150),
            chromatic_enabled=config_parser.getboolean('PostFX', 'chromatic_enabled', fallback=False),
            chromatic_shift=config_parser.getint('PostFX', 'chromatic_shift', fallback=5),
            scanlines_enabled=config_parser.getboolean('PostFX', 'scanlines_enabled', fallback=False),
            scanlines_intensity=config_parser.getfloat('PostFX', 'scanlines_intensity', fallback=0.5),
            scanlines_spacing=config_parser.getint('PostFX', 'scanlines_spacing', fallback=3),
            glitch_enabled=config_parser.getboolean('PostFX', 'glitch_enabled', fallback=False),
            glitch_intensity=config_parser.getfloat('PostFX', 'glitch_intensity', fallback=0.3),
            glitch_block_size=config_parser.getint('PostFX', 'glitch_block_size', fallback=16),
        )
        use_gpu = config_parser.getboolean('Conversor', 'gpu_enabled', fallback=True)
        return PostFXProcessor(fx_config, use_gpu=use_gpu)
    except Exception:
        return PostFXProcessor()


# "A tecnologia e um servo util, mas um mestre perigoso." - Christian Lous Lange
