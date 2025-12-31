from __future__ import annotations

import time

import numpy as np

import config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class AdaptiveVAD:
    def __init__(self, vad_config: dict):
        self.enabled = vad_config.get("AUTO_ADJUST", config.VAD_CONFIG.get("AUTO_ADJUST", True))
        self.multiplier = vad_config.get("NOISE_MULTIPLIER", config.VAD_CONFIG.get("NOISE_MULTIPLIER", 2.0))
        self.calibration_seconds = vad_config.get(
            "CALIBRATION_SECONDS", config.VAD_CONFIG.get("CALIBRATION_SECONDS", 3.0)
        )
        self.min_threshold = vad_config.get("MIN_THRESHOLD", config.VAD_CONFIG.get("MIN_THRESHOLD", 500))
        self.max_threshold = vad_config.get("MAX_THRESHOLD", config.VAD_CONFIG.get("MAX_THRESHOLD", 15000))
        self.base_threshold = vad_config.get("ENERGY_THRESHOLD", config.VAD_CONFIG.get("ENERGY_THRESHOLD", 6000))

        self._rms_samples: list[float] = []
        self._calibration_start: float | None = None
        self._calibrated = False
        self._current_threshold = self.base_threshold
        self._noise_floor = 0.0

        if self.enabled:
            logger.info(
                f"[ADAPTIVE_VAD] Habilitado: multiplier={self.multiplier}, calibration={self.calibration_seconds}s, range=[{self.min_threshold}, {self.max_threshold}]"
            )
        else:
            logger.info(f"[ADAPTIVE_VAD] Desabilitado, usando threshold fixo: {self.base_threshold}")

    def process_chunk(self, rms: float) -> float:
        if not self.enabled:
            return self.base_threshold

        if self._calibration_start is None:
            self._calibration_start = time.time()
            logger.info("[ADAPTIVE_VAD] Iniciando calibracao...")

        if not self._calibrated:
            elapsed = time.time() - self._calibration_start

            if elapsed < self.calibration_seconds:
                self._rms_samples.append(rms)
                return self.max_threshold

            self._calibrate()

        return self._current_threshold

    def _calibrate(self):
        if not self._rms_samples:
            self._current_threshold = self.base_threshold
            logger.warning("[ADAPTIVE_VAD] Sem amostras, usando threshold base")
        else:
            self._noise_floor = np.mean(self._rms_samples)
            raw_threshold = self._noise_floor * self.multiplier
            self._current_threshold = int(np.clip(raw_threshold, self.min_threshold, self.max_threshold))

            logger.info("=" * 50)
            logger.info("[ADAPTIVE_VAD] CALIBRACAO COMPLETA")
            logger.info(f"[ADAPTIVE_VAD]   Amostras: {len(self._rms_samples)}")
            logger.info(f"[ADAPTIVE_VAD]   Noise floor: {self._noise_floor:.0f}")
            logger.info(f"[ADAPTIVE_VAD]   Multiplier: {self.multiplier}x")
            logger.info(f"[ADAPTIVE_VAD]   Threshold calculado: {raw_threshold:.0f}")
            logger.info(f"[ADAPTIVE_VAD]   Threshold final: {self._current_threshold}")
            logger.info("=" * 50)

        self._calibrated = True
        self._rms_samples = []

    def recalibrate(self):
        self._calibrated = False
        self._calibration_start = None
        self._rms_samples = []
        logger.info("[ADAPTIVE_VAD] Recalibracao solicitada")

    @property
    def is_calibrated(self) -> bool:
        return self._calibrated

    @property
    def current_threshold(self) -> float:
        return self._current_threshold

    @property
    def noise_floor(self) -> float:
        return self._noise_floor
