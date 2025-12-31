import logging
from typing import TYPE_CHECKING

import config
from src.soul.audio_threads import AudioCaptureThread, TranscriptionThread, TTSPlaybackThread, TTSThread
from src.soul.processing_threads import AnimationThread, CoordinatorThread, ProcessingThread
from src.soul.threading_manager import LunaThreadingManager, MonitorThread, TTSChunk
from src.soul.wake_word import WakeWordThread

if TYPE_CHECKING:
    from .luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class ThreadingSetupMixin:
    def setup_threading(self: "TemploDaAlma") -> None:
        logger.info("Configurando sistema de threading...")
        self.threading_manager = LunaThreadingManager(app=self)

        if self.ouvido:
            device_id = config.AUDIO_CONFIG.get("DEVICE_ID", 0)
            logger.info(f"Inicializando captura de audio no device: {device_id}")

            self.threading_manager.register_thread(
                "audio_capture",
                AudioCaptureThread(self.threading_manager, config.AUDIO_CONFIG, device_index=device_id, app=self),
            )

            if config.WAKE_WORD_ENABLED:
                self.threading_manager.register_thread(
                    "wake_word",
                    WakeWordThread(
                        threading_manager=self.threading_manager,
                        on_wake=self._handle_wake_word,
                        shutdown_event=self.threading_manager.shutdown_event,
                        sample_rate=config.AUDIO_CONFIG.get("SAMPLE_RATE", 16000),
                    ),
                )
                logger.info("Wake word detection ativado")

            if self.em_chamada:
                self.threading_manager.listening_event.set()

        self.threading_manager.register_thread(
            "transcription", TranscriptionThread(self.threading_manager, config.WHISPER_CONFIG, config.VAD_CONFIG)
        )

        self.threading_manager.register_thread("processing", ProcessingThread(self.threading_manager, self.consciencia))

        self.threading_manager.register_thread("coordinator", CoordinatorThread(self.threading_manager, self))

        self.threading_manager.register_thread(
            "animation", AnimationThread(self.threading_manager, self.animation_controller, self)
        )

        if self.boca:
            self.threading_manager.register_thread("tts", TTSThread(self.threading_manager, self.boca))

            self.threading_manager.register_thread("tts_playback", TTSPlaybackThread(self.threading_manager, self.boca))

        self.threading_manager.register_thread("monitor", MonitorThread(self.threading_manager))

        self.threading_manager.start_all_threads()
        logger.info("Sistema de threading iniciado.")

    def _handle_wake_word(self: "TemploDaAlma", greeting: str) -> None:
        from textual.widgets import Button

        logger.info(f"[WAKE_WORD] Detectado! Resposta: {greeting}")

        if self.daemon and self.daemon.is_hidden:
            self.daemon._show_app()
            from src.core.entity_loader import get_active_entity, get_entity_name

            entity_name = get_entity_name(get_active_entity())
            self.daemon.notify(entity_name, greeting)

        self.threading_manager.listening_event.set()

        if not self.em_chamada:
            self.em_chamada = True
            try:
                btn = self.query_one("#toggle_voice_call", Button)
                btn.label = "[Desativar Voz]"
                btn.remove_class("voice-inactive")
                btn.add_class("voice-active")
            except Exception as e:
                logger.debug(f"Erro ao atualizar botao de voz: {e}")

        try:
            self.call_from_thread(self.add_chat_entry, greeting, False)
            self.call_from_thread(self.run_animation, "curiosa")
        except Exception as e:
            logger.debug(f"[WAKE_WORD] Erro ao atualizar UI: {e}")

        if self.boca:
            tts_chunk = TTSChunk(
                audio_data=greeting.encode("utf-8"),
                chunk_index=0,
                total_chunks=1,
            )
            tts_chunk.text = greeting
            tts_chunk.metatags = {"speed": 1.0, "stability": 0.5, "style": 0.3}
            try:
                self.threading_manager.tts_queue.put(tts_chunk, timeout=1.0)
            except Exception as e:
                logger.debug(f"Erro ao enfileirar TTS: {e}")
