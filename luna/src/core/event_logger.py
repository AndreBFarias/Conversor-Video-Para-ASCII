import json
import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import config

logger = logging.getLogger(__name__)


class EventType(Enum):
    CLICK = "click"
    INPUT = "input"
    VOICE = "voice"
    VISION = "vision"
    TTS = "tts"
    TRANSCRIPTION = "transcription"
    LLM = "llm"
    ERROR = "error"
    STATE = "state"
    SYSTEM = "system"


@dataclass
class UIEvent:
    timestamp: str
    event_type: str
    component: str
    action: str
    details: dict[str, Any] | None = None
    success: bool = True
    error_msg: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_log_line(self) -> str:
        ts = self.timestamp.split("T")[1][:12]
        status = "OK" if self.success else "FAIL"
        duration = f" ({self.duration_ms:.0f}ms)" if self.duration_ms else ""
        error = f" | {self.error_msg}" if self.error_msg else ""
        details_str = ""
        if self.details:
            details_str = " | " + ", ".join(f"{k}={v}" for k, v in self.details.items() if v)
        return (
            f"[{ts}] [{status}] {self.event_type.upper()}: {self.component}.{self.action}{duration}{details_str}{error}"
        )


class EventLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_events: int = 500, log_to_file: bool = True):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._events: deque = deque(maxlen=max_events)
        self._session_start = datetime.now()
        self._event_count = 0
        self._error_count = 0
        self._log_to_file = log_to_file

        self._log_dir = config.APP_DIR / "src" / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

        session_id = self._session_start.strftime("%Y%m%d_%H%M%S")
        self._event_log_path = self._log_dir / f"events_{session_id}.log"
        self._event_json_path = self._log_dir / f"events_{session_id}.json"

        self._file_lock = threading.Lock()
        self._initialized = True

        self._log_system_event("session_start", {"session_id": session_id, "log_path": str(self._event_log_path)})

        logger.info(f"EventLogger iniciado: {self._event_log_path}")

    def log(
        self,
        event_type: EventType,
        component: str,
        action: str,
        details: dict[str, Any] | None = None,
        success: bool = True,
        error_msg: str | None = None,
        duration_ms: float | None = None,
    ) -> UIEvent:
        event = UIEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type.value,
            component=component,
            action=action,
            details=details,
            success=success,
            error_msg=error_msg,
            duration_ms=duration_ms,
        )

        self._events.append(event)
        self._event_count += 1

        if not success:
            self._error_count += 1

        log_line = event.to_log_line()
        logger.info(f"[EVENT] {log_line}")

        if self._log_to_file:
            self._write_to_file(event)

        return event

    def click(self, component: str, button_id: str = None, details: dict = None):
        return self.log(EventType.CLICK, component, button_id or "click", details)

    def input(self, component: str, action: str, text_len: int = 0, details: dict = None):
        d = details or {}
        d["text_len"] = text_len
        return self.log(EventType.INPUT, component, action, d)

    def voice(
        self, action: str, success: bool = True, error_msg: str = None, duration_ms: float = None, details: dict = None
    ):
        return self.log(EventType.VOICE, "audio", action, details, success, error_msg, duration_ms)

    def vision(
        self, action: str, success: bool = True, error_msg: str = None, duration_ms: float = None, details: dict = None
    ):
        return self.log(EventType.VISION, "camera", action, details, success, error_msg, duration_ms)

    def tts(
        self, action: str, success: bool = True, error_msg: str = None, duration_ms: float = None, details: dict = None
    ):
        return self.log(EventType.TTS, "boca", action, details, success, error_msg, duration_ms)

    def transcription(self, text: str, success: bool = True, duration_ms: float = None, details: dict = None):
        d = details or {}
        d["text_preview"] = text[:30] + "..." if len(text) > 30 else text
        return self.log(EventType.TRANSCRIPTION, "whisper", "transcribe", d, success, duration_ms=duration_ms)

    def llm(
        self,
        action: str,
        provider: str,
        success: bool = True,
        error_msg: str = None,
        duration_ms: float = None,
        details: dict = None,
    ):
        d = details or {}
        d["provider"] = provider
        return self.log(EventType.LLM, "consciencia", action, d, success, error_msg, duration_ms)

    def error(self, component: str, action: str, error_msg: str, details: dict = None):
        return self.log(EventType.ERROR, component, action, details, False, error_msg)

    def state(self, component: str, old_state: str, new_state: str, details: dict = None):
        d = details or {}
        d["from"] = old_state
        d["to"] = new_state
        return self.log(EventType.STATE, component, "state_change", d)

    def _log_system_event(self, action: str, details: dict = None):
        return self.log(EventType.SYSTEM, "event_logger", action, details)

    def _write_to_file(self, event: UIEvent):
        with self._file_lock:
            try:
                with open(self._event_log_path, "a", encoding="utf-8") as f:
                    f.write(event.to_log_line() + "\n")
            except Exception as e:
                logger.warning(f"Erro ao escrever log de evento: {e}")

    def get_recent_events(self, count: int = 20, event_type: EventType = None) -> list[UIEvent]:
        events = list(self._events)
        if event_type:
            events = [e for e in events if e.event_type == event_type.value]
        return events[-count:]

    def get_event_sequence(self, last_n: int = 10) -> str:
        events = self.get_recent_events(last_n)
        if not events:
            return "Nenhum evento registrado"

        lines = ["=== SEQUENCIA DE EVENTOS ==="]
        for i, e in enumerate(events, 1):
            lines.append(f"{i}. {e.to_log_line()}")
        return "\n".join(lines)

    def get_error_summary(self) -> str:
        errors = [e for e in self._events if not e.success]
        if not errors:
            return "Nenhum erro registrado"

        lines = [f"=== ERROS ({len(errors)} total) ==="]
        for e in errors[-10:]:
            lines.append(e.to_log_line())
        return "\n".join(lines)

    def get_stats(self) -> dict[str, Any]:
        events = list(self._events)
        type_counts = {}
        for e in events:
            type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1

        return {
            "session_start": self._session_start.isoformat(),
            "total_events": self._event_count,
            "total_errors": self._error_count,
            "events_by_type": type_counts,
            "log_path": str(self._event_log_path),
        }

    def save_session(self):
        self._log_system_event("session_save", {"event_count": self._event_count})

        try:
            with open(self._event_json_path, "w", encoding="utf-8") as f:
                data = {
                    "session_start": self._session_start.isoformat(),
                    "session_end": datetime.now().isoformat(),
                    "stats": self.get_stats(),
                    "events": [e.to_dict() for e in self._events],
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Sessao salva: {self._event_json_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar sessao: {e}")

    def flush(self):
        self.save_session()


_event_logger: EventLogger | None = None


def get_event_logger() -> EventLogger:
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger()
    return _event_logger
