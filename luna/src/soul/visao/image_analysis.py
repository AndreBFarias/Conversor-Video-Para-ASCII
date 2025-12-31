from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

IMAGEHASH_AVAILABLE = False
try:
    import imagehash

    IMAGEHASH_AVAILABLE = True
except ImportError:
    logger.warning("imagehash nao instalado. Usando fallback para deteccao de mudancas.")


class ImageAnalyzer:
    def __init__(self, change_threshold: int = 15, histogram_threshold: float = 0.7):
        self.CHANGE_THRESHOLD = change_threshold
        self.HISTOGRAM_THRESHOLD = histogram_threshold

    def calcular_hash_perceptual(self, frame_rgb: np.ndarray) -> str | None:
        if not IMAGEHASH_AVAILABLE:
            return None

        try:
            img = Image.fromarray(frame_rgb)
            return str(imagehash.phash(img))
        except Exception as e:
            logger.warning(f"Erro ao calcular hash: {e}")
            return None

    def calcular_diferenca_histograma(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        try:
            hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

            cv2.normalize(hist1, hist1)
            cv2.normalize(hist2, hist2)

            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return correlation
        except Exception as e:
            logger.warning(f"Erro ao comparar histogramas: {e}")
            return 1.0

    def comparar_hashes(self, hash1: str, hash2: str) -> int | None:
        if not IMAGEHASH_AVAILABLE:
            return None

        try:
            diferenca = imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)
            return diferenca
        except Exception as e:
            logger.warning(f"Erro ao comparar hashes perceptuais: {e}")
            return None


class FaceAnalyzer:
    def __init__(self, memoria):
        self.memoria = memoria

    def analisar_rostos(self, frame_rgb: np.ndarray) -> list[dict]:
        from src.soul.memoria import FACE_RECOGNITION_AVAILABLE, extrair_embeddings_do_frame

        if not FACE_RECOGNITION_AVAILABLE:
            return []

        try:
            embeddings_e_posicoes = extrair_embeddings_do_frame(frame_rgb)

            resultados = []
            for embedding, posicao in embeddings_e_posicoes:
                nome, distancia = self.memoria.identificar_rosto(embedding)

                resultados.append(
                    {
                        "nome": nome or "Desconhecido",
                        "eh_novo": nome is None,
                        "distancia": distancia,
                        "posicao": posicao,
                        "embedding": embedding,
                    }
                )

            return resultados
        except Exception as e:
            logger.error(f"Erro na analise de rostos: {e}")
            return []


class ChangeDetector:
    def __init__(self, image_analyzer: ImageAnalyzer, face_analyzer: FaceAnalyzer):
        self.image_analyzer = image_analyzer
        self.face_analyzer = face_analyzer

        self.last_frame = None
        self.last_frame_hash = None
        self.last_face_count = 0
        self.last_pessoas = []
        self.frame_count = 0

    def detectar_mudanca_significativa(self, frame_rgb: np.ndarray) -> tuple[bool, str, list[dict]]:
        self.frame_count += 1
        pessoas = self.face_analyzer.analisar_rostos(frame_rgb)

        if self.last_frame is None:
            self.last_frame = frame_rgb.copy()
            self.last_face_count = len(pessoas)
            self.last_pessoas = [p["nome"] for p in pessoas]
            self.last_frame_hash = self.image_analyzer.calcular_hash_perceptual(frame_rgb)
            return True, "primeiro_frame", pessoas

        nomes_atuais = set(p["nome"] for p in pessoas)
        nomes_anteriores = set(self.last_pessoas)

        novos_rostos = [p for p in pessoas if p["eh_novo"]]
        if novos_rostos:
            self._atualizar_estado(frame_rgb, pessoas)
            return True, "rosto_desconhecido_detectado", pessoas

        pessoas_entraram = nomes_atuais - nomes_anteriores - {"Desconhecido"}
        pessoas_sairam = nomes_anteriores - nomes_atuais - {"Desconhecido"}

        if pessoas_entraram:
            self._atualizar_estado(frame_rgb, pessoas)
            return True, f"pessoa_entrou:{','.join(pessoas_entraram)}", pessoas

        if pessoas_sairam:
            self._atualizar_estado(frame_rgb, pessoas)
            return True, f"pessoa_saiu:{','.join(pessoas_sairam)}", pessoas

        diff_rostos = len(pessoas) - self.last_face_count
        if abs(diff_rostos) >= 1:
            self._atualizar_estado(frame_rgb, pessoas)
            if diff_rostos > 0:
                return True, f"mais_rostos_detectados:{diff_rostos}", pessoas
            else:
                return True, f"menos_rostos_detectados:{abs(diff_rostos)}", pessoas

        correlacao = self.image_analyzer.calcular_diferenca_histograma(self.last_frame, frame_rgb)

        if correlacao < self.image_analyzer.HISTOGRAM_THRESHOLD:
            self._atualizar_estado(frame_rgb, pessoas)
            return True, f"mudanca_cenario:correlacao={correlacao:.2f}", pessoas

        if IMAGEHASH_AVAILABLE:
            hash_atual = self.image_analyzer.calcular_hash_perceptual(frame_rgb)
            if hash_atual and self.last_frame_hash:
                diferenca = self.image_analyzer.comparar_hashes(hash_atual, self.last_frame_hash)
                if diferenca is not None and diferenca > self.image_analyzer.CHANGE_THRESHOLD:
                    self._atualizar_estado(frame_rgb, pessoas)
                    return True, f"mudanca_visual:hash_diff={diferenca}", pessoas

        self._atualizar_estado(frame_rgb, pessoas)
        return False, "sem_mudanca", pessoas

    def _atualizar_estado(self, frame_rgb: np.ndarray, pessoas: list[dict]):
        self.last_frame = frame_rgb.copy()
        self.last_face_count = len(pessoas)
        self.last_pessoas = [p["nome"] for p in pessoas]
        self.last_frame_hash = self.image_analyzer.calcular_hash_perceptual(frame_rgb)
