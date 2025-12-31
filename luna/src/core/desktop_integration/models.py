from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DesktopEvent(Enum):
    NOTIFICATION = "notification"
    CLIPBOARD_CHANGE = "clipboard_change"
    WINDOW_CHANGE = "window_change"
    IDLE_START = "idle_start"
    IDLE_END = "idle_end"
    MEDIA_PLAYING = "media_playing"
    MEDIA_PAUSED = "media_paused"


@dataclass
class NotificationData:
    app_name: str
    summary: str
    body: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_context(self) -> str:
        return f"[Notificacao de {self.app_name}] {self.summary}: {self.body[:100]}"


@dataclass
class WindowData:
    title: str
    app_class: str
    app_name: str
    pid: int = 0

    def to_context(self) -> str:
        return f"[Usuario em: {self.app_name}] {self.title[:80]}"


@dataclass
class ClipboardData:
    content: str
    content_type: str = "text"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_context(self) -> str:
        preview = self.content[:150] if len(self.content) > 150 else self.content
        return f"[Copiado para clipboard] {preview}"
