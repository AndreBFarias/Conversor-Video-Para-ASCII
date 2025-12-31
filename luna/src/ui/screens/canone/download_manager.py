from __future__ import annotations

import logging

from textual.widgets import Select

from src.soul.model_manager import get_model_manager
from src.ui.screens.base import DownloadModal

logger = logging.getLogger(__name__)


class DownloadManager:
    def __init__(self, screen):
        self._screen = screen
        self._model_manager = None
        self._download_queue = []
        self._download_total = 0
        self._download_current = 0
        self._download_modal = None
        self._on_complete_callback = None

    @property
    def model_manager(self):
        if self._model_manager is None:
            self._model_manager = get_model_manager()
        return self._model_manager

    def check_and_download(self, on_complete: callable) -> bool:
        self._on_complete_callback = on_complete

        try:
            self.model_manager.refresh_installed()
            models_to_download = []

            chat_provider = self._screen.query_one("#select-chat-provider", Select).value
            if chat_provider == "local":
                chat_model = self._screen.query_one("#select-chat-local-model", Select).value
                if chat_model and chat_model != Select.BLANK:
                    if not self.model_manager.is_installed(chat_model):
                        models_to_download.append(("chat", chat_model))

            vision_provider = self._screen.query_one("#select-vision-provider", Select).value
            if vision_provider == "local":
                vision_model = self._screen.query_one("#select-vision-local-model", Select).value
                if vision_model and vision_model != Select.BLANK:
                    if not self.model_manager.is_installed(vision_model):
                        models_to_download.append(("vision", vision_model))

            if models_to_download:
                self._start_download_queue(models_to_download)
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Erro ao verificar modelos: {e}")
            return False

    def _start_download_queue(self, models: list[tuple[str, str]]):
        self._download_queue = list(models)
        self._download_total = len(models)
        self._download_current = 0
        self._download_modal = None
        self._process_next_download()

    def _process_next_download(self):
        if not self._download_queue:
            if self._download_modal:
                self._download_modal.dismiss(True)
                self._download_modal = None
            if self._on_complete_callback:
                self._on_complete_callback()
            return

        self._download_current += 1
        category, model_name = self._download_queue.pop(0)

        if self._download_modal is None:
            self._download_modal = DownloadModal(
                model_name,
                on_complete=self._on_download_complete,
                current=self._download_current,
                total=self._download_total,
            )
            self._screen.app.push_screen(self._download_modal)
        else:
            self._screen.app.call_from_thread(self._download_modal.update_model, model_name, self._download_current)

        def on_progress(name, status):
            try:
                if self._download_modal and self._screen.app:
                    self._screen.app.call_from_thread(self._download_modal.update_progress, status)
            except Exception as e:
                logger.debug(f"Erro ao atualizar progresso: {e}")

        def on_complete(name, success, message):
            try:
                if success:
                    self._screen.app.call_from_thread(self._on_single_download_complete, name, True, message)
                else:
                    self._screen.app.call_from_thread(self._on_single_download_complete, name, False, message)
            except Exception as e:
                logger.error(f"Erro no callback de download: {e}")

        self.model_manager.download_model(model_name, on_progress, on_complete)

    def _on_single_download_complete(self, model_name: str, success: bool, message: str):
        if success:
            self._screen.notify(f"Modelo {model_name} instalado!", severity="information", timeout=2)
            self._process_next_download()
        else:
            self._screen.notify(f"Falha ao baixar {model_name}: {message}", severity="error", timeout=5)
            if self._download_modal:
                self._download_modal.dismiss(False)
                self._download_modal = None
            self._download_queue.clear()

    def _on_download_complete(self, success: bool, message: str):
        pass
