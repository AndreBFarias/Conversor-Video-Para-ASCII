import logging
import re

import pyperclip
from textual.binding import Binding
from textual.events import Click, Key
from textual.message import Message
from textual.widgets import TextArea

logger = logging.getLogger(__name__)


class MultilineInput(TextArea):
    BINDINGS = [
        Binding("enter", "submit", "Enviar", priority=True),
        Binding("ctrl+j", "newline", "Nova Linha", priority=True),
        Binding("ctrl+a", "select_all", "Selecionar Tudo", priority=True),
        Binding("ctrl+c", "copy", "Copiar", priority=True),
        Binding("ctrl+x", "cut", "Cortar", priority=True),
        Binding("ctrl+v", "paste", "Colar", priority=True),
        Binding("ctrl+z", "undo", "Desfazer", priority=True),
        Binding("ctrl+y", "redo", "Refazer", priority=True),
        Binding("ctrl+shift+z", "redo", "Refazer", priority=True),
        Binding("escape", "blur", "Desfocar", priority=True),
    ]

    DEFAULT_CSS = """
    MultilineInput {
        height: auto;
        min-height: 3;
        max-height: 6;
        width: 1fr;
        border: round transparent;
        background: #44475a;
        padding: 0 1;
        color: #f8f8f2;
    }

    MultilineInput:focus {
        border: round #4f48d0;
        background: #383a4d;
    }

    MultilineInput > .text-area--cursor {
        background: #bd93f9;
        color: #282a36;
    }

    MultilineInput > .text-area--selection {
        background: #44475a;
    }
    """

    class Submitted(Message):
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    class ReactionSelected(Message):
        def __init__(self, reaction: str) -> None:
            self.reaction = reaction
            super().__init__()

    def __init__(
        self,
        placeholder: str = "",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            classes=classes,
            language=None,
            theme="dracula",
            soft_wrap=True,
            tab_behavior="indent",
            show_line_numbers=False,
        )
        self._placeholder = placeholder
        self._undo_stack: list[str] = [""]
        self._redo_stack: list[str] = []
        self._last_text = ""
        self._reaction_pattern = re.compile(r"/(rea[cç]?[aã]?o?|react)\s+(Luna_\w+)", re.IGNORECASE)

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str) -> None:
        self._placeholder = value
        self._update_placeholder_display()

    def on_mount(self) -> None:
        self._update_placeholder_display()

    def _update_placeholder_display(self) -> None:
        if not self.text and self._placeholder:
            pass

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, new_value: str) -> None:
        self.text = new_value

    def on_text_area_changed(self, event) -> None:
        current_text = self.text
        if current_text != self._last_text:
            self._undo_stack.append(self._last_text)
            self._redo_stack.clear()
            if len(self._undo_stack) > 100:
                self._undo_stack.pop(0)
            self._last_text = current_text

        self._check_for_reaction()
        self._adjust_container_height()

    def _adjust_container_height(self) -> None:
        line_count = self.text.count("\n") + 1
        min_lines = 1
        max_lines = 4
        target_lines = max(min_lines, min(line_count, max_lines))
        new_height = 3 + target_lines
        try:
            container = self.parent
            if container and hasattr(container, "styles"):
                container.styles.height = new_height
        except Exception as e:
            logger.debug(f"Ajuste de altura: {e}")

    def _check_for_reaction(self) -> None:
        match = self._reaction_pattern.search(self.text)
        if match:
            self.post_message(self.ReactionSelected(match.group(2)))

    def action_submit(self) -> None:
        text = self.text.strip()
        if text:
            self.post_message(self.Submitted(text))
            self.text = ""
            self._undo_stack = [""]
            self._redo_stack = []
            self._last_text = ""
            try:
                container = self.parent
                if container and hasattr(container, "styles"):
                    container.styles.height = 4
            except Exception as e:
                logger.debug(f"Erro ao restaurar altura do container apos submit: {e}")

    def action_newline(self) -> None:
        self.insert("\n")

    def action_select_all(self) -> None:
        self.select_all()

    def action_copy(self) -> None:
        selection = self.selected_text
        if selection:
            try:
                pyperclip.copy(selection)
                self.notify("Copiado!", timeout=1)
            except Exception as e:
                logger.error(f"Erro ao copiar: {e}")
        else:
            try:
                pyperclip.copy(self.text)
                self.notify("Texto copiado!", timeout=1)
            except Exception as e:
                logger.error(f"Erro ao copiar: {e}")

    def action_cut(self) -> None:
        selection = self.selected_text
        if selection:
            try:
                pyperclip.copy(selection)
                self.delete(*self.selection)
                self.notify("Cortado!", timeout=1)
            except Exception as e:
                logger.error(f"Erro ao cortar: {e}")

    def action_paste(self) -> None:
        try:
            text = pyperclip.paste()
            if text:
                if self.selected_text:
                    self.delete(*self.selection)
                self.insert(text)
        except Exception as e:
            logger.error(f"Erro ao colar: {e}")

    def action_undo(self) -> None:
        if len(self._undo_stack) > 1:
            current = self._undo_stack.pop()
            self._redo_stack.append(current)
            previous = self._undo_stack[-1]
            self._last_text = previous
            self.text = previous

    def action_redo(self) -> None:
        if self._redo_stack:
            text = self._redo_stack.pop()
            self._undo_stack.append(text)
            self._last_text = text
            self.text = text

    def action_blur(self) -> None:
        self.blur()

    async def _on_key(self, event: Key) -> None:
        key = event.key
        if key == "ctrl+j":
            event.prevent_default()
            event.stop()
            self.insert("\n")
            return
        elif key == "enter":
            event.prevent_default()
            event.stop()
            self.action_submit()
            return
        await super()._on_key(event)

    def on_click(self, event: Click) -> None:
        if event.button == 3:
            self._show_context_menu(event.screen_x, event.screen_y)
            event.stop()

    def _show_context_menu(self, x: int, y: int) -> None:
        try:
            from src.ui.context_menu import ContextMenu, ContextMenuItem

            items = [
                ContextMenuItem("Cortar", "ctrl+x", self.action_cut),
                ContextMenuItem("Copiar", "ctrl+c", self.action_copy),
                ContextMenuItem("Colar", "ctrl+v", self.action_paste),
                ContextMenuItem("---", "", None),
                ContextMenuItem("Selecionar Tudo", "ctrl+a", self.action_select_all),
                ContextMenuItem("---", "", None),
                ContextMenuItem("Desfazer", "ctrl+z", self.action_undo),
                ContextMenuItem("Refazer", "ctrl+y", self.action_redo),
            ]

            menu = ContextMenu(items, x, y)
            self.app.push_screen(menu)
        except ImportError:
            self._show_simple_context_menu()
        except Exception as e:
            logger.error(f"Erro ao mostrar menu de contexto: {e}")
            self._show_simple_context_menu()

    def _show_simple_context_menu(self) -> None:
        self.notify("Ctrl+C=Copiar | Ctrl+X=Cortar | Ctrl+V=Colar | Ctrl+Z=Desfazer", timeout=3)

    def insert_text_at_cursor(self, text: str) -> None:
        self.insert(text)
