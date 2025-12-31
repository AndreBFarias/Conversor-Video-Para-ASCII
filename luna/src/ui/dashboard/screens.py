from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen

from .widgets import (
    AudioWaveNode,
    MatrixRainNode,
    NetworkTraceNode,
    PersonaBanner,
    SystemLogNode,
)


class DashboardScreen(Screen):
    CSS = """
    DashboardScreen {
        background: #282a36;
    }

    #dashboard-grid {
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1;
        padding: 1;
        height: 100%;
    }

    #persona-banner {
        column-span: 2;
        height: 100%;
    }

    #system-log {
        height: 100%;
    }

    #matrix-rain {
        height: 100%;
    }

    #audio-wave {
        height: 100%;
    }

    #network-trace {
        height: 100%;
    }

    Static {
        background: #282a36;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            PersonaBanner(persona_name="LUNA", id="persona-banner"),
            SystemLogNode(id="system-log"),
            MatrixRainNode(id="matrix-rain"),
            AudioWaveNode(id="audio-wave"),
            NetworkTraceNode(id="network-trace"),
            id="dashboard-grid",
        )
