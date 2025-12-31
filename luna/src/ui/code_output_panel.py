import logging

import pyperclip
from textual.message import Message
from textual.widgets import Label, Static, TextArea

logger = logging.getLogger(__name__)


class CodeOutputPanel(Static):
    CSS = """
    CodeOutputPanel {
        height: 100%;
        background: #1e1f29;
    }

    #code-output-header {
        height: 1;
        background: #2d2f3d;
        color: #bd93f9;
        padding: 0 1;
        text-style: bold;
    }

    #code-output-area {
        height: 1fr;
        background: #1e1f29;
        border: none;
        scrollbar-background: #2d2f3d;
        scrollbar-color: #6272a4;
    }

    #code-status {
        height: 1;
        background: #2d2f3d;
        color: #6272a4;
        padding: 0 1;
    }

    .code-output-clickable {
        cursor: pointer;
    }
    """

    class CodeCopied(Message):
        def __init__(self, length: int) -> None:
            self.length = length
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code_buffer = ""
        self.line_count = 0

    def compose(self):
        yield Label("Code Output Mode", id="code-output-header")
        yield TextArea(id="code-output-area", read_only=True, language="python")
        yield Label("Clique para copiar todo o codigo", id="code-status")

    def on_mount(self) -> None:
        self.tooltip = "Clique para copiar todo o codigo"

    def append_code(self, code: str, language: str = "python") -> None:
        self.code_buffer += code + "\n\n"
        self.line_count += code.count("\n") + 2
        try:
            area = self.query_one("#code-output-area", TextArea)
            area.load_text(self.code_buffer)
            area.scroll_end()
            self._update_status()
        except Exception as e:
            logger.error(f"Erro ao adicionar codigo: {e}")

    def append_stream(self, chunk: str) -> None:
        self.code_buffer += chunk
        try:
            area = self.query_one("#code-output-area", TextArea)
            area.load_text(self.code_buffer)
            area.scroll_end()
        except Exception as e:
            logger.debug(f"Erro no stream: {e}")

    def _update_status(self) -> None:
        try:
            status = self.query_one("#code-status", Label)
            char_count = len(self.code_buffer)
            status.update(f"{self.line_count} linhas | {char_count} chars | Clique para copiar")
        except Exception as e:
            logger.debug(f"Erro ao atualizar status do painel de codigo: {e}")

    def clear(self) -> None:
        self.code_buffer = ""
        self.line_count = 0
        try:
            area = self.query_one("#code-output-area", TextArea)
            area.load_text("")
            self._update_status()
        except Exception as e:
            logger.error(f"Erro ao limpar: {e}")

    def on_click(self) -> None:
        if not self.code_buffer:
            self.notify("Nenhum codigo para copiar", timeout=1.5)
            return

        try:
            pyperclip.copy(self.code_buffer)
            self.post_message(self.CodeCopied(len(self.code_buffer)))
            self.notify("Todo codigo copiado!", timeout=1.5)
            logger.info(f"Codigo copiado: {len(self.code_buffer)} caracteres")
        except Exception as e:
            logger.error(f"Erro ao copiar: {e}")
            self.notify(f"Erro ao copiar: {e}", severity="error", timeout=2)

    def get_code(self) -> str:
        return self.code_buffer

    def set_language(self, language: str) -> None:
        try:
            area = self.query_one("#code-output-area", TextArea)
            area.language = language
        except Exception as e:
            logger.debug(f"Erro ao definir linguagem: {e}")
