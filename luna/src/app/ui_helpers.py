import json
import logging
import threading
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from .luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class UIHelpersMixin:
    def get_user_name(self: "TemploDaAlma") -> str:
        try:
            profile_path = config.APP_DIR / "src" / "data_memory" / "user" / "profile.json"
            if profile_path.exists():
                with open(profile_path, encoding="utf-8") as f:
                    profile = json.load(f)
                return profile.get("nome", "Viajante")
        except Exception as e:
            logger.debug(f"Erro ao carregar nome do usuario: {e}")
        return "Viajante"

    def _apply_entity_styles_inline(self: "TemploDaAlma", entity_id: str) -> None:
        try:
            from src.core.entity_loader import EntityLoader

            loader = EntityLoader(entity_id)
            theme = loader.get_full_color_theme()
            if not theme:
                logger.warning(f"Tema nao encontrado para {entity_id}")
                return

            background = theme.get("background", "#282a36")
            border_color = theme.get("border_color", theme.get("text_secondary", "#6272a4"))

            elements_with_border = ["#ascii-container", "#menu-pane", "#chat-area", "#input-container"]

            for selector in elements_with_border:
                try:
                    element = self.query_one(selector)
                    element.styles.background = background
                    element.styles.border = ("heavy", border_color)
                except Exception as e:
                    logger.debug(f"Nao foi possivel aplicar estilo em {selector}: {e}")

            elements_with_background = ["#right-pane", "#welcome-pane", "#chat-list", "#status-area"]

            for selector in elements_with_background:
                try:
                    element = self.query_one(selector)
                    element.styles.background = background
                except Exception as e:
                    logger.debug(f"Nao foi possivel aplicar background em {selector}: {e}")

            self.screen.styles.background = background
            logger.info(f"Estilos inline aplicados para {entity_id}: bg={background}, border={border_color}")

        except Exception as e:
            logger.error(f"Erro ao aplicar estilos inline: {e}")

    def _safe_ui_call(self: "TemploDaAlma", func, *args) -> None:
        if threading.current_thread() is threading.main_thread():
            func(*args)
        else:
            self.call_from_thread(func, *args)

    def _show_keyboard_help(self: "TemploDaAlma") -> None:
        help_text = """Navegacao por Teclado

Tab .............. Proximo elemento focavel
Shift+Tab ........ Elemento anterior
Enter ............ Ativar botao/enviar
Escape ........... Voltar (2x para sair)

Atalhos Globais:
Ctrl+Q ........... Sair
Ctrl+T / F5 ...... Nova conversa
Ctrl+H ........... Historico
Ctrl+E ........... Editar alma

Texto:
Ctrl+C ........... Copiar
Ctrl+V ........... Colar
Ctrl+A ........... Selecionar tudo

O foco atual e indicado por fundo roxo e borda rosa."""
        self.add_chat_entry("kernel", help_text)

    def _show_commands_help(self: "TemploDaAlma") -> None:
        help_text = """Comandos Disponiveis

/teclado ......... Guia de navegacao por teclado
/keyboard ........ Alias para /teclado
/key ............. Alias para /teclado

/user luna ....... Mostra apenas mensagens da Luna
/user [nome] ..... Mostra apenas mensagens do usuario
/user kernel ..... Mostra apenas mensagens do sistema
/user code ....... Mostra apenas blocos de codigo
/user all ........ Mostra todas as mensagens

/comandos ........ Este sumario
/commands ........ Alias para /comandos
/help ............ Alias para /comandos

/reacao Luna_X ... Forca animacao especifica na resposta
                   Ex: /reacao Luna_feliz como vai?

Atalhos de Menu:
Confissao ........ Nova conversa (Ctrl+T)
Relicario ........ Historico de conversas (Ctrl+H)
Custodia ......... Editar alma da Luna (Ctrl+E)
Ver .............. Captura visual (webcam)
Canone ........... Configuracoes
Requiem .......... Encerrar (Ctrl+Q)"""
        self.add_chat_entry("kernel", help_text)

    def _filter_messages_by_role(self: "TemploDaAlma", role_filter: str) -> None:
        from src.ui import ChatMessage

        role_filter = role_filter.lower().strip()

        role_map = {
            "luna": "luna",
            "user": "user",
            "usuario": "user",
            "kernel": "kernel",
            "sistema": "kernel",
            "system": "kernel",
            "code": "code",
            "codigo": "code",
            "all": None,
            "todos": None,
            "tudo": None,
        }

        target_role = role_map.get(role_filter)

        if role_filter not in role_map and role_filter:
            target_role = "user"
            user_name_filter = role_filter
        else:
            user_name_filter = None

        try:
            chat_list = self.query_one("#chat-list")
            messages = chat_list.query(ChatMessage)

            visible_count = 0
            hidden_count = 0

            for msg in messages:
                if target_role is None:
                    msg.remove_class("filtered-hidden")
                    msg.styles.display = "block"
                    visible_count += 1
                elif msg.role == target_role:
                    if user_name_filter and msg.role == "user":
                        if (
                            hasattr(msg, "user_name")
                            and msg.user_name
                            and user_name_filter.lower() in msg.user_name.lower()
                        ):
                            msg.remove_class("filtered-hidden")
                            msg.styles.display = "block"
                            visible_count += 1
                        else:
                            msg.add_class("filtered-hidden")
                            msg.styles.display = "none"
                            hidden_count += 1
                    else:
                        msg.remove_class("filtered-hidden")
                        msg.styles.display = "block"
                        visible_count += 1
                else:
                    msg.add_class("filtered-hidden")
                    msg.styles.display = "none"
                    hidden_count += 1

            if target_role is None:
                self.add_chat_entry("kernel", f"Filtro removido. {visible_count} mensagens visiveis.")
            else:
                display_role = role_filter if not user_name_filter else user_name_filter
                self.add_chat_entry(
                    "kernel", f"Filtro: {display_role}. {visible_count} visiveis, {hidden_count} ocultas."
                )

        except Exception as e:
            logger.error(f"Erro ao filtrar mensagens: {e}")
            self.add_chat_entry("kernel", f"Erro ao filtrar: {e}")

    def hide_ui_for_onboarding(self: "TemploDaAlma") -> None:
        try:

            def do_hide():
                self.query_one("#menu-pane").add_class("hidden")
                self.query_one("#attach_file").add_class("hidden")
                self.query_one("#toggle_voice_call").add_class("hidden")

            self._safe_ui_call(do_hide)
            logger.info("UI oculta para Onboarding (Ato I)")
        except Exception as e:
            logger.error(f"Erro ao ocultar UI: {e}")

    def reveal_voice_button(self: "TemploDaAlma") -> None:
        try:

            def do_reveal():
                self.query_one("#toggle_voice_call").remove_class("hidden")

            self._safe_ui_call(do_reveal)
        except Exception as e:
            logger.error(f"Erro ao revelar botao de voz: {e}")

    def reveal_menu(self: "TemploDaAlma") -> None:
        try:

            def do_reveal():
                self.query_one("#menu-pane").remove_class("hidden")

            self._safe_ui_call(do_reveal)
            logger.info("Menu lateral revelado")
        except Exception as e:
            logger.error(f"Erro ao revelar menu: {e}")

    def reveal_capabilities(self: "TemploDaAlma") -> None:
        try:

            def do_reveal():
                self.query_one("#attach_file").remove_class("hidden")
                self.query_one("#toggle_voice_call").remove_class("hidden")

            self._safe_ui_call(do_reveal)
            logger.info("Capacidades reveladas")
        except Exception as e:
            logger.error(f"Erro ao revelar capacidades: {e}")
