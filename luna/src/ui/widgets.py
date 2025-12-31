import re

import pyperclip
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Label, RichLog, Static

from src.core.entity_loader import EntityLoader, get_active_entity


def _get_entity_sender_name() -> str:
    entity_id = get_active_entity()
    loader = EntityLoader(entity_id)
    return loader.get_config().get("name", entity_id.capitalize())


def strip_rich_tags(text: str) -> str:
    pattern = r"\[/?[^\]]+\]"
    clean = re.sub(pattern, "", text)
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
    clean = re.sub(r"\*(.+?)\*", r"\1", clean)
    clean = re.sub(r"_(.+?)_", r"\1", clean)
    return clean


def markdown_to_rich(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"[b]\1[/b]", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"[i]\1[/i]", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"[i]\1[/i]", text)
    return text


class CodeBlock(Static):
    class Copied(Message):
        def __init__(self, code: str) -> None:
            self.code = code
            super().__init__()

    def __init__(self, code: str, language: str = "python"):
        super().__init__()
        self.code = code
        self.language = language
        self.add_class("code-block")

    def compose(self) -> ComposeResult:
        with Vertical(classes="code-block-container"):
            with Horizontal(classes="code-header"):
                yield Label(self.language, classes="code-lang")
                yield Label("clique para copiar", classes="code-hint")

            code_log = RichLog(classes="code-content", wrap=False, highlight=True, markup=False)

            syntax = Syntax(self.code, self.language, theme="dracula", line_numbers=True, word_wrap=False)
            code_log.write(syntax)

            yield code_log

    def on_mount(self) -> None:
        self.tooltip = "Clique para copiar o codigo"

    def on_click(self) -> None:
        try:
            pyperclip.copy(self.code)
            self.post_message(self.Copied(self.code))
            self.notify("Codigo copiado!", timeout=1.5)
            self.add_class("copied")
            self.set_timer(0.5, self._remove_copied_class)
        except Exception as e:
            self.notify(f"Erro ao copiar: {e}", severity="error", timeout=2)

    def _remove_copied_class(self) -> None:
        self.remove_class("copied")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy_code":
            pyperclip.copy(self.code)
            self.notify("Codigo copiado!", severity="information")
            event.stop()


class ClickableText(Static):
    class Clicked(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, content: str, plain_content: str, **kwargs):
        super().__init__(content, markup=True, **kwargs)
        self.plain_content = plain_content

    def on_click(self, event) -> None:
        if event.button == 1:
            try:
                pyperclip.copy(self.plain_content)
                self.add_class("copied")
                self.notify("Texto copiado!", timeout=1.5)
                self.set_timer(0.5, lambda: self.remove_class("copied"))
            except Exception:
                self.notify("Clipboard indisponivel", severity="warning")


class ChatMessage(Static):
    can_focus = True

    BINDINGS = [
        ("enter", "copy_message", "Copiar"),
        ("space", "copy_message", "Copiar"),
    ]

    def __init__(self, role: str, parts: list, user_name: str = None):
        super().__init__()
        entity_name = _get_entity_sender_name()
        role_names = {"luna": entity_name, "user": user_name or "User", "kernel": "Kernel", "code": "Code"}
        self.role = role
        self.display_name = role_names.get(role, role.capitalize())
        self.parts = parts
        self.classes = f"message-container message-{role}"
        self._last_click = 0
        self._full_text = self._extract_full_text()

    def _extract_full_text(self) -> str:
        texts = []
        for type_, content, lang in self.parts:
            if type_ == "text":
                texts.append(strip_rich_tags(content))
            elif type_ == "code":
                texts.append(f"```{lang or ''}\n{content}\n```")
        return "\n\n".join(texts)

    def compose(self) -> ComposeResult:
        yield Label(self.display_name, classes=f"msg-sender {self.role}-sender")
        for type_, content, lang in self.parts:
            if type_ == "text":
                rich_content = markdown_to_rich(content)
                plain_content = strip_rich_tags(content)
                yield ClickableText(rich_content, plain_content, classes="msg-text")
            elif type_ == "code":
                yield CodeBlock(content, lang)

    def on_click(self, event) -> None:
        import time

        now = time.time()
        if now - self._last_click < 0.4:
            self.action_copy_message()
        self._last_click = now

    def action_copy_message(self) -> None:
        try:
            pyperclip.copy(self._full_text)
            self.add_class("copied")
            self.notify(f"Mensagem copiada! ({len(self._full_text)} chars)", timeout=1.5)
            self.set_timer(0.8, lambda: self.remove_class("copied"))
        except Exception:
            self.notify("Clipboard indisponivel", severity="warning")

    def get_text_content(self) -> str:
        return self._full_text
