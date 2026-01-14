# -*- coding: utf-8 -*-
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List

try:
    GPU_AVAILABLE = cv2.cuda.getCudaEnabledDeviceCount() > 0
except:
    GPU_AVAILABLE = False


@dataclass
class OpticalFlowConfig:
    enabled: bool = False
    target_fps: int = 30
    quality: str = 'medium'


QUALITY_PRESETS = {
    'fast': {
        'pyr_scale': 0.5,
        'levels': 2,
        'winsize': 10,
        'iterations': 2,
        'poly_n': 5,
        'poly_sigma': 1.1
    },
    'medium': {
        'pyr_scale': 0.5,
        'levels': 3,
        'winsize': 15,
        'iterations': 3,
        'poly_n': 5,
        'poly_sigma': 1.2
    },
    'high': {
        'pyr_scale': 0.5,
        'levels': 4,
        'winsize': 20,
        'iterations': 5,
        'poly_n': 7,
        'poly_sigma': 1.5
    }
}


class OpticalFlowInterpolator:

    def __init__(self, config: Optional[OpticalFlowConfig] = None):
        self.config = config or OpticalFlowConfig()
        self.prev_frame = None
        self.prev_gray = None
        self.use_gpu = GPU_AVAILABLE
        self._flow_gpu = None

        if self.use_gpu:
            try:
                self._flow_gpu = cv2.cuda.FarnebackOpticalFlow_create()
            except Exception as e:
                print(f"[OpticalFlow] GPU nao disponivel: {e}")
                self.use_gpu = False

    def set_source_fps(self, fps: float):
        self.source_fps = fps

    def get_interpolation_factor(self, source_fps: float) -> int:
        if source_fps <= 0:
            return 1
        factor = int(self.config.target_fps / source_fps)
        return max(1, min(factor, 4))

    def process_frame(self, frame: np.ndarray) -> List[np.ndarray]:
        if not self.config.enabled:
            self.prev_frame = frame.copy()
            self.prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return [frame]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            self.prev_gray = gray.copy()
            return [frame]

        flow = self._compute_flow(self.prev_gray, gray)

        interpolated = self._interpolate_frames(self.prev_frame, frame, flow)

        self.prev_frame = frame.copy()
        self.prev_gray = gray.copy()

        return interpolated

    def _compute_flow(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        preset = QUALITY_PRESETS.get(self.config.quality, QUALITY_PRESETS['medium'])

        if self.use_gpu and self._flow_gpu:
            try:
                prev_gpu = cv2.cuda_GpuMat()
                curr_gpu = cv2.cuda_GpuMat()
                prev_gpu.upload(prev_gray)
                curr_gpu.upload(curr_gray)

                flow_gpu = self._flow_gpu.calc(prev_gpu, curr_gpu, None)
                flow = flow_gpu.download()
                return flow
            except Exception:
                self.use_gpu = False

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=preset['pyr_scale'],
            levels=preset['levels'],
            winsize=preset['winsize'],
            iterations=preset['iterations'],
            poly_n=preset['poly_n'],
            poly_sigma=preset['poly_sigma'],
            flags=0
        )

        return flow

    def _interpolate_frames(self, prev_frame: np.ndarray, curr_frame: np.ndarray,
                           flow: np.ndarray) -> List[np.ndarray]:
        factor = self.get_interpolation_factor(getattr(self, 'source_fps', 15))

        if factor <= 1:
            return [curr_frame]

        h, w = prev_frame.shape[:2]
        y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)

        frames = []

        for i in range(1, factor + 1):
            t = i / factor

            map_x = x_coords + flow[..., 0] * t
            map_y = y_coords + flow[..., 1] * t

            map_x = np.clip(map_x, 0, w - 1)
            map_y = np.clip(map_y, 0, h - 1)

            warped_prev = cv2.remap(prev_frame, map_x, map_y, cv2.INTER_LINEAR)

            map_x_back = x_coords - flow[..., 0] * (1 - t)
            map_y_back = y_coords - flow[..., 1] * (1 - t)

            map_x_back = np.clip(map_x_back, 0, w - 1)
            map_y_back = np.clip(map_y_back, 0, h - 1)

            warped_curr = cv2.remap(curr_frame, map_x_back, map_y_back, cv2.INTER_LINEAR)

            blended = cv2.addWeighted(warped_prev, 1 - t, warped_curr, t, 0)

            frames.append(blended)

        return frames

    def reset(self):
        self.prev_frame = None
        self.prev_gray = None


def create_interpolator_from_config(config_parser) -> OpticalFlowInterpolator:
    try:
        of_config = OpticalFlowConfig(
            enabled=config_parser.getboolean('OpticalFlow', 'enabled', fallback=False),
            target_fps=config_parser.getint('OpticalFlow', 'target_fps', fallback=30),
            quality=config_parser.get('OpticalFlow', 'quality', fallback='medium'),
        )
        return OpticalFlowInterpolator(of_config)
    except Exception:
        return OpticalFlowInterpolator()


# "O tempo e uma ilusao." - Albert Einstein
