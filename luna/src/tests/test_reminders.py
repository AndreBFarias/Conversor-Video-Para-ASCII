import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestReminderStatus:
    def test_all_statuses_exist(self):
        from src.soul.reminders import ReminderStatus

        assert ReminderStatus.PENDING.value == "pending"
        assert ReminderStatus.TRIGGERED.value == "triggered"
        assert ReminderStatus.DISMISSED.value == "dismissed"
        assert ReminderStatus.EXPIRED.value == "expired"


class TestReminder:
    def test_create_reminder(self):
        from src.soul.reminders import Reminder

        reminder = Reminder(
            id="test_001",
            message="Test reminder",
            trigger_time="2024-12-28T10:00:00",
            created_at="2024-12-28T09:00:00",
            entity_id="luna",
        )

        assert reminder.id == "test_001"
        assert reminder.message == "Test reminder"
        assert reminder.status == "pending"

    def test_to_dict(self):
        from src.soul.reminders import Reminder

        reminder = Reminder(
            id="test_001",
            message="Test",
            trigger_time="2024-12-28T10:00:00",
            created_at="2024-12-28T09:00:00",
            entity_id="luna",
        )

        data = reminder.to_dict()

        assert data["id"] == "test_001"
        assert data["message"] == "Test"

    def test_from_dict(self):
        from src.soul.reminders import Reminder

        data = {
            "id": "test_001",
            "message": "Test",
            "trigger_time": "2024-12-28T10:00:00",
            "created_at": "2024-12-28T09:00:00",
            "entity_id": "luna",
            "status": "pending",
            "repeat": None,
        }

        reminder = Reminder.from_dict(data)

        assert reminder.id == "test_001"

    def test_is_due_when_past(self):
        from src.soul.reminders import Reminder

        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        reminder = Reminder(
            id="test",
            message="Test",
            trigger_time=past_time,
            created_at=past_time,
            entity_id="luna",
            status="pending",
        )

        assert reminder.is_due() is True

    def test_is_due_when_future(self):
        from src.soul.reminders import Reminder

        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = Reminder(
            id="test",
            message="Test",
            trigger_time=future_time,
            created_at=datetime.now().isoformat(),
            entity_id="luna",
            status="pending",
        )

        assert reminder.is_due() is False

    def test_is_due_not_pending(self):
        from src.soul.reminders import Reminder

        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        reminder = Reminder(
            id="test",
            message="Test",
            trigger_time=past_time,
            created_at=past_time,
            entity_id="luna",
            status="triggered",
        )

        assert reminder.is_due() is False

    def test_get_time_until(self):
        from src.soul.reminders import Reminder

        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = Reminder(
            id="test",
            message="Test",
            trigger_time=future_time,
            created_at=datetime.now().isoformat(),
            entity_id="luna",
        )

        time_until = reminder.get_time_until()

        assert 3500 < time_until.total_seconds() < 3700


class TestReminderParser:
    def test_is_reminder_request_true(self):
        from src.soul.reminders import ReminderParser

        assert ReminderParser.is_reminder_request("Me lembre de comprar leite") is True
        assert ReminderParser.is_reminder_request("Lembrete de reuniao") is True
        assert ReminderParser.is_reminder_request("Me avise em 5 minutos") is True

    def test_is_reminder_request_false(self):
        from src.soul.reminders import ReminderParser

        assert ReminderParser.is_reminder_request("Qual e a hora?") is False
        assert ReminderParser.is_reminder_request("Ola, como vai?") is False

    def test_parse_minutes(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Me lembre em 30 minutos de beber agua")

        assert result is not None
        assert "trigger_time" in result
        trigger = datetime.fromisoformat(result["trigger_time"])
        assert (trigger - datetime.now()).total_seconds() > 1700

    def test_parse_hours(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Me lembre em 2 horas de algo")

        assert result is not None
        trigger = datetime.fromisoformat(result["trigger_time"])
        assert (trigger - datetime.now()).total_seconds() > 7000

    def test_parse_tomorrow(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Me lembre amanha de comprar")

        assert result is not None
        trigger = datetime.fromisoformat(result["trigger_time"])
        assert trigger.day != datetime.now().day

    def test_parse_specific_time(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Me lembre as 15:30 de reuniao")

        assert result is not None
        trigger = datetime.fromisoformat(result["trigger_time"])
        assert trigger.hour == 15
        assert trigger.minute == 30

    def test_parse_cleans_message(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Me lembre em 5 minutos de beber agua")

        assert "5 minutos" not in result["message"]

    def test_parse_default_hour(self):
        from src.soul.reminders import ReminderParser

        result = ReminderParser.parse("Lembrete de teste")

        assert result is not None
        trigger = datetime.fromisoformat(result["trigger_time"])
        assert (trigger - datetime.now()).total_seconds() > 3500


class TestReminderManager:
    def test_singleton(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    m1 = ReminderManager()
                    m2 = ReminderManager()

                    assert m1 is m2

    def test_add_reminder(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    trigger_time = datetime.now() + timedelta(hours=1)

                    reminder = manager.add("Test message", trigger_time)

                    assert reminder is not None
                    assert reminder.message == "Test message"
                    assert len(manager.reminders) == 1

    def test_get_pending(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    manager.add("Test 1", datetime.now() + timedelta(hours=1))
                    manager.add("Test 2", datetime.now() + timedelta(hours=2), entity_id="eris")

                    all_pending = manager.get_pending()
                    luna_pending = manager.get_pending(entity_id="luna")

                    assert len(all_pending) == 2
                    assert len(luna_pending) == 1

    def test_dismiss_reminder(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    reminder = manager.add("Test", datetime.now() + timedelta(hours=1))

                    result = manager.dismiss(reminder.id)

                    assert result is True
                    assert reminder.status == "dismissed"

    def test_trigger_reminder(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    reminder = manager.add("Test", datetime.now() + timedelta(hours=1))

                    result = manager.trigger(reminder.id)

                    assert result is True
                    assert reminder.status == "triggered"

    def test_register_callback(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    callback = MagicMock()

                    manager.register_callback(callback)
                    reminder = manager.add("Test", datetime.now() + timedelta(hours=1))
                    manager.trigger(reminder.id)

                    callback.assert_called_once()

    def test_format_reminder_list_empty(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()

                    result = manager.format_reminder_list()

                    assert "Nenhum lembrete" in result

    def test_format_reminder_list_with_items(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import ReminderManager

                    manager = ReminderManager()
                    manager.add("Beber agua", datetime.now() + timedelta(hours=1))

                    result = manager.format_reminder_list()

                    assert "Beber agua" in result
                    assert "pendentes" in result.lower()


class TestGlobalFunctions:
    def test_is_reminder_request(self):
        from src.soul.reminders import is_reminder_request

        assert is_reminder_request("Me lembre de algo") is True
        assert is_reminder_request("Como esta o tempo?") is False

    def test_create_reminder_from_text(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import create_reminder_from_text

                    reminder = create_reminder_from_text("Me lembre em 5 minutos de beber agua")

                    assert reminder is not None

    def test_create_reminder_from_text_not_request(self):
        import src.soul.reminders as module

        module._reminder_manager = None
        module.ReminderManager._instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.reminders.manager.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)
                with patch("src.soul.reminders.manager.REMINDERS_PATH", Path(tmpdir) / "reminders.json"):
                    from src.soul.reminders import create_reminder_from_text

                    reminder = create_reminder_from_text("Ola, como vai?")

                    assert reminder is None
