import logging
from typing import TYPE_CHECKING

from src.core.event_logger import get_event_logger
from src.ui.banner import run_voice_toggle_transition

if TYPE_CHECKING:
    from ..luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class VoiceActionsMixin:
    def watch_em_chamada(self: "TemploDaAlma", em_chamada: bool) -> None:
        toggle_button = self.query_one("#toggle_voice_call")
        main_input = self.query_one("#main_input")

        if em_chamada:
            if not self.ouvido:
                logger.error("Tentativa de iniciar chamada de voz sem modulo de audicao.")
                self.em_chamada = False
                return

            toggle_button.remove_class("voice-inactive")
            toggle_button.add_class("voice-active")

            if toggle_button.tooltip:
                toggle_button.tooltip = "Desativar chamada de voz"

            main_input.placeholder = "Ouvindo sua melodia... (pode digitar tambem)"
            logger.info("Chamada de voz ATIVADA")

            self.run_worker(run_voice_toggle_transition(self, activating=True), exclusive=False, thread=False)

            if hasattr(self, "threading_manager"):
                self.threading_manager.listening_event.set()
                self.threading_manager.user_speaking_event.clear()

            if hasattr(self, "daemon") and self.daemon and self.daemon.tray:
                self.daemon.tray.update_voice_state(True)
        else:
            toggle_button.remove_class("voice-active")
            toggle_button.add_class("voice-inactive")

            if toggle_button.tooltip:
                toggle_button.tooltip = "Ativar chamada de voz"

            main_input.disabled = False
            main_input.placeholder = "Sua proxima fala..."
            logger.info("Chamada de voz DESATIVADA")

            self.run_worker(run_voice_toggle_transition(self, activating=False), exclusive=False, thread=False)

            if hasattr(self, "threading_manager"):
                self.threading_manager.listening_event.clear()

            if hasattr(self, "daemon") and self.daemon and self.daemon.tray:
                self.daemon.tray.update_voice_state(False)

    async def action_toggle_voice_call(self: "TemploDaAlma") -> None:
        evt_logger = get_event_logger()

        if not self.ouvido:
            evt_logger.voice("toggle", success=False, error_msg="modulo_audicao_indisponivel")
            logger.error("Tentativa de alternar chamada de voz sem modulo de audicao.")
            self.notify(
                "Modulo de audicao nao disponivel. Verifique se o Whisper esta instalado.", severity="error", timeout=5
            )
            self.add_chat_entry(
                "kernel", "Erro: Modulo de audicao nao esta disponivel. Instale: pip install faster-whisper"
            )
            if self.em_chamada:
                self.em_chamada = False
            return

        novo_estado = not self.em_chamada
        evt_logger.state("voice", "on" if self.em_chamada else "off", "on" if novo_estado else "off")
        logger.info(f"Alternando chamada de voz: {self.em_chamada} -> {novo_estado}")

        if novo_estado:
            evt_logger.voice("activated", success=True)
            self.notify("Chamada de voz ATIVADA - Luna esta ouvindo e falando", severity="information", timeout=3)
        else:
            evt_logger.voice("deactivated", success=True)
            self.notify("Chamada de voz DESATIVADA", severity="information", timeout=2)

        self.em_chamada = novo_estado

    def _interrupt_luna(self: "TemploDaAlma", reason: str = "usuario") -> None:
        logger.info(f"[INTERRUPT] Interrompendo Luna: {reason}")

        if self.boca:
            self.boca.parar()
        self.is_speaking = False

        if hasattr(self, "threading_manager"):
            self.threading_manager.luna_speaking_event.clear()
            try:
                while not self.threading_manager.tts_queue.empty():
                    self.threading_manager.tts_queue.get_nowait()
                while not self.threading_manager.tts_playback_queue.empty():
                    self.threading_manager.tts_playback_queue.get_nowait()
                logger.info("[INTERRUPT] Filas TTS limpas")
            except Exception as e:
                logger.warning(f"[INTERRUPT] Erro ao limpar filas: {e}")
