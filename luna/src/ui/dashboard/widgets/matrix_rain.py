from __future__ import annotations

import random

from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

from ..constants import DRACULA, MATRIX_CHARS


class MatrixRainNode(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._width = 40
        self._height = 10
        self._drops: list[int] = []
        self._speeds: list[int] = []
        self._timer: Timer | None = None
        self._grid: list[list[str]] = []

    def on_mount(self) -> None:
        self._init_rain()
        self._timer = self.set_interval(0.1, self._animate_rain)

    def _init_rain(self) -> None:
        self._drops = [random.randint(-self._height, 0) for _ in range(self._width)]
        self._speeds = [random.randint(1, 3) for _ in range(self._width)]
        self._grid = [[" " for _ in range(self._width)] for _ in range(self._height)]

    def _animate_rain(self) -> None:
        self._grid = [[" " for _ in range(self._width)] for _ in range(self._height)]

        for col in range(self._width):
            self._drops[col] += self._speeds[col]

            if self._drops[col] > self._height + random.randint(3, 8):
                self._drops[col] = random.randint(-5, 0)
                self._speeds[col] = random.randint(1, 3)

            head_row = self._drops[col]
            for trail in range(5):
                row = head_row - trail
                if 0 <= row < self._height:
                    self._grid[row][col] = random.choice(MATRIX_CHARS)

        self._update_display()

    def _update_display(self) -> None:
        text = Text()
        for row_idx, row in enumerate(self._grid):
            for col_idx, char in enumerate(row):
                if char == " ":
                    text.append(" ")
                else:
                    head_row = self._drops[col_idx]
                    distance = head_row - row_idx
                    if distance == 0:
                        style = Style(color="#ffffff", bold=True)
                    elif distance == 1:
                        style = Style(color=DRACULA["green"], bold=True)
                    elif distance < 3:
                        style = Style(color=DRACULA["green"])
                    else:
                        style = Style(color=DRACULA["green"], dim=True)
                    text.append(char, style=style)
            text.append("\n")

        panel = Panel(
            text,
            border_style=Style(color=DRACULA["green"]),
            title="[bold #50fa7b]◈ MATRIX RAIN ◈[/]",
            title_align="center",
        )
        self.update(panel)
