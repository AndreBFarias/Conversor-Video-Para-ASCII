from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum


class ReminderStatus(Enum):
    PENDING = "pending"
    TRIGGERED = "triggered"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


@dataclass
class Reminder:
    id: str
    message: str
    trigger_time: str
    created_at: str
    entity_id: str
    status: str = "pending"
    repeat: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(**data)

    def is_due(self) -> bool:
        if self.status != "pending":
            return False
        trigger = datetime.fromisoformat(self.trigger_time)
        return datetime.now() >= trigger

    def get_time_until(self) -> timedelta:
        trigger = datetime.fromisoformat(self.trigger_time)
        return trigger - datetime.now()
