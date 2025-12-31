import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import TemploDaAlma

logger = logging.getLogger(__name__)


class AudioController:
    def __init__(self, app: "TemploDaAlma"):
        self.app = app
        self._em_chamada: bool = False
        self._wake_word_enabled: bool = True
        self._recording: bool = False

    @property
    def em_chamada(self) -> bool:
        return self._em_chamada

    @em_chamada.setter
    def em_chamada(self, value: bool):
        self._em_chamada = value
        logger.info(f"Modo chamada: {value}")
        self._update_ui_state()

    def _update_ui_state(self):
        if hasattr(self.app, "ui_controller"):
            status = "Em chamada" if self._em_chamada else "Aguardando"
            self.app.ui_controller.update_status(status)

    def toggle_voice_mode(self) -> bool:
        self.em_chamada = not self.em_chamada
        return self.em_chamada

    def start_recording(self):
        if self._recording:
            return

        self._recording = True
        if hasattr(self.app, "threading_controller"):
            audio_thread = self.app.threading_controller._threads.get("audio_capture")
            if audio_thread:
                audio_thread.start_capture()

        logger.info("Gravacao iniciada")

    def stop_recording(self):
        if not self._recording:
            return

        self._recording = False
        if hasattr(self.app, "threading_controller"):
            audio_thread = self.app.threading_controller._threads.get("audio_capture")
            if audio_thread:
                audio_thread.stop_capture()

        logger.info("Gravacao parada")

    def enable_wake_word(self, enable: bool = True):
        self._wake_word_enabled = enable
        logger.info(f"Wake word: {enable}")

    def is_recording(self) -> bool:
        return self._recording
