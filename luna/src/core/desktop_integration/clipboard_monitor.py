from __future__ import annotations

import logging
import subprocess
import threading
import time
from collections.abc import Callable

from src.core.desktop_integration.models import ClipboardData

logger = logging.getLogger(__name__)


class ClipboardMonitor:
    def __init__(self, callback: Callable[[ClipboardData], None] | None = None):
        self._callback = callback
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_content = ""
        self._current_data: ClipboardData | None = None
        self._history: list[ClipboardData] = []
        self._max_history = 10
        self._poll_interval = 1.0

    def _get_clipboard(self) -> str:
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"], capture_output=True, timeout=1, text=True
            )
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            try:
                result = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, timeout=1, text=True)
                if result.returncode == 0:
                    return result.stdout
            except Exception as e:
                logger.debug(f"Erro ao ler clipboard com xsel: {e}")
        except Exception as e:
            logger.debug(f"Erro ao ler clipboard com xclip: {e}")
        return ""

    def _monitor_loop(self):
        while self._running:
            try:
                content = self._get_clipboard()

                if content and content != self._last_content:
                    self._last_content = content

                    data = ClipboardData(content=content, content_type="text")
                    self._current_data = data
                    self._history.append(data)

                    if len(self._history) > self._max_history:
                        self._history.pop(0)

                    if self._callback:
                        try:
                            self._callback(data)
                        except Exception as e:
                            logger.error(f"Clipboard callback error: {e}")

                    logger.debug(f"Clipboard mudou: {content[:50]}...")

                time.sleep(self._poll_interval)

            except Exception as e:
                logger.error(f"Erro no monitor clipboard: {e}")
                time.sleep(5)

    def start(self):
        if self._running:
            return

        self._running = True
        self._last_content = self._get_clipboard()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Clipboard monitor iniciado")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Clipboard monitor parado")

    def get_current(self) -> ClipboardData | None:
        return self._current_data

    def get_history(self, count: int = 5) -> list[ClipboardData]:
        return self._history[-count:]

    def get_context(self) -> str:
        if not self._current_data:
            return ""
        return self._current_data.to_context()
