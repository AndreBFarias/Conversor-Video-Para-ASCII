from __future__ import annotations

import logging
import re
from typing import Callable

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Label, ProgressBar, Static

logger = logging.getLogger(__name__)


class DownloadModal(ModalScreen):
    CSS = """
    DownloadModal {
        align: center middle;
    }

    DownloadModal > Container {
        width: 60;
        height: auto;
        max-height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    DownloadModal #download-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    DownloadModal #download-counter {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    DownloadModal #download-model {
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }

    DownloadModal #download-status {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    DownloadModal ProgressBar {
        margin: 1 0;
    }

    DownloadModal #download-details {
        text-align: center;
        color: $text-muted;
        height: 1;
    }
    """

    def __init__(
        self,
        model_name: str,
        on_complete: Callable[[bool, str], None] | None = None,
        current: int = 1,
        total: int = 1,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self._on_complete = on_complete
        self._current = current
        self._total = total
        self._progress = 0.0
        self._status = "Iniciando..."
        self._details = ""

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Baixando Modelo", id="download-title")
            counter_text = f"[dim]{self._current}/{self._total}[/dim]" if self._total > 1 else ""
            yield Static(counter_text, id="download-counter")
            yield Static(f"[bold]{self.model_name}[/bold]", id="download-model")
            yield Static(self._status, id="download-status")
            yield ProgressBar(total=100, show_eta=False, id="download-progress")
            yield Static("", id="download-details")

    def update_model(self, model_name: str, current: int) -> None:
        self.model_name = model_name
        self._current = current
        self._progress = 0.0
        self._status = "Iniciando..."
        try:
            self.query_one("#download-model", Static).update(f"[bold]{model_name}[/bold]")
            self.query_one("#download-counter", Static).update(f"[dim]{current}/{self._total}[/dim]")
            self.query_one("#download-status", Static).update("[yellow]Iniciando...[/yellow]")
            self.query_one("#download-progress", ProgressBar).progress = 0
            self.query_one("#download-details", Static).update("")
        except Exception as e:
            logger.debug(f"Erro ao atualizar modelo no modal: {e}")

    def update_progress(self, status: str) -> None:
        try:
            ansi_pattern = r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\[[\?0-9]*[a-zA-Z]"
            clean_status = re.sub(ansi_pattern, "", status)
            clean_status = re.sub(r"[\x00-\x1f\x7f]", "", clean_status)
            clean_status = clean_status.strip()

            if not clean_status:
                return

            self._status = clean_status
            progress_widget = self.query_one("#download-progress", ProgressBar)
            status_widget = self.query_one("#download-status", Static)
            details_widget = self.query_one("#download-details", Static)

            match = re.search(r"(\d+)%", clean_status)
            if match:
                self._progress = float(match.group(1))
                progress_widget.progress = self._progress

            speed_match = re.search(r"(\d+\.?\d*\s*[KMGT]?B/s)", clean_status)
            if speed_match:
                self._details = speed_match.group(1)
                details_widget.update(f"[dim]{self._details}[/dim]")

            display_status = clean_status[:50] + "..." if len(clean_status) > 50 else clean_status
            status_widget.update(f"[yellow]{display_status}[/yellow]")

        except Exception as e:
            logger.debug(f"Erro ao atualizar progresso: {e}")

    def complete(self, success: bool, message: str) -> None:
        if self._on_complete:
            self._on_complete(success, message)
        self.dismiss(success)

    def on_key(self, event) -> None:
        event.prevent_default()
        event.stop()


class GlitchLabel(Label):
    def __init__(self, text: str, **kwargs):
        super().__init__(text, **kwargs)
        self._original_text = text
        self._glitch_chars = "!@#$%^&*()[]{}|;:,.<>?/\\~`"

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.08, self._animate)
        self._frame = 0
        self._locked = [False] * len(self._original_text)
        self._current = list(self._original_text)

    def _animate(self) -> None:
        import random

        if all(self._locked):
            if random.random() > 0.95:
                self._glitch_burst()
            return

        self._frame += 1

        for i, char in enumerate(self._original_text):
            if char in " \n\t":
                self._current[i] = char
                self._locked[i] = True
                continue

            if not self._locked[i]:
                lock_chance = 0.03 + (self._frame * 0.008)
                if random.random() < lock_chance:
                    self._locked[i] = True
                    self._current[i] = char
                else:
                    self._current[i] = random.choice(self._glitch_chars)

        self.update("".join(self._current))

    def _glitch_burst(self) -> None:
        import random

        for i, char in enumerate(self._original_text):
            if char not in " \n\t" and random.random() > 0.85:
                self._current[i] = random.choice(self._glitch_chars)
        self.update("".join(self._current))
        self.set_timer(0.15, self._restore)

    def _restore(self) -> None:
        self._current = list(self._original_text)
        self.update(self._original_text)
