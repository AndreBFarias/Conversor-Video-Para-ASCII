from __future__ import annotations

import random

from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

from ..constants import DRACULA


class AudioWaveNode(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._bars = 20
        self._max_height = 8
        self._levels: list[int] = [0] * self._bars
        self._targets: list[int] = [0] * self._bars
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.1, self._animate_spectrum)

    def _animate_spectrum(self) -> None:
        for i in range(self._bars):
            if random.random() > 0.7:
                self._targets[i] = random.randint(1, self._max_height)

            if self._levels[i] < self._targets[i]:
                self._levels[i] += 1
            elif self._levels[i] > self._targets[i]:
                self._levels[i] -= 1

            if random.random() > 0.9:
                self._targets[i] = max(1, self._targets[i] - 2)

        self._update_display()

    def _update_display(self) -> None:
        lines = []
        for row in range(self._max_height, 0, -1):
            text = Text()
            for col, level in enumerate(self._levels):
                if level >= row:
                    if row > self._max_height * 0.75:
                        style = Style(color=DRACULA["red"], bold=True)
                    elif row > self._max_height * 0.5:
                        style = Style(color=DRACULA["orange"])
                    elif row > self._max_height * 0.25:
                        style = Style(color=DRACULA["yellow"])
                    else:
                        style = Style(color=DRACULA["green"])
                    text.append("█ ", style=style)
                else:
                    text.append("░ ", style=Style(color=DRACULA["comment"], dim=True))
            lines.append(text)

        combined = Text("\n").join(lines)
        panel = Panel(
            combined,
            border_style=Style(color=DRACULA["cyan"]),
            title="[bold #8be9fd]◈ AUDIO SPECTRUM ◈[/]",
            title_align="center",
        )
        self.update(panel)
