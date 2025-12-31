from .manager import ReminderManager
from .models import Reminder
from .parser import ReminderParser

_reminder_manager: ReminderManager | None = None


def get_reminder_manager() -> ReminderManager:
    global _reminder_manager
    if _reminder_manager is None:
        _reminder_manager = ReminderManager()
    return _reminder_manager


def create_reminder_from_text(text: str, entity_id: str = "luna") -> Reminder | None:
    return get_reminder_manager().add_from_text(text, entity_id)


def is_reminder_request(text: str) -> bool:
    return ReminderParser.is_reminder_request(text)
