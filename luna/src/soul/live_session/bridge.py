from __future__ import annotations

import logging
import queue
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.soul.live_session.client import LunaLiveSession

logger = logging.getLogger(__name__)


class LiveAudioBridge:
    def __init__(self, live_session: "LunaLiveSession", audio_queue: queue.Queue, sample_rate: int = 16000):
        self.session = live_session
        self.audio_queue = audio_queue
        self.sample_rate = sample_rate

        self._running = False
        self._bridge_thread: threading.Thread | None = None
        self._user_speaking = threading.Event()

        logger.info("LiveAudioBridge inicializada")

    def start(self):
        if self._running:
            return

        self._running = True
        self._bridge_thread = threading.Thread(target=self._bridge_loop, daemon=True)
        self._bridge_thread.start()
        logger.info("LiveAudioBridge iniciada")

    def stop(self):
        self._running = False
        if self._bridge_thread:
            self._bridge_thread.join(timeout=2)
        logger.info("LiveAudioBridge parada")

    def notify_user_speaking(self, is_speaking: bool):
        from src.soul.live_session.handlers import interrupt

        if is_speaking:
            self._user_speaking.set()
            if self.session.is_speaking:
                interrupt(self.session)
        else:
            self._user_speaking.clear()

    def _bridge_loop(self):
        from src.soul.live_session.handlers import send_audio

        while self._running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)

                if hasattr(audio_chunk, "data"):
                    audio_data = audio_chunk.data
                elif isinstance(audio_chunk, bytes):
                    audio_data = audio_chunk
                else:
                    continue

                send_audio(self.session, audio_data, self.sample_rate)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro no bridge: {e}")
