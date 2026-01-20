import numpy as np
import cv2
import os
from typing import Optional

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'models', 'selfie_segmenter.tflite')


class AutoSegmenter:
    def __init__(self, threshold: float = 0.5, use_gpu: bool = True):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe nao esta instalado. Execute: pip install mediapipe")

        self.threshold = threshold
        self.use_gpu = use_gpu and CUPY_AVAILABLE

        if self.use_gpu:
            try:
                test = cp.array([1])
                del test
            except Exception as e:
                print(f"[AutoSeg] GPU/CUDA nao disponivel, usando CPU: {e}")
                self.use_gpu = False

        self._prev_mask = None
        self._temporal_weight = 0.6

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo nao encontrado: {MODEL_PATH}")

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_category_mask=True,
            running_mode=vision.RunningMode.IMAGE
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)

    def process(self, frame: np.ndarray) -> np.ndarray:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self.segmenter.segment(mp_image)

        if not result.category_mask:
            return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

        category_mask = result.category_mask.numpy_view()

        if self.use_gpu:
            try:
                mask_gpu = cp.asarray(category_mask)
                mask = cp.where(mask_gpu > 0, cp.uint8(255), cp.uint8(0))
                mask = cp.asnumpy(mask)
            except Exception as e:
                print(f"[AutoSeg] Falha ao usar GPU, caindo para CPU: {e}")
                self.use_gpu = False
                mask = np.where(category_mask > 0, 255, 0).astype(np.uint8)
        else:
            mask = np.where(category_mask > 0, 255, 0).astype(np.uint8)

        if self._prev_mask is not None and self._prev_mask.shape == mask.shape:
            mask = cv2.addWeighted(
                mask.astype(np.float32), 1 - self._temporal_weight,
                self._prev_mask.astype(np.float32), self._temporal_weight,
                0
            ).astype(np.uint8)

        self._prev_mask = mask.copy()

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def set_threshold(self, threshold: float):
        self.threshold = max(0.1, min(0.9, threshold))

    def set_temporal_weight(self, weight: float):
        self._temporal_weight = max(0.0, min(0.9, weight))

    def reset(self):
        self._prev_mask = None

    def close(self):
        if hasattr(self, 'segmenter') and self.segmenter:
            try:
                self.segmenter.close()
            except Exception:
                pass
            self.segmenter = None
        self._prev_mask = None

        import gc
        gc.collect()

        try:
            import tensorflow as tf
            tf.keras.backend.clear_session()
        except Exception:
            pass


def is_available() -> bool:
    return MEDIAPIPE_AVAILABLE and os.path.exists(MODEL_PATH)


# "O homem e a medida de todas as coisas." - Protagoras
