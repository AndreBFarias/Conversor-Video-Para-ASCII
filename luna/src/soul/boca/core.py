from __future__ import annotations

import threading
import time
from typing import Any

import config
from src.core.entity_loader import EntityLoader, get_active_entity
from src.core.event_logger import get_event_logger
from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.soul.boca.providers import (
    ChatterboxProvider,
    CoquiProvider,
    DaemonProvider,
    ElevenLabsProvider,
    TTSParams,
    TTSProvider,
)
from src.soul.boca.sanitizer import sanitize_text

logger = get_logger(__name__)


class Boca:
    def __init__(self):
        from src.soul.boca.engine_check import (
            check_chatterbox,
            check_coqui,
            check_daemon,
            check_elevenlabs,
            get_effective_engine,
        )

        self.current_process = None
        self.elevenlabs_disponivel = False
        self.coqui_disponivel = False
        self.chatterbox_disponivel = False
        self.daemon_disponivel = False
        self._speech_lock = threading.Lock()

        self.active_entity_id = get_active_entity()
        self.entity_loader = EntityLoader(self.active_entity_id)
        self.entity_voice_config = self._load_entity_voice_config()

        check_daemon(self)
        check_elevenlabs(self)
        check_coqui(self)
        check_chatterbox(self)

        self.effective_engine = get_effective_engine(self)

        self._providers: list[TTSProvider] = []
        self._init_providers()

        logger.info(f"TTS Engine configurado: {config.TTS_ENGINE}")
        logger.info(f"TTS Engine efetivo: {self.effective_engine}")
        logger.info(f"TTS para entidade: {self.active_entity_id}")
        self._log_providers()

    def _init_providers(self) -> None:
        daemon = DaemonProvider(self)
        daemon.check_availability()

        coqui = CoquiProvider(self)
        coqui.check_availability()

        chatterbox = ChatterboxProvider(self)
        chatterbox.check_availability()

        elevenlabs = ElevenLabsProvider(self)
        elevenlabs.check_availability()

        all_providers = [daemon, elevenlabs, coqui, chatterbox]
        available = [p for p in all_providers if p.is_available]
        available.sort(key=lambda p: -p.priority)

        preferred = config.TTS_ENGINE.lower()
        ordered = []

        if daemon.is_available:
            ordered.append(daemon)

        for p in available:
            if p.name == preferred and p not in ordered:
                ordered.insert(1 if daemon.is_available else 0, p)
                break

        for p in available:
            if p not in ordered:
                ordered.append(p)

        self._providers = ordered

    def _log_providers(self) -> None:
        for p in self._providers:
            logger.info(f"TTS Provider: {p}")

    def _load_entity_voice_config(self) -> dict:
        try:
            entity_config = self.entity_loader.get_config()
            return entity_config.get("voice", {})
        except Exception as e:
            logger.error(f"Erro ao carregar voice config da entidade: {e}")
            return {}

    def reload_for_entity(self, entity_id: str) -> None:
        logger.info(f"Recarregando TTS para entidade: {entity_id}")

        self.active_entity_id = entity_id
        self.entity_loader = EntityLoader(entity_id)
        self.entity_voice_config = self._load_entity_voice_config()

        from src.soul.boca.engine_check import (
            check_chatterbox,
            check_coqui,
            check_elevenlabs,
            get_effective_engine,
        )

        self.coqui_disponivel = False
        self.chatterbox_disponivel = False
        self.elevenlabs_disponivel = False

        check_elevenlabs(self)
        check_coqui(self)
        check_chatterbox(self)

        self.effective_engine = get_effective_engine(self)
        self._init_providers()

        logger.info(f"TTS recarregado para {entity_id} (engine: {self.effective_engine})")

    def falar(self, texto: str, metatags: dict[str, Any] | None = None) -> None:
        if not texto or not texto.strip():
            logger.warning("Texto vazio, nada a falar")
            return

        with self._speech_lock:
            self._falar_interno(texto, metatags)

    def gerar_audio(self, texto: str, metatags: dict[str, Any] | None = None) -> str | None:
        if not texto or not texto.strip():
            logger.warning("Texto vazio, nada a gerar")
            return None

        start_time = time.time()
        evt_logger = get_event_logger()

        with self._speech_lock:
            result = self._gerar_audio_interno(texto, metatags)

        duration_ms = (time.time() - start_time) * 1000
        engine = self._providers[0].name if self._providers else "none"
        evt_logger.tts(
            "generate",
            success=result is not None,
            duration_ms=duration_ms,
            details={"engine": engine, "chars": len(texto)},
        )
        return result

    def _gerar_audio_interno(self, texto: str, metatags: dict = None) -> str | None:
        texto = sanitize_text(texto)
        params = TTSParams.from_metatags(metatags)

        logger.info(f"[GERAR_AUDIO] Tentando {len(self._providers)} providers...")

        for provider in self._providers:
            logger.info(f"[GERAR_AUDIO] Tentando {provider.name}...")
            path = provider.generate(texto, params)
            if path:
                logger.info(f"[GERAR_AUDIO] Sucesso com {provider.name}")
                return path
            logger.warning(f"[GERAR_AUDIO] {provider.name} falhou, tentando proximo...")

        logger.error("Todos os providers de TTS falharam na geracao")
        return None

    @perf_monitor("boca.falar")
    def _falar_interno(self, texto: str, metatags: dict = None):
        texto = sanitize_text(texto)
        params = TTSParams.from_metatags(metatags)

        logger.info(f"Tentando falar: '{texto[:50]}...' (speed={params.speed:.2f})")

        for provider in self._providers:
            logger.info(f"[FALAR] Tentando {provider.name}...")
            if provider.speak(texto, params):
                logger.info(f"[FALAR] Sucesso com {provider.name}")
                return
            logger.warning(f"[FALAR] {provider.name} falhou, tentando proximo...")

        logger.error("Todos os providers de TTS falharam")

    def parar(self) -> None:
        from src.soul.boca.playback import parar

        parar(self)

    def get_providers(self) -> list[TTSProvider]:
        return self._providers.copy()

    def get_provider_by_name(self, name: str) -> TTSProvider | None:
        for p in self._providers:
            if p.name == name:
                return p
        return None
