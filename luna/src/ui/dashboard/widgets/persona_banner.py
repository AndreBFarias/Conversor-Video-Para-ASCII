from __future__ import annotations

import random

from rich.align import Align
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static

from ..constants import DRACULA, GLITCH_CHARS

try:
    import pyfiglet
except ImportError:
    pyfiglet = None


class PersonaBanner(Static):
    frame_count: reactive[int] = reactive(0)
    is_decrypting: reactive[bool] = reactive(True)

    def __init__(self, persona_name: str = "LUNA", font: str = "slant", **kwargs) -> None:
        super().__init__(**kwargs)
        self.persona_name = persona_name.upper()
        self.font = font
        self._ascii_lines: list[str] = []
        self._locked_chars: list[list[bool]] = []
        self._current_display: list[list[str]] = []
        self._timer: Timer | None = None
        self._generate_ascii()

    def _generate_ascii(self) -> None:
        if pyfiglet:
            try:
                fig = pyfiglet.Figlet(font=self.font, width=200)
                ascii_art = fig.renderText(self.persona_name)
                self._ascii_lines = [line for line in ascii_art.split("\n") if line.strip()]
            except Exception:
                self._ascii_lines = [self.persona_name]
        else:
            self._ascii_lines = [self.persona_name]

        self._locked_chars = []
        self._current_display = []

        for line in self._ascii_lines:
            self._locked_chars.append([False] * len(line))
            self._current_display.append(list(line))

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.08, self._animate_frame)

    def _animate_frame(self) -> None:
        if not self.is_decrypting:
            if random.random() > 0.95:
                self._glitch_frame()
            return

        self.frame_count += 1

        all_locked = True
        for row_idx, line in enumerate(self._ascii_lines):
            for col_idx, char in enumerate(line):
                if char == " ":
                    self._current_display[row_idx][col_idx] = " "
                    self._locked_chars[row_idx][col_idx] = True
                    continue

                if not self._locked_chars[row_idx][col_idx]:
                    all_locked = False
                    lock_chance = 0.02 + (self.frame_count * 0.005)
                    if random.random() < lock_chance:
                        self._locked_chars[row_idx][col_idx] = True
                        self._current_display[row_idx][col_idx] = char
                    else:
                        self._current_display[row_idx][col_idx] = random.choice(GLITCH_CHARS)

        if all_locked:
            self.is_decrypting = False

        self._update_display()

    def _glitch_frame(self) -> None:
        for row_idx, line in enumerate(self._ascii_lines):
            for col_idx, char in enumerate(line):
                if char != " " and random.random() > 0.92:
                    self._current_display[row_idx][col_idx] = random.choice(GLITCH_CHARS)
                else:
                    self._current_display[row_idx][col_idx] = char

        self._update_display()

        self.set_timer(0.1, self._restore_display)

    def _restore_display(self) -> None:
        for row_idx, line in enumerate(self._ascii_lines):
            self._current_display[row_idx] = list(line)
        self._update_display()

    def _update_display(self) -> None:
        lines = []
        for row_idx, row in enumerate(self._current_display):
            text = Text()
            for col_idx, char in enumerate(row):
                if self._locked_chars[row_idx][col_idx]:
                    style = Style(color=DRACULA["purple"], bold=True)
                else:
                    colors = [DRACULA["pink"], DRACULA["cyan"], DRACULA["comment"]]
                    style = Style(color=random.choice(colors))
                text.append(char, style=style)
            lines.append(text)

        combined = Text("\n").join(lines)
        panel = Panel(
            Align.center(combined),
            border_style=Style(color=DRACULA["purple"], bold=True),
            title="[bold #ff79c6]◈ NEURAL CORE ◈[/]",
            title_align="center",
            subtitle="[#6272a4]PERSONA ACTIVE[/]",
            subtitle_align="center",
        )
        self.update(panel)
