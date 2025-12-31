from __future__ import annotations

import random

from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

from ..constants import DRACULA


class NetworkTraceNode(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._connections: list[dict] = []
        self._max_connections = 8
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.5, self._update_network)

    def _random_ip(self) -> str:
        return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

    def _update_network(self) -> None:
        if random.random() > 0.6 and len(self._connections) < self._max_connections:
            protocols = ["TCP", "UDP", "HTTPS", "WSS", "GRPC"]
            statuses = ["ESTABLISHED", "SYN_SENT", "CONNECTED", "LISTENING"]
            ports = [443, 8080, 3000, 5000, 9090, 27017, 6379, 5432]

            conn = {
                "ip": self._random_ip(),
                "port": random.choice(ports),
                "protocol": random.choice(protocols),
                "status": random.choice(statuses),
                "latency": random.randint(1, 150),
                "age": 0,
            }
            self._connections.append(conn)

        for conn in self._connections:
            conn["age"] += 1
            conn["latency"] = max(1, conn["latency"] + random.randint(-10, 10))

        self._connections = [c for c in self._connections if c["age"] < random.randint(10, 20)]

        self._update_display()

    def _update_display(self) -> None:
        text = Text()

        header = Text()
        header.append("IP ADDRESS       ", style=Style(color=DRACULA["purple"], bold=True))
        header.append("PORT  ", style=Style(color=DRACULA["purple"], bold=True))
        header.append("PROTO ", style=Style(color=DRACULA["purple"], bold=True))
        header.append("STATUS      ", style=Style(color=DRACULA["purple"], bold=True))
        header.append("PING", style=Style(color=DRACULA["purple"], bold=True))
        text.append_text(header)
        text.append("\n")
        text.append("─" * 50 + "\n", style=Style(color=DRACULA["comment"]))

        for conn in self._connections:
            ip_text = f"{conn['ip']:<16} "
            port_text = f"{conn['port']:<5} "
            proto_text = f"{conn['protocol']:<5} "
            status_text = f"{conn['status']:<11} "
            latency_text = f"{conn['latency']}ms"

            if conn["status"] == "ESTABLISHED":
                status_style = Style(color=DRACULA["green"])
            elif conn["status"] == "CONNECTED":
                status_style = Style(color=DRACULA["cyan"])
            else:
                status_style = Style(color=DRACULA["yellow"])

            if conn["latency"] < 50:
                latency_style = Style(color=DRACULA["green"])
            elif conn["latency"] < 100:
                latency_style = Style(color=DRACULA["yellow"])
            else:
                latency_style = Style(color=DRACULA["red"])

            text.append(ip_text, style=Style(color=DRACULA["fg"]))
            text.append(port_text, style=Style(color=DRACULA["orange"]))
            text.append(proto_text, style=Style(color=DRACULA["cyan"]))
            text.append(status_text, style=status_style)
            text.append(latency_text, style=latency_style)
            text.append("\n")

        if not self._connections:
            text.append("No active connections...\n", style=Style(color=DRACULA["comment"], italic=True))

        panel = Panel(
            text,
            border_style=Style(color=DRACULA["orange"]),
            title="[bold #ffb86c]◈ NETWORK TRACE ◈[/]",
            title_align="center",
        )
        self.update(panel)
