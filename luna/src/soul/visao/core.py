from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import numpy as np

import config
from src.core.event_logger import get_event_logger
from src.core.metricas import get_metrics, perf_monitor
from src.soul.memoria import FACE_RECOGNITION_AVAILABLE, MemoriaDeRostos

from .cache import VisionCache
from .camera import CameraManager
from .image_analysis import ChangeDetector, FaceAnalyzer, ImageAnalyzer
from .person_profile import PersonProfileManager
from .providers import OllamaVisionProvider, VisionProviderFactory

if TYPE_CHECKING:
    from .providers import GeminiVisionProvider

logger = logging.getLogger(__name__)


class Visao:
    def __init__(self):
        self.webcam_index = config.VISION_CONFIG.get("CAMERA_INDEX", 0)
        self.metrics = get_metrics()

        self.camera = CameraManager(self.webcam_index)
        self.memoria = MemoriaDeRostos()

        self.image_analyzer = ImageAnalyzer()
        self.face_analyzer = FaceAnalyzer(self.memoria)
        self.change_detector = ChangeDetector(self.image_analyzer, self.face_analyzer)
        self.vision_cache = VisionCache()

        self._min_vision_interval = 3.0
        self._last_vision_time = 0
        self._last_api_call = 0
        self._min_api_interval = 10.0

        self.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}

        self.provider_name, self.provider, self.vision_error = VisionProviderFactory.create()
        self.vision_ready = self.provider is not None

        self.person_profile = PersonProfileManager(self.provider)

        if FACE_RECOGNITION_AVAILABLE:
            logger.info("Reconhecimento facial ativo")
        else:
            logger.warning("Reconhecimento facial desabilitado (face_recognition nao instalado)")

    @property
    def model_name(self) -> str | None:
        if hasattr(self.provider, "model_name"):
            return self.provider.model_name
        return None

    def reload_config(self):
        if self.provider_name == "local" and isinstance(self.provider, OllamaVisionProvider):
            old_model = self.provider.model_name
            new_model = config.VISION_LOCAL["model"]
            if old_model != new_model:
                logger.info(f"Modelo de visao atualizado: {old_model} -> {new_model}")
                self.provider.model_name = new_model
                if not self.provider.verify_model():
                    logger.warning(f"Novo modelo {new_model} nao disponivel")
        elif self.provider_name == "gemini" and self.provider:
            old_model = self.provider.model_name
            new_model = config.GEMINI_CONFIG["MODEL_NAME"]
            if old_model != new_model:
                logger.info(f"Modelo de visao Gemini atualizado: {old_model} -> {new_model}")
                self.provider.model_name = new_model

    def health_check(self) -> dict:
        status = {
            "ready": self.vision_ready,
            "provider": self.provider_name,
            "model": self.model_name,
            "error": self.vision_error,
            "face_recognition": FACE_RECOGNITION_AVAILABLE,
        }

        if self.provider_name == "local" and isinstance(self.provider, OllamaVisionProvider):
            status["ollama_healthy"] = self.provider.client.check_health() if self.provider.client else False

        return status

    def capturar_frame(self) -> np.ndarray | None:
        return self.camera.capturar_frame()

    def detectar_mudanca_significativa(self, frame_rgb: np.ndarray) -> tuple[bool, str, list[dict]]:
        return self.change_detector.detectar_mudanca_significativa(frame_rgb)

    def registrar_pessoa(self, nome: str, embedding: np.ndarray) -> bool:
        return self.memoria.registrar_rosto(nome, embedding)

    def registrar_rosto_imediato(self, nome: str, frame_rgb: np.ndarray | None = None) -> bool:
        if frame_rgb is None:
            frame_rgb = self.capturar_frame()
            if frame_rgb is None:
                logger.warning("Camera nao disponivel para registro imediato.")
                return False

        from src.soul.memoria import extrair_embeddings_do_frame

        embeddings_encontrados = extrair_embeddings_do_frame(frame_rgb)

        if not embeddings_encontrados:
            logger.warning("Nenhum rosto encontrado para registro.")
            return False

        embedding, _ = embeddings_encontrados[0]
        return self.memoria.registrar_rosto(nome, embedding)

    @perf_monitor("visao.olhar_agora")
    def olhar_agora(self) -> str:
        start_time = time.time()
        evt_logger = get_event_logger()
        self.stats["total_captures"] += 1

        now = time.time()
        time_since_last = now - self._last_vision_time
        if time_since_last < self._min_vision_interval:
            logger.debug(f"Vision throttled: {time_since_last:.1f}s < {self._min_vision_interval}s")
            cached = self.vision_cache.get_latest()
            if cached:
                return cached
            return "Ainda estou processando o que vi..."

        self._last_vision_time = now

        frame_rgb = self.capturar_frame()
        if frame_rgb is None:
            return "Nao consegui abrir meus olhos (erro na camera)."

        if self.provider is None:
            return "Vejo o mundo, mas minha mente (API) nao consegue processa-lo."

        frame_hash = self.image_analyzer.calcular_hash_perceptual(frame_rgb)

        if frame_hash:
            cached = self.vision_cache.get(frame_hash)
            if cached:
                self.stats["cache_hits"] += 1
                logger.info(f"Vision cache HIT (saved API call). Hash: {frame_hash[:8]}")
                return cached

        try:
            self.metrics.increment("visao.captures_total")
            self.stats["api_calls"] += 1

            descricao = self.provider.describe(frame_rgb)
            logger.info(f"Visao ({self.provider_name}): {descricao[:80]}...")

            if frame_hash:
                self.vision_cache.set(frame_hash, descricao)

            self.metrics.record_success("visao.vision_processing")

            reduction_pct = (
                (self.stats["cache_hits"] / self.stats["total_captures"] * 100)
                if self.stats["total_captures"] > 0
                else 0
            )
            logger.info(
                f"Vision quota: {self.stats['api_calls']} calls, {self.stats['cache_hits']} cached ({reduction_pct:.1f}% saved)"
            )

            duration_ms = (time.time() - start_time) * 1000
            evt_logger.vision(
                "describe", success=True, duration_ms=duration_ms, details={"provider": self.provider_name}
            )

            if self.provider_name == "local" and isinstance(self.provider, OllamaVisionProvider):
                self.provider.unload_model()

            return descricao

        except Exception as e:
            logger.error(f"Erro na visao: {e}", exc_info=True)
            self.metrics.record_failure("visao.vision_processing")
            self.metrics.increment("visao.vision_errors")
            duration_ms = (time.time() - start_time) * 1000
            evt_logger.vision("describe", success=False, error_msg=str(e)[:50], duration_ms=duration_ms)
            return f"Tentei olhar, mas minha visao falhou: {str(e)[:50]}..."

    def get_vision_stats(self) -> dict:
        total = self.stats["total_captures"]
        api = self.stats["api_calls"]
        cached = self.stats["cache_hits"]

        return {
            "total_captures": total,
            "api_calls": api,
            "cache_hits": cached,
            "local_detections": self.stats["local_detections"],
            "quota_reduction_pct": (cached / total * 100) if total > 0 else 0,
            "api_call_rate": (api / total * 100) if total > 0 else 0,
        }

    def olhar_inteligente(self) -> tuple[bool, str, str, list[dict]]:
        from src.soul.voice_profile import get_appearance_tracker

        self.stats["total_captures"] += 1

        frame_rgb = self.capturar_frame()
        if frame_rgb is None:
            return False, "", "Camera indisponivel", []

        mudou, tipo_mudanca, pessoas_identificadas = self.detectar_mudanca_significativa(frame_rgb)

        if not mudou:
            self.stats["local_detections"] += 1
            logger.info("Local detection: no significant change (saved API call)")
            return False, tipo_mudanca, "", pessoas_identificadas

        if self.provider is None:
            return True, tipo_mudanca, "Sem capacidade de analise (API indisponivel)", pessoas_identificadas

        now = time.time()
        if now - self._last_api_call < self._min_api_interval:
            logger.info(f"API throttle: skipping call (last call {now - self._last_api_call:.1f}s ago)")
            self.stats["local_detections"] += 1
            return False, tipo_mudanca, "", pessoas_identificadas

        self._last_api_call = now

        frame_hash = self.image_analyzer.calcular_hash_perceptual(frame_rgb)
        if frame_hash:
            cached = self.vision_cache.get(frame_hash)
            if cached:
                self.stats["cache_hits"] += 1
                logger.info(f"Vision cache hit on intelligent look")
                return True, tipo_mudanca, cached, pessoas_identificadas

        try:
            self.stats["api_calls"] += 1

            prompt = "Descreva em uma frase curta o que ha de mais importante nesta imagem. Responda em portugues."
            logger.info(f"Chamando Vision ({self.provider_name}) (mudanca: {tipo_mudanca})...")
            descricao = self.provider.describe(frame_rgb, prompt)

            if frame_hash:
                self.vision_cache.set(frame_hash, descricao)

            try:
                appearance_tracker = get_appearance_tracker()
                changed, comment = appearance_tracker.detect_change(descricao)
                if changed and comment:
                    descricao = f"{comment}\n\n{descricao}"
                    logger.info(f"[APPEARANCE] Mudanca detectada: {comment}")
                appearance_tracker.add_observation(descricao)
            except Exception as e:
                logger.debug(f"Erro ao verificar aparencia: {e}")

            local_rate = (
                (self.stats["local_detections"] / self.stats["total_captures"] * 100)
                if self.stats["total_captures"] > 0
                else 0
            )
            logger.info(
                f"Vision stats: {self.stats['api_calls']} API, {self.stats['local_detections']} local ({local_rate:.1f}% local)"
            )

            return True, tipo_mudanca, descricao, pessoas_identificadas

        except Exception as e:
            logger.error(f"Erro na visao inteligente: {e}")
            return True, tipo_mudanca, f"Erro: {str(e)[:40]}", pessoas_identificadas

    def hiper_descrever_pessoa(self, frame_rgb: np.ndarray = None) -> str:
        if frame_rgb is None:
            frame_rgb = self.capturar_frame()
            if frame_rgb is None:
                return "Nao consegui capturar imagem para descricao."

        return self.person_profile.hiper_descrever_pessoa(frame_rgb)

    def salvar_perfil_visual(self, nome: str, descricao: str, frame_rgb: np.ndarray = None) -> bool:
        return self.person_profile.salvar_perfil_visual(nome, descricao, frame_rgb)

    def release(self):
        logger.info("[VISAO] Cleanup do modulo de visao concluido")
