import asyncio
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from main import TemploDaAlma

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class UIController:
    def __init__(self, app: "TemploDaAlma"):
        self.app = app
        self._bindings_registered = False

    def get_widget(self, selector: str, widget_type=None):
        try:
            if widget_type:
                return self.app.query_one(selector, widget_type)
            return self.app.query_one(selector)
        except Exception:
            return None

    def update_chat_panel(self, content: str, append: bool = True):
        chat = self.get_widget("#chat-history", Static)
        if not chat:
            return

        if append:
            current = chat.renderable or ""
            chat.update(f"{current}\n{content}")
        else:
            chat.update(content)

    def update_status(self, status: str):
        status_widget = self.get_widget("#status-label", Static)
        if status_widget:
            status_widget.update(status)

    def update_emotion_label(self, emotion: str, entity_name: str = "Luna"):
        label = self.get_widget("#emotion-label", Static)
        if label:
            label.update(f"[{entity_name} esta {emotion}]")

    def clear_input(self):
        from src.ui.multiline_input import MultilineInput

        main_input = self.get_widget("#main_input", MultilineInput)
        if main_input:
            main_input.clear()

    def set_input_placeholder(self, text: str):
        from src.ui.multiline_input import MultilineInput

        main_input = self.get_widget("#main_input", MultilineInput)
        if main_input:
            main_input.placeholder = text

    def toggle_fullscreen_ascii(self, enable: bool):
        ascii_pane = self.get_widget("#ascii-pane")
        if not ascii_pane:
            return

        if enable:
            ascii_pane.add_class("fullscreen")
        else:
            ascii_pane.remove_class("fullscreen")

    def show_notification(self, message: str, severity: str = "information"):
        self.app.notify(message, severity=severity)

    def hide_for_onboarding(self):
        selectors = ["#chat-history", "#main_input", "#voice-button", "#status-label", "#metrics-label"]
        for sel in selectors:
            widget = self.get_widget(sel)
            if widget:
                widget.add_class("hidden-onboarding")

    def show_after_onboarding(self):
        selectors = ["#chat-history", "#main_input", "#voice-button", "#status-label", "#metrics-label"]
        for sel in selectors:
            widget = self.get_widget(sel)
            if widget:
                widget.remove_class("hidden-onboarding")

    async def stream_to_chat(
        self, response_generator: Generator, prefix: str = "", on_complete: Callable[[dict], None] | None = None
    ) -> dict:
        """
        Exibe resposta em streaming no chat panel.

        Args:
            response_generator: Generator que yield (chunk, is_final, parsed_data)
            prefix: Prefixo para exibir antes da resposta (ex: nome da entidade)
            on_complete: Callback chamado quando streaming termina

        Returns:
            dict com resposta parseada final
        """
        chat = self.get_widget("#chat-history", Static)
        if not chat:
            logger.warning("Chat widget nao encontrado para streaming")
            return {}

        buffer = prefix
        parsed_data = {}

        try:
            for chunk, is_final, data in response_generator:
                if chunk:
                    buffer += chunk
                    chat.update(buffer)
                    await asyncio.sleep(0.01)

                if is_final and data:
                    parsed_data = data
                    if "log_terminal" in data:
                        chat.update(f"{prefix}{data['log_terminal']}")
                    break

            if on_complete and parsed_data:
                on_complete(parsed_data)

        except Exception as e:
            logger.error(f"Erro no streaming para chat: {e}")
            chat.update(f"{prefix}[Erro no streaming: {str(e)[:50]}]")

        return parsed_data

    def stream_to_chat_sync(self, response_generator: Generator, prefix: str = "") -> dict:
        """
        Versao sincrona do stream_to_chat.
        Usa call_later do Textual para updates.
        """
        chat = self.get_widget("#chat-history", Static)
        if not chat:
            return {}

        buffer = prefix
        parsed_data = {}

        try:
            for chunk, is_final, data in response_generator:
                if chunk:
                    buffer += chunk
                    self.app.call_later(lambda b=buffer: chat.update(b))

                if is_final and data:
                    parsed_data = data
                    if "log_terminal" in data:
                        final_content = f"{prefix}{data['log_terminal']}"
                        self.app.call_later(lambda c=final_content: chat.update(c))
                    break

        except Exception as e:
            logger.error(f"Erro no streaming sync: {e}")

        return parsed_data
