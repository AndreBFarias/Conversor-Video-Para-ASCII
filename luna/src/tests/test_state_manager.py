from unittest.mock import MagicMock


class TestAppModeEnum:
    def test_modes_exist(self):
        from src.app.state_manager import AppMode

        assert AppMode.IDLE is not None
        assert AppMode.BUSY is not None
        assert AppMode.RECORDING is not None
        assert AppMode.PROCESSING is not None

    def test_modes_are_different(self):
        from src.app.state_manager import AppMode

        modes = [AppMode.IDLE, AppMode.BUSY, AppMode.RECORDING, AppMode.PROCESSING]

        assert len(set(modes)) == 4


class TestAppStateDataclass:
    def test_default_values(self):
        from src.app.state_manager import AppMode, AppState

        state = AppState()

        assert state.mode == AppMode.IDLE
        assert state.em_chamada is False
        assert state.is_speaking is False
        assert state.is_looping_olhar is False

    def test_custom_values(self):
        from src.app.state_manager import AppMode, AppState

        state = AppState(mode=AppMode.BUSY, em_chamada=True, is_speaking=True, is_looping_olhar=True)

        assert state.mode == AppMode.BUSY
        assert state.em_chamada is True
        assert state.is_speaking is True
        assert state.is_looping_olhar is True


class TestStateManagerInit:
    def test_creates_instance(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        assert manager is not None
        assert manager._observers == []

    def test_initial_mode_is_idle(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()

        assert manager.mode == AppMode.IDLE


class TestStateManagerProperties:
    def test_is_idle(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        assert manager.is_idle is True
        assert manager.is_busy is False

    def test_em_chamada_getter_setter(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        assert manager.em_chamada is False
        manager.em_chamada = True
        assert manager.em_chamada is True

    def test_is_speaking_getter_setter(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        assert manager.is_speaking is False
        manager.is_speaking = True
        assert manager.is_speaking is True

    def test_is_looping_olhar_getter_setter(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        assert manager.is_looping_olhar is False
        manager.is_looping_olhar = True
        assert manager.is_looping_olhar is True


class TestStateManagerTransitions:
    def test_idle_to_busy(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()

        result = manager.transition_to(AppMode.BUSY)

        assert result is True
        assert manager.mode == AppMode.BUSY

    def test_idle_to_recording(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()

        result = manager.transition_to(AppMode.RECORDING)

        assert result is True
        assert manager.mode == AppMode.RECORDING

    def test_idle_to_processing(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()

        result = manager.transition_to(AppMode.PROCESSING)

        assert result is True
        assert manager.mode == AppMode.PROCESSING

    def test_invalid_transition_returns_false(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.BUSY)

        result = manager.transition_to(AppMode.RECORDING)

        assert result is False
        assert manager.mode == AppMode.BUSY

    def test_same_state_transition_allowed(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()

        result = manager.transition_to(AppMode.IDLE)

        assert result is True
        assert manager.mode == AppMode.IDLE

    def test_busy_to_idle(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.BUSY)

        result = manager.transition_to(AppMode.IDLE)

        assert result is True
        assert manager.mode == AppMode.IDLE

    def test_busy_to_processing(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.BUSY)

        result = manager.transition_to(AppMode.PROCESSING)

        assert result is True
        assert manager.mode == AppMode.PROCESSING

    def test_processing_to_idle(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.PROCESSING)

        result = manager.transition_to(AppMode.IDLE)

        assert result is True
        assert manager.mode == AppMode.IDLE


class TestStateManagerForceIdle:
    def test_forces_idle_from_busy(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.BUSY)

        manager.force_idle()

        assert manager.mode == AppMode.IDLE

    def test_forces_idle_from_processing(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        manager.transition_to(AppMode.PROCESSING)

        manager.force_idle()

        assert manager.mode == AppMode.IDLE


class TestStateManagerObservers:
    def test_subscribe(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        callback = MagicMock()

        manager.subscribe(callback)

        assert callback in manager._observers

    def test_unsubscribe(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        callback = MagicMock()
        manager.subscribe(callback)

        manager.unsubscribe(callback)

        assert callback not in manager._observers

    def test_unsubscribe_nonexistent(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        callback = MagicMock()

        manager.unsubscribe(callback)

        assert callback not in manager._observers

    def test_notify_on_transition(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        callback = MagicMock()
        manager.subscribe(callback)

        manager.transition_to(AppMode.BUSY)

        callback.assert_called_once()

    def test_notify_on_em_chamada_change(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        callback = MagicMock()
        manager.subscribe(callback)

        manager.em_chamada = True

        callback.assert_called_once()

    def test_notify_on_is_speaking_change(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        callback = MagicMock()
        manager.subscribe(callback)

        manager.is_speaking = True

        callback.assert_called_once()

    def test_observer_exception_handled(self):
        from src.app.state_manager import AppMode, StateManager

        manager = StateManager()
        callback = MagicMock(side_effect=Exception("Observer error"))
        manager.subscribe(callback)

        manager.transition_to(AppMode.BUSY)

        assert manager.mode == AppMode.BUSY


class TestStateManagerGetStateSnapshot:
    def test_returns_dict(self):
        from src.app.state_manager import StateManager

        manager = StateManager()

        snapshot = manager.get_state_snapshot()

        assert isinstance(snapshot, dict)
        assert "mode" in snapshot
        assert "em_chamada" in snapshot
        assert "is_speaking" in snapshot
        assert "is_looping_olhar" in snapshot

    def test_snapshot_values(self):
        from src.app.state_manager import StateManager

        manager = StateManager()
        manager.em_chamada = True
        manager.is_speaking = True

        snapshot = manager.get_state_snapshot()

        assert snapshot["mode"] == "IDLE"
        assert snapshot["em_chamada"] is True
        assert snapshot["is_speaking"] is True
        assert snapshot["is_looping_olhar"] is False
