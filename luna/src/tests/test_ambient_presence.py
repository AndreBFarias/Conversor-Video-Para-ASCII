import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAmbientPresenceInit:
    def test_default_values(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()

        assert ap.idle_threshold == 5 * 60
        assert ap.spontaneous_chance == 0.02
        assert ap.check_interval == 30
        assert ap.is_idle is False
        assert ap.is_running is False

    def test_custom_values(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(
            idle_threshold_minutes=10,
            spontaneous_chance=0.05,
            check_interval_seconds=60,
        )

        assert ap.idle_threshold == 10 * 60
        assert ap.spontaneous_chance == 0.05
        assert ap.check_interval == 60

    def test_callbacks_stored(self):
        from src.core.ambient_presence import AmbientPresence

        idle_start = MagicMock()
        idle_end = MagicMock()
        spontaneous = MagicMock()
        animation = MagicMock()

        ap = AmbientPresence(
            on_idle_start=idle_start,
            on_idle_end=idle_end,
            on_spontaneous=spontaneous,
            on_animation_suggest=animation,
        )

        assert ap.on_idle_start is idle_start
        assert ap.on_idle_end is idle_end
        assert ap.on_spontaneous is spontaneous
        assert ap.on_animation_suggest is animation


class TestRecordActivity:
    def test_updates_last_activity(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()
        old_time = ap.last_activity

        time.sleep(0.1)
        ap.record_activity()

        assert ap.last_activity > old_time

    def test_clears_idle_state(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()
        ap.is_idle = True

        ap.record_activity()

        assert ap.is_idle is False

    def test_calls_on_idle_end_when_was_idle(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(on_idle_end=callback)
        ap.is_idle = True

        ap.record_activity()

        callback.assert_called_once()

    def test_no_callback_when_not_idle(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(on_idle_end=callback)
        ap.is_idle = False

        ap.record_activity()

        callback.assert_not_called()


class TestGetIdleSeconds:
    def test_returns_seconds_since_activity(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()
        ap.last_activity = datetime.now() - timedelta(seconds=60)

        idle_seconds = ap.get_idle_seconds()

        assert 59 <= idle_seconds <= 61


class TestStartStop:
    def test_start_sets_running(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(check_interval_seconds=1)

        ap.start()

        assert ap.is_running is True
        assert ap._thread is not None
        assert ap._thread.is_alive()

        ap.stop()

    def test_stop_clears_running(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(check_interval_seconds=1)
        ap.start()

        ap.stop()

        assert ap.is_running is False

    def test_double_start_ignored(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(check_interval_seconds=1)
        ap.start()
        first_thread = ap._thread

        ap.start()

        assert ap._thread is first_thread

        ap.stop()


class TestCheckIdle:
    def test_becomes_idle_after_threshold(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_idle_start=callback,
            idle_threshold_minutes=1,
        )
        ap.last_activity = datetime.now() - timedelta(seconds=70)

        ap._check_idle()

        assert ap.is_idle is True
        callback.assert_called_once()

    def test_not_idle_before_threshold(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_idle_start=callback,
            idle_threshold_minutes=5,
        )
        ap.last_activity = datetime.now() - timedelta(seconds=60)

        ap._check_idle()

        assert ap.is_idle is False
        callback.assert_not_called()

    def test_no_double_idle_callback(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_idle_start=callback,
            idle_threshold_minutes=1,
        )
        ap.last_activity = datetime.now() - timedelta(seconds=70)

        ap._check_idle()
        ap._check_idle()

        callback.assert_called_once()


class TestMaybeSpontaneous:
    def test_no_message_when_not_idle(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_spontaneous=callback,
            spontaneous_chance=1.0,
        )
        ap.is_idle = False

        ap._maybe_spontaneous()

        callback.assert_not_called()

    def test_message_when_idle_and_random_hits(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_spontaneous=callback,
            spontaneous_chance=1.0,
        )
        ap.is_idle = True

        with patch("random.random", return_value=0.5):
            ap._maybe_spontaneous()

        callback.assert_called_once()

    def test_no_message_when_random_misses(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_spontaneous=callback,
            spontaneous_chance=0.1,
        )
        ap.is_idle = True

        with patch("random.random", return_value=0.5):
            ap._maybe_spontaneous()

        callback.assert_not_called()


class TestUpdateAnimation:
    def test_suggests_idle_animation_when_idle(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(on_animation_suggest=callback)
        ap.is_idle = True

        with patch("random.choice", return_value="entediada"):
            ap._update_animation()

        callback.assert_called_with("entediada")

    def test_suggests_active_animation_when_active(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(on_animation_suggest=callback)
        ap.is_idle = False

        with patch("random.choice", return_value="feliz"):
            ap._update_animation()

        callback.assert_called_with("feliz")

    def test_no_callback_when_none(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(on_animation_suggest=None)

        ap._update_animation()

        assert ap.on_animation_suggest is None


class TestAddSpontaneousMessage:
    def test_adds_new_message(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()
        initial_count = len(ap.spontaneous_messages)

        ap.add_spontaneous_message("Nova mensagem teste")

        assert len(ap.spontaneous_messages) == initial_count + 1
        assert "Nova mensagem teste" in ap.spontaneous_messages

    def test_no_duplicate(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()
        existing = ap.spontaneous_messages[0]
        initial_count = len(ap.spontaneous_messages)

        ap.add_spontaneous_message(existing)

        assert len(ap.spontaneous_messages) == initial_count


class TestSetIdleThreshold:
    def test_updates_threshold(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()

        ap.set_idle_threshold(10)

        assert ap.idle_threshold == 600


class TestSetSpontaneousChance:
    def test_updates_chance(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()

        ap.set_spontaneous_chance(0.5)

        assert ap.spontaneous_chance == 0.5

    def test_clamps_to_valid_range(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence()

        ap.set_spontaneous_chance(1.5)
        assert ap.spontaneous_chance == 1.0

        ap.set_spontaneous_chance(-0.5)
        assert ap.spontaneous_chance == 0.0


class TestGetStatus:
    def test_returns_status_dict(self):
        from src.core.ambient_presence import AmbientPresence

        ap = AmbientPresence(
            idle_threshold_minutes=5,
            spontaneous_chance=0.02,
        )
        ap.is_running = True
        ap.is_idle = False

        status = ap.get_status()

        assert status["is_running"] is True
        assert status["is_idle"] is False
        assert status["idle_threshold"] == 300
        assert status["spontaneous_chance"] == 0.02
        assert "last_activity" in status
        assert "idle_seconds" in status


class TestCreateAmbientPresence:
    def test_creates_instance(self):
        from src.core.ambient_presence import create_ambient_presence

        mock_app = MagicMock()

        ap = create_ambient_presence(mock_app)

        assert ap is not None
        assert ap.idle_threshold == 300
        assert ap.spontaneous_chance == 0.02

    def test_callbacks_are_set(self):
        from src.core.ambient_presence import create_ambient_presence

        mock_app = MagicMock()

        ap = create_ambient_presence(mock_app)

        assert ap.on_idle_start is not None
        assert ap.on_idle_end is not None
        assert ap.on_spontaneous is not None
        assert ap.on_animation_suggest is not None


class TestGlobalFunctions:
    def test_get_and_set_ambient(self):
        from src.core.ambient_presence import (
            AmbientPresence,
            get_ambient_presence,
            set_ambient_presence,
        )

        ap = AmbientPresence()
        set_ambient_presence(ap)

        result = get_ambient_presence()

        assert result is ap


class TestMonitorLoop:
    def test_loop_runs_and_stops(self):
        from src.core.ambient_presence import AmbientPresence

        callback = MagicMock()
        ap = AmbientPresence(
            on_animation_suggest=callback,
            check_interval_seconds=1,
        )

        ap.start()
        time.sleep(1.5)
        ap.stop()

        assert callback.call_count >= 1

    def test_loop_detects_idle(self):
        from src.core.ambient_presence import AmbientPresence

        idle_callback = MagicMock()
        ap = AmbientPresence(
            on_idle_start=idle_callback,
            idle_threshold_minutes=0,
            check_interval_seconds=1,
        )
        ap.last_activity = datetime.now() - timedelta(seconds=10)

        ap.start()
        time.sleep(1.5)
        ap.stop()

        idle_callback.assert_called()
