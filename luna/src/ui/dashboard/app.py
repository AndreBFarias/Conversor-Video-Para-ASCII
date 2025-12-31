from __future__ import annotations

from textual.app import App

from .screens import DashboardScreen


class DashboardApp(App):
    CSS = """
    Screen {
        background: #282a36;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


def main() -> None:
    app = DashboardApp()
    app.run()
