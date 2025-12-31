from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.core.desktop_integration.clipboard_monitor import ClipboardMonitor
from src.core.desktop_integration.idle_detector import IdleDetector
from src.core.desktop_integration.models import (
    ClipboardData,
    DesktopEvent,
    NotificationData,
    WindowData,
)
from src.core.desktop_integration.notification_listener import DBusNotificationListener
from src.core.desktop_integration.proactivity import ProactivityManager
from src.core.desktop_integration.window_tracker import ActiveWindowTracker

logger = logging.getLogger(__name__)


class DesktopIntegration:
    def __init__(self):
        self._notification_listener: DBusNotificationListener | None = None
        self._clipboard_monitor: ClipboardMonitor | None = None
        self._window_tracker: ActiveWindowTracker | None = None
        self._idle_detector: IdleDetector | None = None
        self._proactivity: ProactivityManager | None = None
        self._event_callbacks: dict[DesktopEvent, list[Callable]] = {}
        self._enabled_features: dict[str, bool] = {
            "notifications": True,
            "clipboard": True,
            "active_window": True,
            "idle_detection": True,
            "proactivity": True,
        }

    def set_feature(self, feature: str, enabled: bool):
        if feature in self._enabled_features:
            self._enabled_features[feature] = enabled

    def register_callback(self, event: DesktopEvent, callback: Callable):
        if event not in self._event_callbacks:
            self._event_callbacks[event] = []
        self._event_callbacks[event].append(callback)

    def _fire_event(self, event: DesktopEvent, data: Any = None):
        if event in self._event_callbacks:
            for callback in self._event_callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")

    def setup(
        self,
        idle_threshold: int = 300,
        proactive_interval: int = 30,
        luna_speak_callback: Callable[[str], None] | None = None,
    ):
        if self._enabled_features.get("notifications"):
            self._notification_listener = DBusNotificationListener(
                callback=lambda n: self._fire_event(DesktopEvent.NOTIFICATION, n)
            )

        if self._enabled_features.get("clipboard"):
            self._clipboard_monitor = ClipboardMonitor(
                callback=lambda c: self._fire_event(DesktopEvent.CLIPBOARD_CHANGE, c)
            )

        if self._enabled_features.get("active_window"):
            self._window_tracker = ActiveWindowTracker(
                callback=lambda w: self._fire_event(DesktopEvent.WINDOW_CHANGE, w)
            )

        if self._enabled_features.get("idle_detection"):
            self._idle_detector = IdleDetector(
                idle_threshold_seconds=idle_threshold,
                on_idle_start=lambda: self._fire_event(DesktopEvent.IDLE_START),
                on_idle_end=lambda: self._fire_event(DesktopEvent.IDLE_END),
            )

        if self._enabled_features.get("proactivity") and luna_speak_callback:
            self._proactivity = ProactivityManager(
                luna_speak_callback=luna_speak_callback, min_interval_minutes=proactive_interval
            )
            self._setup_default_triggers()

    def _setup_default_triggers(self):
        if not self._proactivity:
            return

        def is_late_night():
            hour = datetime.now().hour
            return 23 <= hour or hour <= 5

        def late_night_message():
            hour = datetime.now().hour
            if hour >= 23:
                return "Ja passou das onze... Voce nao deveria estar dormindo?"
            elif hour <= 3:
                return "Madrugada alta. Seu corpo agradece se voce descansar."
            else:
                return "O sol ja vai nascer. Ultima chance de dormir algo."

        self._proactivity.add_trigger(
            name="late_night", condition=is_late_night, message_generator=late_night_message, cooldown_minutes=120
        )

        if self._idle_detector:

            def is_long_idle():
                duration = self._idle_detector.get_idle_duration()
                if duration:
                    return duration.total_seconds() > 600
                return False

            def idle_message():
                return "Voce sumiu. Tudo bem por ai?"

            self._proactivity.add_trigger(
                name="long_idle", condition=is_long_idle, message_generator=idle_message, cooldown_minutes=60
            )

    def start(self):
        if self._notification_listener:
            self._notification_listener.start()
        if self._clipboard_monitor:
            self._clipboard_monitor.start()
        if self._window_tracker:
            self._window_tracker.start()
        if self._idle_detector:
            self._idle_detector.start()
        if self._proactivity:
            self._proactivity.start()

        logger.info("Desktop integration iniciada")

    def stop(self):
        if self._proactivity:
            self._proactivity.stop()
        if self._idle_detector:
            self._idle_detector.stop()
        if self._window_tracker:
            self._window_tracker.stop()
        if self._clipboard_monitor:
            self._clipboard_monitor.stop()
        if self._notification_listener:
            self._notification_listener.stop()

        logger.info("Desktop integration parada")

    def get_full_context(self) -> str:
        parts = []

        if self._window_tracker:
            ctx = self._window_tracker.get_context()
            if ctx:
                parts.append(ctx)

        if self._clipboard_monitor:
            ctx = self._clipboard_monitor.get_context()
            if ctx:
                parts.append(ctx)

        if self._idle_detector:
            ctx = self._idle_detector.get_context()
            if ctx:
                parts.append(ctx)

        if self._notification_listener:
            ctx = self._notification_listener.get_context()
            if ctx:
                parts.append(ctx)

        return "\n".join(parts)

    def get_active_window(self) -> WindowData | None:
        if self._window_tracker:
            return self._window_tracker.get_current()
        return None

    def get_clipboard(self) -> ClipboardData | None:
        if self._clipboard_monitor:
            return self._clipboard_monitor.get_current()
        return None

    def is_user_idle(self) -> bool:
        if self._idle_detector:
            return self._idle_detector.is_idle()
        return False

    def get_recent_notifications(self, count: int = 5) -> list[NotificationData]:
        if self._notification_listener:
            return self._notification_listener.get_recent(count)
        return []


_desktop_integration: DesktopIntegration | None = None


def get_desktop_integration() -> DesktopIntegration:
    global _desktop_integration
    if _desktop_integration is None:
        _desktop_integration = DesktopIntegration()
    return _desktop_integration


def check_desktop_tools() -> dict[str, bool]:
    tools = {"xclip": False, "xsel": False, "xdotool": False, "xprintidle": False, "dbus-monitor": False}

    for tool in tools.keys():
        try:
            result = subprocess.run(["which", tool], capture_output=True, timeout=2)
            tools[tool] = result.returncode == 0
        except Exception as e:
            logger.debug(f"Erro ao verificar ferramenta {tool}: {e}")

    return tools
