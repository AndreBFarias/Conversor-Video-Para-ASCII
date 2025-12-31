import logging
import re
from typing import TYPE_CHECKING

from src.core.ambient_presence import get_ambient_presence
from src.core.event_logger import EventType, get_event_logger
from src.ui.banner import run_processing_static

if TYPE_CHECKING:
    from .luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class EventHandlerMixin:
    def on_key(self: "TemploDaAlma", event) -> None:
        focused_id = self.focused.id if self.focused else "None"
        focused_type = type(self.focused).__name__ if self.focused else "None"
        logger.info(f"[TECLA] {event.key} | Foco: {focused_type}#{focused_id}")

    def on_multiline_input_submitted(self: "TemploDaAlma", event) -> None:
        self._process_user_input(event.value)

    async def on_input_submitted(self: "TemploDaAlma", event) -> None:
        self._process_user_input(event.value)

    def _process_user_input(self: "TemploDaAlma", user_input: str) -> None:
        if not user_input.strip():
            return

        ambient = get_ambient_presence()
        if ambient:
            ambient.record_activity()

        if self.is_speaking or (
            hasattr(self, "threading_manager") and self.threading_manager.luna_speaking_event.is_set()
        ):
            self._interrupt_luna("texto digitado")

        forced_animation = None
        reaction_pattern = re.compile(r"/(rea[cç]?[aã]?o?|react)\s+(Luna_\w+)", re.IGNORECASE)
        match = reaction_pattern.search(user_input)
        if match:
            forced_animation = match.group(2)
            user_input = reaction_pattern.sub("", user_input).strip()
            logger.info(f"Reacao forcada detectada: {forced_animation}")

        keyboard_pattern = re.compile(r"^/(teclado|keyboard|key)$", re.IGNORECASE)
        if keyboard_pattern.match(user_input.strip()):
            self.query_one("#main_input").value = ""
            self._show_keyboard_help()
            return

        commands_pattern = re.compile(r"^/(comandos|commands|help)$", re.IGNORECASE)
        if commands_pattern.match(user_input.strip()):
            self.query_one("#main_input").value = ""
            self._show_commands_help()
            return

        user_filter_pattern = re.compile(r"^/user\s+(\S+)$", re.IGNORECASE)
        user_match = user_filter_pattern.match(user_input.strip())
        if user_match:
            self.query_one("#main_input").value = ""
            self._filter_messages_by_role(user_match.group(1))
            return

        logger.info("INPUT TEXTO")
        logger.info(f"Usuario digitou: '{user_input}'")

        self.query_one("#main_input").value = ""
        self.add_chat_entry("user", user_input)

        if hasattr(self, "onboarding"):
            if self.onboarding and self.onboarding.input_future and not self.onboarding.input_future.done():
                self.onboarding.handle_text_input(user_input)
                return

        if self.app_state == "BUSY":
            self.add_chat_entry("kernel", "Ocupado... aguarde.")
            return

        self.app_state = "BUSY"

        self.run_worker(run_processing_static(self, on=True), exclusive=False, thread=False)

        try:
            status_label = self.query_one("#status-label")
            if hasattr(status_label, "set_text"):
                status_label.set_text("Processando...", animate=True)
            else:
                status_label.update("Processando...")

            emotion_label = self.query_one("#emotion-label")
            if hasattr(emotion_label, "start_chaos_mode"):
                emotion_label.start_chaos_mode()
        except Exception as e:
            logger.debug(f"Erro ao atualizar UI de processamento: {e}")

        self.submit_interaction(
            user_input,
            attached_content=self.attached_file_content,
            already_in_chat=True,
            forced_animation=forced_animation,
        )

        self.file_handler.clear_attachments()

    def on_button_pressed(self: "TemploDaAlma", event) -> None:
        evt_logger = get_event_logger()
        evt_logger.click("button", event.button.id, {"state": self.app_state})

        logger.info(f"Usuario clicou no botao: {event.button.id}")

        onboarding_active = hasattr(self, "onboarding") and getattr(self.onboarding, "is_running", False)
        onboarding_waiting_for = getattr(self.onboarding, "waiting_for_button", None) if onboarding_active else None

        allowed_when_busy = ["toggle_voice_call", "quit"]
        if onboarding_active and onboarding_waiting_for:
            allowed_when_busy.append(onboarding_waiting_for)

        if self.app_state != "IDLE" and event.button.id not in allowed_when_busy:
            evt_logger.log(
                EventType.CLICK, "button", event.button.id, {"blocked": True, "reason": "BUSY"}, success=False
            )
            logger.warning(f"Acao '{event.button.id}' bloqueada: App esta BUSY.")
            return

        if event.button.id == "toggle_voice_call":
            if onboarding_active:
                self.onboarding.handle_button_click(event.button.id)
            self.run_worker(self.action_toggle_voice_call(), exclusive=False, thread=False)
            return

        if event.button.id == "olhar":
            if onboarding_active:
                self.onboarding.handle_button_click(event.button.id)
            self.call_later(self.action_olhar)
            return

        if onboarding_active:
            if self.onboarding.handle_button_click(event.button.id):
                return

        action_map = {
            "nova_conversa": self.action_nova_conversa,
            "ver_historico": self.action_ver_historico,
            "editar_alma": self.action_editar_alma,
            "olhar": self.action_olhar,
            "canone": self.action_canone,
            "quit": self.action_quit,
            "attach_file": self.action_attach_file,
        }
        action = action_map.get(event.button.id)
        if action:
            self.call_later(action)

    def _is_luna_speaking(self: "TemploDaAlma") -> bool:
        return hasattr(self, "threading_manager") and self.threading_manager.luna_speaking_event.is_set()

    def _is_onboarding_active(self: "TemploDaAlma") -> bool:
        return hasattr(self, "onboarding") and getattr(self.onboarding, "is_running", False)
