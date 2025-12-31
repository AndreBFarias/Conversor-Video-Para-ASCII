from __future__ import annotations

import logging
import subprocess
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IdleDetector:
    def __init__(
        self,
        idle_threshold_seconds: int = 300,
        on_idle_start: Callable[[], None] | None = None,
        on_idle_end: Callable[[], None] | None = None,
    ):
        self._threshold = idle_threshold_seconds
        self._on_idle_start = on_idle_start
        self._on_idle_end = on_idle_end
        self._running = False
        self._thread: threading.Thread | None = None
        self._is_idle = False
        self._last_idle_time: datetime | None = None
        self._poll_interval = 30

    def _get_idle_time(self) -> int:
        try:
            result = subprocess.run(["xprintidle"], capture_output=True, timeout=2, text=True)

            if result.returncode == 0:
                return int(result.stdout.strip()) // 1000

        except FileNotFoundError:
            try:
                result = subprocess.run(["xssstate", "-i"], capture_output=True, timeout=2, text=True)
                if result.returncode == 0:
                    return int(result.stdout.strip()) // 1000
            except Exception as e:
                logger.debug(f"Erro ao obter idle time com xssstate: {e}")
        except Exception as e:
            logger.debug(f"Erro ao obter idle time com xprintidle: {e}")

        return 0

    def _monitor_loop(self):
        while self._running:
            try:
                idle_seconds = self._get_idle_time()

                if idle_seconds >= self._threshold and not self._is_idle:
                    self._is_idle = True
                    self._last_idle_time = datetime.now()
                    logger.info(f"Usuario idle detectado ({idle_seconds}s)")

                    if self._on_idle_start:
                        try:
                            self._on_idle_start()
                        except Exception as e:
                            logger.error(f"Idle start callback error: {e}")

                elif idle_seconds < self._threshold and self._is_idle:
                    self._is_idle = False
                    logger.info("Usuario retornou da inatividade")

                    if self._on_idle_end:
                        try:
                            self._on_idle_end()
                        except Exception as e:
                            logger.error(f"Idle end callback error: {e}")

                time.sleep(self._poll_interval)

            except Exception as e:
                logger.error(f"Erro no detector de idle: {e}")
                time.sleep(60)

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Idle detector iniciado (threshold: {self._threshold}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Idle detector parado")

    def is_idle(self) -> bool:
        return self._is_idle

    def get_idle_duration(self) -> timedelta | None:
        if self._is_idle and self._last_idle_time:
            return datetime.now() - self._last_idle_time
        return None

    def get_context(self) -> str:
        if self._is_idle:
            duration = self.get_idle_duration()
            if duration:
                minutes = int(duration.total_seconds() // 60)
                return f"[Usuario ausente ha {minutes} minutos]"
        return ""
