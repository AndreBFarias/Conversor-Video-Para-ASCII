import re
from datetime import datetime, timedelta
from typing import Any


class ReminderParser:
    TIME_PATTERNS = [
        (r"em (\d+)\s*(minuto|min|m)s?", "minutes"),
        (r"em (\d+)\s*(hora|h)s?", "hours"),
        (r"em (\d+)\s*(dia|d)s?", "days"),
        (r"em (\d+)\s*(semana|sem)s?", "weeks"),
        (r"daqui a (\d+)\s*(minuto|min|m)s?", "minutes"),
        (r"daqui a (\d+)\s*(hora|h)s?", "hours"),
        (r"daqui (\d+)\s*(minuto|min|m)s?", "minutes"),
        (r"daqui (\d+)\s*(hora|h)s?", "hours"),
        (r"as (\d{1,2}):(\d{2})", "time"),
        (r"às (\d{1,2}):(\d{2})", "time"),
        (r"(\d{1,2}):(\d{2})", "time"),
        (r"amanha", "tomorrow"),
        (r"amanhã", "tomorrow"),
        (r"depois de amanha", "day_after"),
        (r"depois de amanhã", "day_after"),
    ]

    TRIGGER_WORDS = ["me lembre", "lembre-me", "lembrete", "me avise", "avise-me", "me notifique", "alarme", "timer"]

    @classmethod
    def is_reminder_request(cls, text: str) -> bool:
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in cls.TRIGGER_WORDS)

    @classmethod
    def parse(cls, text: str) -> dict[str, Any] | None:
        text_lower = text.lower()

        trigger_time = None
        message = text

        for trigger in cls.TRIGGER_WORDS:
            if trigger in text_lower:
                idx = text_lower.find(trigger)
                message = text[idx + len(trigger) :].strip()
                break

        for pattern, time_type in cls.TIME_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                if time_type == "minutes":
                    amount = int(match.group(1))
                    trigger_time = datetime.now() + timedelta(minutes=amount)
                elif time_type == "hours":
                    amount = int(match.group(1))
                    trigger_time = datetime.now() + timedelta(hours=amount)
                elif time_type == "days":
                    amount = int(match.group(1))
                    trigger_time = datetime.now() + timedelta(days=amount)
                elif time_type == "weeks":
                    amount = int(match.group(1))
                    trigger_time = datetime.now() + timedelta(weeks=amount)
                elif time_type == "time":
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    target = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target <= datetime.now():
                        target += timedelta(days=1)
                    trigger_time = target
                elif time_type == "tomorrow":
                    trigger_time = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1)
                elif time_type == "day_after":
                    trigger_time = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=2)
                break

        if trigger_time is None:
            trigger_time = datetime.now() + timedelta(hours=1)

        message = re.sub(r"em \d+\s*(minuto|min|m|hora|h|dia|d|semana|sem)s?", "", message, flags=re.IGNORECASE)
        message = re.sub(r"daqui a? \d+\s*(minuto|min|m|hora|h)s?", "", message, flags=re.IGNORECASE)
        message = re.sub(r"[àa]s \d{1,2}:\d{2}", "", message, flags=re.IGNORECASE)
        message = re.sub(r"amanha|amanhã|depois de amanha|depois de amanhã", "", message, flags=re.IGNORECASE)
        message = re.sub(r"\s+", " ", message).strip()

        prepositions = ["de", "que", "para", "sobre", "a", "o"]
        for prep in prepositions:
            if message.lower().startswith(prep + " "):
                message = message[len(prep) + 1 :]

        return {"message": message.strip() or "Lembrete", "trigger_time": trigger_time.isoformat()}
