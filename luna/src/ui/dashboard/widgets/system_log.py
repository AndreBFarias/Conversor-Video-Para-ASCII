from __future__ import annotations

import random
from datetime import datetime

from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static

from ..constants import BOOT_MESSAGES, DRACULA


class SystemLogNode(Static):
    log_index: reactive[int] = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._logs: list[str] = []
        self._max_lines = 12
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.15, self._add_log_line)

    def _add_log_line(self) -> None:
        if self.log_index < len(BOOT_MESSAGES):
            self._logs.append(BOOT_MESSAGES[self.log_index])
            self.log_index += 1
        else:
            fake_logs = [
                f"[{datetime.now().strftime('%H:%M:%S')}] SYNC: Memory bank {random.randint(1,8)} consolidated",
                f"[{datetime.now().strftime('%H:%M:%S')}] NET: Packet received from {self._random_ip()}",
                f"[{datetime.now().strftime('%H:%M:%S')}] PROC: Thread pool adjusted to {random.randint(4,16)} workers",
                f"[{datetime.now().strftime('%H:%M:%S')}] MEM: GC cycle completed, freed {random.randint(10,500)}MB",
                f"[{datetime.now().strftime('%H:%M:%S')}] CORE: Attention weight recalibrated",
            ]
            self._logs.append(random.choice(fake_logs))

        if len(self._logs) > self._max_lines:
            self._logs = self._logs[-self._max_lines :]

        self._update_display()

    def _random_ip(self) -> str:
        return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

    def _update_display(self) -> None:
        text = Text()
        for i, log in enumerate(self._logs):
            if "LUNA" in log or "NEURAL" in log:
                style = Style(color=DRACULA["purple"])
            elif "error" in log.lower() or "fail" in log.lower():
                style = Style(color=DRACULA["red"])
            elif "[" in log and "]" in log:
                style = Style(color=DRACULA["green"], dim=(i < len(self._logs) - 3))
            else:
                style = Style(color=DRACULA["fg"], dim=True)
            text.append(log + "\n", style=style)

        panel = Panel(
            text,
            border_style=Style(color=DRACULA["green"]),
            title="[bold #50fa7b]◈ SYSTEM LOG ◈[/]",
            title_align="center",
        )
        self.update(panel)
