import json
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta

import config

from .models import Reminder
from .parser import ReminderParser

logger = logging.getLogger(__name__)

REMINDERS_PATH = config.APP_DIR / "src" / "data_memory" / "reminders.json"


class ReminderManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.reminders: list[Reminder] = []
        self._callbacks: list[Callable[[Reminder], None]] = []
        self._check_thread: threading.Thread | None = None
        self._running = False
        self._check_interval = 30

        self._load_from_disk()
        self._initialized = True

        logger.info(f"ReminderManager inicializado: {len(self.reminders)} lembretes pendentes")

    def _load_from_disk(self):
        if REMINDERS_PATH.exists():
            try:
                with open(REMINDERS_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    self.reminders = [Reminder.from_dict(r) for r in data.get("reminders", [])]
            except Exception as e:
                logger.error(f"Erro ao carregar lembretes: {e}")
                self.reminders = []

    def _save_to_disk(self):
        try:
            REMINDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {"reminders": [r.to_dict() for r in self.reminders], "last_updated": datetime.now().isoformat()}
            with open(REMINDERS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar lembretes: {e}")

    def add(self, message: str, trigger_time: datetime, entity_id: str = "luna", repeat: str | None = None) -> Reminder:
        reminder_id = f"rem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.reminders)}"

        reminder = Reminder(
            id=reminder_id,
            message=message,
            trigger_time=trigger_time.isoformat(),
            created_at=datetime.now().isoformat(),
            entity_id=entity_id,
            status="pending",
            repeat=repeat,
        )

        self.reminders.append(reminder)
        self._save_to_disk()

        logger.info(f"Lembrete criado: {reminder_id} - '{message}' para {trigger_time}")
        return reminder

    def add_from_text(self, text: str, entity_id: str = "luna") -> Reminder | None:
        if not ReminderParser.is_reminder_request(text):
            return None

        parsed = ReminderParser.parse(text)
        if not parsed:
            return None

        trigger_time = datetime.fromisoformat(parsed["trigger_time"])
        return self.add(message=parsed["message"], trigger_time=trigger_time, entity_id=entity_id)

    def get_pending(self, entity_id: str | None = None) -> list[Reminder]:
        pending = [r for r in self.reminders if r.status == "pending"]
        if entity_id:
            pending = [r for r in pending if r.entity_id == entity_id]
        return sorted(pending, key=lambda r: r.trigger_time)

    def get_due(self) -> list[Reminder]:
        return [r for r in self.reminders if r.is_due()]

    def dismiss(self, reminder_id: str) -> bool:
        for r in self.reminders:
            if r.id == reminder_id:
                r.status = "dismissed"
                self._save_to_disk()
                return True
        return False

    def trigger(self, reminder_id: str) -> bool:
        for r in self.reminders:
            if r.id == reminder_id:
                r.status = "triggered"
                self._save_to_disk()

                for callback in self._callbacks:
                    try:
                        callback(r)
                    except Exception as e:
                        logger.error(f"Erro em callback de lembrete: {e}")

                return True
        return False

    def register_callback(self, callback: Callable[[Reminder], None]):
        self._callbacks.append(callback)

    def start_checking(self):
        if self._running:
            return

        self._running = True
        self._check_thread = threading.Thread(target=self._check_loop, daemon=True, name="ReminderChecker")
        self._check_thread.start()
        logger.info("ReminderChecker iniciado")

    def stop_checking(self):
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
            self._check_thread = None
        logger.info("ReminderChecker parado")

    def _check_loop(self):
        while self._running:
            try:
                due_reminders = self.get_due()
                for reminder in due_reminders:
                    self.trigger(reminder.id)
                    logger.info(f"Lembrete disparado: {reminder.id} - {reminder.message}")
            except Exception as e:
                logger.error(f"Erro no check de lembretes: {e}")

            time.sleep(self._check_interval)

    def cleanup_old(self, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        initial = len(self.reminders)

        self.reminders = [
            r for r in self.reminders if r.status == "pending" or datetime.fromisoformat(r.created_at) > cutoff
        ]

        deleted = initial - len(self.reminders)
        if deleted > 0:
            self._save_to_disk()
            logger.info(f"Removidos {deleted} lembretes antigos")

        return deleted

    def format_reminder_list(self, entity_id: str | None = None) -> str:
        pending = self.get_pending(entity_id)

        if not pending:
            return "Nenhum lembrete pendente."

        lines = ["Lembretes pendentes:"]
        for r in pending[:10]:
            time_until = r.get_time_until()
            if time_until.total_seconds() < 0:
                time_str = "agora"
            elif time_until.total_seconds() < 3600:
                time_str = f"em {int(time_until.total_seconds() / 60)} min"
            elif time_until.total_seconds() < 86400:
                time_str = f"em {int(time_until.total_seconds() / 3600)} h"
            else:
                time_str = f"em {int(time_until.total_seconds() / 86400)} dias"

            lines.append(f"  - {r.message} ({time_str})")

        return "\n".join(lines)
