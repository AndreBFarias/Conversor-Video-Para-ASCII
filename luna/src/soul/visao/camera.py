from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(self, webcam_index: int = 0):
        self.webcam_index = webcam_index

    def abrir(self) -> cv2.VideoCapture | None:
        logger.debug(f"[VISAO] Abrindo webcam (indice {self.webcam_index})...")
        cap = cv2.VideoCapture(self.webcam_index)

        if not cap.isOpened():
            logger.error(f"[VISAO] Nao foi possivel abrir a webcam (indice {self.webcam_index})")
            return None

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        for _ in range(3):
            cap.read()

        logger.debug("[VISAO] Webcam aberta")
        return cap

    def fechar(self, cap: cv2.VideoCapture):
        if cap is not None:
            cap.release()
            logger.debug("[VISAO] Webcam fechada")

    def capturar_frame(self) -> np.ndarray | None:
        cap = self.abrir()
        if cap is None:
            return None

        try:
            ret, frame = cap.read()

            if not ret:
                logger.warning("[VISAO] Falha ao ler frame na primeira tentativa")
                self.fechar(cap)

                cap = self.abrir()
                if cap is None:
                    return None

                ret, frame = cap.read()
                if not ret:
                    logger.error("[VISAO] Falha ao ler frame mesmo apos reabrir")
                    return None

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            logger.debug(f"[VISAO] Frame capturado: {frame_rgb.shape}")
            return frame_rgb
        finally:
            self.fechar(cap)
