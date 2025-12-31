from __future__ import annotations

import logging
import re
import subprocess
import threading
import time
from collections.abc import Callable

from src.core.desktop_integration.models import WindowData

logger = logging.getLogger(__name__)


class ActiveWindowTracker:
    def __init__(self, callback: Callable[[WindowData], None] | None = None):
        self._callback = callback
        self._running = False
        self._thread: threading.Thread | None = None
        self._current_window: WindowData | None = None
        self._window_history: list[WindowData] = []
        self._max_history = 20
        self._poll_interval = 2.0

    def _get_active_window(self) -> WindowData | None:
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"], capture_output=True, timeout=2, text=True
            )

            if result.returncode != 0:
                return None

            title = result.stdout.strip()

            result2 = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, timeout=2, text=True)

            window_id = result2.stdout.strip()

            result3 = subprocess.run(["xprop", "-id", window_id, "WM_CLASS"], capture_output=True, timeout=2, text=True)

            app_class = ""
            app_name = ""

            if result3.returncode == 0:
                match = re.search(r'= "([^"]*)", "([^"]*)"', result3.stdout)
                if match:
                    app_class = match.group(1)
                    app_name = match.group(2)

            return WindowData(title=title, app_class=app_class, app_name=app_name or self._guess_app_from_title(title))

        except FileNotFoundError:
            logger.warning("xdotool nao instalado - Active Window desabilitado")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter janela ativa: {e}")
            return None

    def _guess_app_from_title(self, title: str) -> str:
        patterns = {
            "firefox": ["Firefox", "Mozilla"],
            "chrome": ["Chrome", "Chromium"],
            "vscode": ["Visual Studio Code", "Code"],
            "terminal": ["Terminal", "Konsole", "gnome-terminal", "Alacritty"],
            "nautilus": ["Files", "Nautilus"],
            "spotify": ["Spotify"],
            "discord": ["Discord"],
            "telegram": ["Telegram"],
            "slack": ["Slack"],
        }

        title_lower = title.lower()
        for app, keywords in patterns.items():
            if any(kw.lower() in title_lower for kw in keywords):
                return app

        return "unknown"

    def _monitor_loop(self):
        while self._running:
            try:
                window = self._get_active_window()

                if window and (not self._current_window or window.title != self._current_window.title):
                    self._current_window = window
                    self._window_history.append(window)

                    if len(self._window_history) > self._max_history:
                        self._window_history.pop(0)

                    if self._callback:
                        try:
                            self._callback(window)
                        except Exception as e:
                            logger.error(f"Window callback error: {e}")

                    logger.debug(f"Janela ativa: {window.app_name} - {window.title[:50]}")

                time.sleep(self._poll_interval)

            except Exception as e:
                logger.error(f"Erro no tracker de janela: {e}")
                time.sleep(5)

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Active window tracker iniciado")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Active window tracker parado")

    def get_current(self) -> WindowData | None:
        return self._current_window

    def get_history(self, count: int = 5) -> list[WindowData]:
        return self._window_history[-count:]

    def get_context(self) -> str:
        if not self._current_window:
            return ""
        return self._current_window.to_context()
