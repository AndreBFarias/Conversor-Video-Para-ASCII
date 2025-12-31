"""
Desktop Integration - Integracao com ambiente desktop Linux.

Monitora eventos do sistema:
- Notificacoes via D-Bus
- Clipboard via xclip/xsel
- Janela ativa via xdotool
- Tempo de inatividade via xprintidle
- Proatividade baseada em triggers

Classes principais:
    DesktopIntegration: Gerenciador central
    DBusNotificationListener: Monitor de notificacoes
    ClipboardMonitor: Monitor de clipboard
    ActiveWindowTracker: Monitor de janela ativa
    IdleDetector: Detector de inatividade
    ProactivityManager: Gerenciador de proatividade

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/core/desktop_integration/
"""

from src.core.desktop_integration import (
    ActiveWindowTracker,
    ClipboardData,
    ClipboardMonitor,
    DBusNotificationListener,
    DesktopEvent,
    DesktopIntegration,
    IdleDetector,
    NotificationData,
    ProactivityManager,
    WindowData,
    check_desktop_tools,
    get_desktop_integration,
)

__all__ = [
    "DesktopEvent",
    "NotificationData",
    "WindowData",
    "ClipboardData",
    "DBusNotificationListener",
    "ClipboardMonitor",
    "ActiveWindowTracker",
    "IdleDetector",
    "ProactivityManager",
    "DesktopIntegration",
    "get_desktop_integration",
    "check_desktop_tools",
]
