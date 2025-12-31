from __future__ import annotations

import logging
import re
import subprocess
import threading
from collections.abc import Callable

from src.core.desktop_integration.models import NotificationData

logger = logging.getLogger(__name__)


class DBusNotificationListener:
    def __init__(self, callback: Callable[[NotificationData], None] | None = None):
        self._callback = callback
        self._running = False
        self._thread: threading.Thread | None = None
        self._notifications: list[NotificationData] = []
        self._max_stored = 20
        self._dbus_available = self._check_dbus()

    def _check_dbus(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "dbus-send",
                    "--session",
                    "--print-reply",
                    "--dest=org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus.ListNames",
                ],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _parse_notification(self, line: str) -> NotificationData | None:
        patterns = [
            r"string \"([^\"]+)\".*string \"([^\"]+)\".*string \"([^\"]+)\"",
            r"member=Notify.*string \"([^\"]+)\"",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    return NotificationData(app_name=groups[0], summary=groups[1], body=groups[2])
                elif len(groups) >= 1:
                    return NotificationData(app_name=groups[0], summary="", body="")
        return None

    def _monitor_loop(self):
        if not self._dbus_available:
            logger.warning("D-Bus nao disponivel, listener desativado")
            return

        try:
            proc = subprocess.Popen(
                ["dbus-monitor", "--session", "interface='org.freedesktop.Notifications',member='Notify'"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )

            buffer = ""
            while self._running:
                line = proc.stdout.readline()
                if not line:
                    break

                buffer += line

                if "member=Notify" in buffer or len(buffer) > 2000:
                    notification = self._parse_notification(buffer)
                    if notification:
                        self._notifications.append(notification)
                        if len(self._notifications) > self._max_stored:
                            self._notifications.pop(0)

                        if self._callback:
                            try:
                                self._callback(notification)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

                        logger.debug(f"Notificacao: {notification.app_name} - {notification.summary}")

                    buffer = ""

            proc.terminate()

        except Exception as e:
            logger.error(f"Erro no listener D-Bus: {e}")

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("D-Bus notification listener iniciado")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("D-Bus notification listener parado")

    def get_recent(self, count: int = 5) -> list[NotificationData]:
        return self._notifications[-count:]

    def get_context(self) -> str:
        recent = self.get_recent(3)
        if not recent:
            return ""
        return "\n".join(n.to_context() for n in recent)
