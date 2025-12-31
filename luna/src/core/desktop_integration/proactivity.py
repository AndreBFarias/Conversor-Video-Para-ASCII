from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProactivityManager:
    def __init__(self, luna_speak_callback: Callable[[str], None] | None = None, min_interval_minutes: int = 30):
        self._callback = luna_speak_callback
        self._min_interval = timedelta(minutes=min_interval_minutes)
        self._last_proactive: datetime | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._triggers: list[dict] = []
        self._check_interval = 60

    def add_trigger(
        self, name: str, condition: Callable[[], bool], message_generator: Callable[[], str], cooldown_minutes: int = 60
    ):
        self._triggers.append(
            {
                "name": name,
                "condition": condition,
                "message": message_generator,
                "cooldown": timedelta(minutes=cooldown_minutes),
                "last_fired": None,
            }
        )

    def _can_be_proactive(self) -> bool:
        if not self._last_proactive:
            return True
        return datetime.now() - self._last_proactive > self._min_interval

    def _check_triggers(self):
        if not self._can_be_proactive():
            return

        now = datetime.now()

        for trigger in self._triggers:
            if trigger["last_fired"]:
                if now - trigger["last_fired"] < trigger["cooldown"]:
                    continue

            try:
                if trigger["condition"]():
                    message = trigger["message"]()

                    if message and self._callback:
                        logger.info(f"Proatividade disparada: {trigger['name']}")
                        self._callback(message)
                        trigger["last_fired"] = now
                        self._last_proactive = now
                        break

            except Exception as e:
                logger.error(f"Erro no trigger {trigger['name']}: {e}")

    def _monitor_loop(self):
        while self._running:
            try:
                self._check_triggers()
                time.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"Erro no proactivity manager: {e}")
                time.sleep(120)

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Proactivity manager iniciado")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Proactivity manager parado")
