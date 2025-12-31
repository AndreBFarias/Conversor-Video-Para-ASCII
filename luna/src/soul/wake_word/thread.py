import logging
import time
from collections.abc import Callable
from threading import Event, Thread

import numpy as np

from .detector import WakeWordDetector

logger = logging.getLogger(__name__)


class WakeWordThread(Thread):
    def __init__(
        self,
        threading_manager,
        on_wake: Callable[[str], None],
        shutdown_event: Event,
        sample_rate: int = 16000,
        whisper_model=None,
    ):
        super().__init__(name="WakeWordThread", daemon=True)
        self.manager = threading_manager
        self.on_wake = on_wake
        self.shutdown_event = shutdown_event
        self.sample_rate = sample_rate
        self.whisper_model = whisper_model

        self.detector = WakeWordDetector(sample_rate=sample_rate)
        self._active = True
        self._paused = True
        self._enabled = False

    def enable(self):
        self._enabled = True
        self._paused = False
        logger.info("[WAKE_WORD] Habilitado via daemon")

    def disable(self):
        self._enabled = False
        self._paused = True
        self.detector.reset()
        logger.info("[WAKE_WORD] Desabilitado")

    def toggle(self) -> bool:
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def run(self):
        logger.info("[WAKE_WORD] Iniciando thread (modo daemon)...")

        if not self.detector.load_model(whisper_model=self.whisper_model):
            logger.error("[WAKE_WORD] Falha ao carregar modelo. Thread encerrada.")
            return

        logger.info("[WAKE_WORD] Aguardando audio_ready_event...")
        audio_ready = self.manager.audio_ready_event.wait(timeout=60)
        if not audio_ready:
            logger.error("[WAKE_WORD] Timeout aguardando audio_ready_event")
        logger.info("[WAKE_WORD] Thread pronta, aguardando ativacao via daemon...")

        chunks_received = 0
        chunks_processed = 0
        last_log_time = time.time()

        while not self.shutdown_event.is_set():
            try:
                now = time.time()
                if now - last_log_time > 30.0:
                    queue_size = (
                        self.manager.wake_word_queue.qsize() if hasattr(self.manager, "wake_word_queue") else -1
                    )
                    logger.debug(
                        f"[WAKE_WORD] Stats: enabled={self._enabled}, received={chunks_received}, processed={chunks_processed}, queue={queue_size}"
                    )
                    last_log_time = now

                if not self._enabled or self._paused:
                    time.sleep(0.1)
                    continue

                if self.manager.luna_speaking_event.is_set():
                    time.sleep(0.05)
                    continue

                if self.manager.listening_event.is_set():
                    time.sleep(0.05)
                    continue

                try:
                    chunk = self.manager.wake_word_queue.get(timeout=0.5)
                    chunks_received += 1
                except Exception:
                    continue

                if chunk is None or not hasattr(chunk, "data"):
                    continue

                chunks_processed += 1
                audio_data = chunk.data

                if isinstance(audio_data, (list, tuple)):
                    audio_data = np.array(audio_data, dtype=np.int16).tobytes()
                elif hasattr(audio_data, "tobytes"):
                    audio_data = audio_data.tobytes()

                detected, transcript = self.detector.detect(audio_data)

                if detected:
                    logger.info(f"=== WAKE WORD ATIVADO: '{transcript}' ===")
                    greeting = self.detector.get_greeting()
                    self.on_wake(greeting)

            except Exception as e:
                if not self.shutdown_event.is_set():
                    logger.warning(f"[WAKE_WORD] Erro no loop: {e}")
                time.sleep(0.1)

        logger.info("[WAKE_WORD] Thread encerrada")

    def pause(self):
        self._paused = True

    def resume(self):
        if self._enabled:
            self._paused = False
            self.detector.reset()

    def reload_for_entity(self, entity_id: str):
        self.detector.reload_patterns(entity_id)
