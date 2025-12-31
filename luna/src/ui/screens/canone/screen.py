from __future__ import annotations

import logging
import os
import shutil
import sys

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TabbedContent, TabPane

import config
from src.core.entity_loader import EntityLoader, get_active_entity, set_active_entity
from src.ui.entity_selector import EntitySelectorScreen
from src.ui.glitch_button import GlitchButton
from src.ui.screens.canone.download_manager import DownloadManager
from src.ui.screens.canone.helpers import EnvHelper
from src.ui.screens.canone.tabs import (
    compose_advanced_tab,
    compose_audio_tab,
    compose_effects_tab,
    compose_entity_tab,
    compose_keys_tab,
    compose_providers_tab,
    compose_voice_tab,
)

logger = logging.getLogger(__name__)


class CanoneScreen(ModalScreen):
    BINDINGS = [
        Binding(key="escape", action="dismiss", description="Fechar"),
        Binding(key="ctrl+s", action="save", description="Salvar"),
        Binding(key="tab", action="focus_next_field", description="Proximo Campo"),
        Binding(key="shift+tab", action="focus_prev_field", description="Campo Anterior"),
        Binding(key="ctrl+left", action="prev_tab", description="Aba Anterior"),
        Binding(key="ctrl+right", action="next_tab", description="Proxima Aba"),
        Binding(key="enter", action="focus_first_field", description="Entrar nos Campos"),
        Binding(key="1", action="goto_tab_1", description="Entidade"),
        Binding(key="2", action="goto_tab_2", description="Provedores"),
        Binding(key="3", action="goto_tab_3", description="Voz"),
        Binding(key="4", action="goto_tab_4", description="Audio"),
        Binding(key="5", action="goto_tab_5", description="Chaves"),
        Binding(key="6", action="goto_tab_6", description="Avancado"),
        Binding(key="7", action="goto_tab_7", description="Efeitos"),
        Binding(key="f2", action="save", description="Salvar (F2)"),
    ]

    TAB_IDS = ["tab-entity", "tab-providers", "tab-voice", "tab-audio", "tab-keys", "tab-advanced", "tab-effects"]

    PANE_FIELD_MAP = {
        "tab-entity": "#btn-change-entity",
        "tab-providers": "#select-chat-provider",
        "tab-voice": "#select-tts-engine",
        "tab-audio": "#input-audio-device",
        "tab-keys": "#input-google-key",
        "tab-advanced": "#input-ollama-url",
        "tab-effects": "#input-piscando-fps",
    }

    def __init__(self):
        super().__init__()
        self._env = EnvHelper()
        self._download_manager = DownloadManager(self)

    def _navigate_tab(self, direction: int) -> None:
        try:
            tabs = self.query_one("#canone-tabs", TabbedContent)
            if tabs.active in self.TAB_IDS:
                idx = self.TAB_IDS.index(tabs.active)
                tabs.active = self.TAB_IDS[(idx + direction) % len(self.TAB_IDS)]
        except Exception as e:
            logger.debug(f"Erro ao navegar aba: {e}")

    def action_prev_tab(self) -> None:
        self._navigate_tab(-1)

    def action_next_tab(self) -> None:
        self._navigate_tab(1)

    def action_goto_tab_1(self) -> None:
        self._goto_tab("tab-entity")

    def action_goto_tab_2(self) -> None:
        self._goto_tab("tab-providers")

    def action_goto_tab_3(self) -> None:
        self._goto_tab("tab-voice")

    def action_goto_tab_4(self) -> None:
        self._goto_tab("tab-audio")

    def action_goto_tab_5(self) -> None:
        self._goto_tab("tab-keys")

    def action_goto_tab_6(self) -> None:
        self._goto_tab("tab-advanced")

    def action_goto_tab_7(self) -> None:
        self._goto_tab("tab-effects")

    def _goto_tab(self, tab_id: str) -> None:
        try:
            self.query_one("#canone-tabs", TabbedContent).active = tab_id
        except Exception as e:
            logger.debug(f"Erro ao ir para aba {tab_id}: {e}")

    def action_focus_first_field(self) -> None:
        try:
            tabs = self.query_one("#canone-tabs", TabbedContent)
            first_field_id = self.PANE_FIELD_MAP.get(tabs.active, "#btn-change-entity")
            self.query_one(first_field_id).focus()
        except Exception as e:
            logger.debug(f"Erro ao focar primeiro campo: {e}")

    def action_focus_next_field(self) -> None:
        self._focus_field(1)

    def action_focus_prev_field(self) -> None:
        self._focus_field(-1)

    def _focus_field(self, direction: int) -> None:
        try:
            focusable = [w for w in self.query("Select, Input, Switch, Button") if w.can_focus and w.display]
            current = self.focused
            if current in focusable:
                idx = focusable.index(current)
                focusable[(idx + direction) % len(focusable)].focus()
            elif focusable:
                focusable[0 if direction > 0 else -1].focus()
        except Exception as e:
            logger.debug(f"Erro ao focar campo: {e}")

    def compose(self) -> ComposeResult:
        active_entity_id = get_active_entity()
        entity_loader = EntityLoader(active_entity_id)
        entity_config = entity_loader.get_config()
        primary_color = entity_loader.get_color_theme().get("primary_color", "#bd93f9")
        entity_name = entity_config.get("name", active_entity_id.capitalize())

        with Container(id="canone-overlay"):
            with Vertical(id="canone-modal"):
                yield Static(f"[bold {primary_color}]Canone do Espirito[/]", id="canone-title")
                yield Static("[dim]Controle total sobre a essencia[/dim]", id="canone-subtitle")

                with TabbedContent(id="canone-tabs"):
                    with TabPane("Entidade", id="tab-entity"):
                        yield from compose_entity_tab(entity_config, primary_color, entity_name)
                    with TabPane("Provedores", id="tab-providers"):
                        yield from compose_providers_tab(self._env)
                    with TabPane("Voz", id="tab-voice"):
                        yield from compose_voice_tab(self._env)
                    with TabPane("Audio", id="tab-audio"):
                        yield from compose_audio_tab(self._env)
                    with TabPane("Chaves", id="tab-keys"):
                        yield from compose_keys_tab(self._env)
                    with TabPane("Avancado", id="tab-advanced"):
                        yield from compose_advanced_tab(self._env)
                    with TabPane("Efeitos", id="tab-effects"):
                        yield from compose_effects_tab(self._env)

                with Horizontal(id="canone-buttons"):
                    yield GlitchButton("Fiat", id="btn-save-canone")
                    yield GlitchButton("Eterno Retorno", id="btn-cancel-canone")

    def action_dismiss(self) -> None:
        self.app.pop_screen()

    def action_save(self) -> None:
        self._save_settings()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-cancel-canone":
            self.app.pop_screen()
        elif event.button.id == "btn-save-canone":
            self._save_settings()
        elif event.button.id == "btn-change-entity":
            self._open_entity_selector()

    def _open_entity_selector(self):
        def on_entity_selected(selected_entity_id: str):
            if selected_entity_id and selected_entity_id != get_active_entity():
                self._change_entity(selected_entity_id)

        self.app.push_screen(EntitySelectorScreen(), on_entity_selected)

    def _change_entity(self, new_entity_id: str):
        try:
            old_entity_id = get_active_entity()
            if new_entity_id == old_entity_id:
                self.notify("Entidade ja esta ativa", severity="warning", timeout=3)
                return

            if not set_active_entity(new_entity_id):
                self.notify(f"Falha ao trocar entidade para {new_entity_id}", severity="error", timeout=5)
                return

            logger.info(f"Trocando entidade: {old_entity_id} -> {new_entity_id}")
            entity_loader = EntityLoader(new_entity_id)
            new_entity_name = entity_loader.get_config().get("name", new_entity_id.capitalize())
            self._clear_theme_caches()
            self.notify(f"Reiniciando para aplicar {new_entity_name}...", severity="information", timeout=2)
            self.app.set_timer(1.5, lambda: self._restart_application())
        except Exception as e:
            logger.error(f"Erro ao trocar entidade: {e}")
            self.notify(f"Erro ao trocar entidade: {e}", severity="error", timeout=5)

    def _clear_theme_caches(self):
        cache_dirs = [
            config.APP_DIR / "src" / "temp",
            config.APP_DIR / "__pycache__",
            config.APP_DIR / "src" / "__pycache__",
            config.APP_DIR / "src" / "ui" / "__pycache__",
            config.APP_DIR / "src" / "core" / "__pycache__",
        ]
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                except Exception as e:
                    logger.debug(f"Erro ao limpar cache {cache_dir}: {e}")

    def _restart_application(self):
        try:
            if hasattr(self.app, "safe_exit"):
                self.app.safe_exit()
            else:
                self.app.exit()
            python = sys.executable
            main_script = config.APP_DIR / "main.py"
            os.execv(python, [python, str(main_script)])
        except Exception as e:
            logger.error(f"Erro ao reiniciar aplicacao: {e}")
            self.app.exit()

    def _save_settings(self):
        if not self._download_manager.check_and_download(self._do_save_settings):
            self._do_save_settings()

    def _do_save_settings(self):
        from src.ui.screens.canone.save_settings import save_all_settings

        save_all_settings(self, self._env.env_path, logger)
