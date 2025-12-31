import logging
import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

import config
from src.soul.personalidade import get_personalidade
from src.ui import CanoneScreen, HistoryScreen, MultilineInput
from src.ui.banner import run_shutdown_sequence

if TYPE_CHECKING:
    from ..luna_app import TemploDaAlma

logger = logging.getLogger(__name__)

GEMINI_ERROR = None


def set_gemini_error(error: str) -> None:
    global GEMINI_ERROR
    GEMINI_ERROR = error


def get_gemini_error() -> str:
    return GEMINI_ERROR


class MenuActionsMixin:
    async def action_nova_conversa(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            return
        logger.info("Iniciando nova conversa...")
        await self.session_manager.save_current_session(GEMINI_ERROR)
        self.current_session_id = None
        self.session_manager.reset_message_count()
        self.file_handler.clear_attachments()
        chat_list = self.query_one("#chat-list")
        await chat_list.remove_children()
        self.conversation_history = []
        personalidade = get_personalidade()

        placeholder_frase = personalidade.obter_frase("placeholder_input")
        try:
            main_input = self.query_one("#main_input", MultilineInput)
            main_input.placeholder = placeholder_frase
        except Exception as e:
            logger.debug(f"Erro ao atualizar placeholder: {e}")

        if not GEMINI_ERROR:
            self.add_chat_entry("luna", personalidade.obter_frase("saudacao_inicial"))
        else:
            self.add_chat_entry("kernel", f"AVISO: {GEMINI_ERROR}")
            self.add_chat_entry("luna", personalidade.obter_frase("modo_offline"))
        self.run_animation("observando")
        self.query_one("#main_input").focus()

    async def action_ver_historico(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            return
        logger.info("Abrindo historico...")
        await self.session_manager.save_current_session(GEMINI_ERROR)

        def check_selection(session_id):
            if session_id:
                logger.info(f"Carregando sessao: {session_id}")
                self.session_manager.load_session(session_id)

        self.push_screen(HistoryScreen(), check_selection)

    async def action_editar_alma(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            return
        logger.info("Tentando abrir arquivo da alma para edicao...")
        try:
            from src.core.entity_loader import EntityLoader, get_active_entity

            entity_id = get_active_entity()
            loader = EntityLoader(entity_id)
            soul_path = loader.entity_data.get("soul_path")

            if not soul_path or not soul_path.exists():
                logger.error(f"Arquivo da alma nao encontrado para {entity_id}")
                self.add_chat_entry("kernel", f"Erro: Arquivo da alma de {entity_id} nao encontrado.")
                return

            soul_path_str = str(soul_path)
            if sys.platform == "win32":
                os.startfile(soul_path_str)
            elif sys.platform == "darwin":
                subprocess.run(["open", soul_path_str], check=True)
            else:
                subprocess.run(["xdg-open", soul_path_str], check=True)
        except FileNotFoundError:
            logger.error("Erro: Comando 'xdg-open' (ou 'open') nao encontrado.")
            self.add_chat_entry("kernel", "Erro: Comando para abrir arquivo nao encontrado.")
        except Exception as e:
            logger.error(f"Nao foi possivel abrir o arquivo da alma: {e}", exc_info=True)
            self.add_chat_entry("kernel", f"Nao foi possivel abrir o arquivo da alma: {e}")

    async def action_canone(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            return
        logger.info("Abrindo Canone (configuracoes)...")
        self.push_screen(CanoneScreen())

    async def action_quit(self: "TemploDaAlma") -> None:
        if self.daemon and self.daemon.is_initialized and config.DAEMON_MODE:
            now = time.time()
            if hasattr(self, "_last_quit_click") and (now - self._last_quit_click) < 1.5:
                logger.info("Duplo clique em Requiem - fechando de verdade")
                await self.action_force_quit()
                return

            self._last_quit_click = now
            logger.info("Minimizando para tray (clique duplo para fechar)")
            self.notify("Clique duplo para encerrar", timeout=2)
            self.daemon._hide_app()

            if self.daemon.tray:
                from src.core.entity_loader import get_active_entity, get_entity_name

                entity_name = get_entity_name(get_active_entity())
                self.daemon.tray.notify(entity_name, "Minimizada para o tray")
            return

        await self.action_force_quit()

    async def action_force_quit(self: "TemploDaAlma") -> None:
        logger.info("Saindo da aplicacao...")

        if hasattr(self, "onboarding") and self.onboarding.is_running:
            logger.info("Cancelando onboarding ativo...")
            self.onboarding.is_running = False

        if self.em_chamada:
            self.em_chamada = False

        if self.is_looping_olhar and self.olhar_timer:
            self.is_looping_olhar = False
            try:
                self.olhar_timer.stop()
            except Exception as e:
                logger.debug(f"Erro ao parar olhar timer: {e}")

        if self.boca:
            self.boca.parar()

        if self.daemon:
            logger.info("Encerrando daemon...")
            self.daemon.shutdown()

        if self.desktop_integration:
            logger.info("Encerrando desktop integration...")
            self.desktop_integration.stop()

        logger.info("Executando sequencia de shutdown...")
        await run_shutdown_sequence(self, duration=1.2)

        if hasattr(self, "threading_manager"):
            logger.info("Parando listening...")
            self.threading_manager.listening_event.clear()

            logger.info("Parando sistema de threading...")
            self.threading_manager.stop_all_threads(timeout=3.0)

        if self.ouvido:
            try:
                logger.info("Fechando ouvido...")
                self.ouvido.close()
            except Exception as e:
                logger.error(f"Erro ao fechar ouvido: {e}")

        if self.visao:
            try:
                logger.info("Liberando visao...")
                self.visao.release()
            except Exception as e:
                logger.error(f"Erro ao liberar visao: {e}")

        logger.info("Ate logo!")
        self.exit()

    async def action_attach_file(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            return
        logger.info("Iniciando fluxo de anexo...")
        await self.file_handler.handle_attachment()

    def action_voltar(self: "TemploDaAlma") -> None:
        now = time.time()

        if self.screen.is_modal:
            self.pop_screen()
            logger.debug("Modal fechado via Escape")
            self._last_esc_time = 0
            return

        if len(self.screen_stack) > 1:
            self.pop_screen()
            logger.debug("Tela anterior restaurada via Escape")
            self._last_esc_time = 0
            return

        if now - self._last_esc_time < self._esc_double_threshold:
            logger.info("Esc duplo detectado - encerrando aplicacao")
            self._last_esc_time = 0
            self.call_later(self.action_quit)
            return

        self._last_esc_time = now

        if self.app_state == "BUSY":
            logger.info("Cancelamento solicitado durante processamento")
            self.notify("Processando... aguarde", timeout=2)
        else:
            self.notify("Pressione Esc novamente para sair", timeout=1)
