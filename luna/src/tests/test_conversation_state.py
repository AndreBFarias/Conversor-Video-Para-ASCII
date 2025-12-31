from datetime import datetime, timedelta


class TestConversationState:
    def test_all_states_exist(self):
        from src.soul.conversation_state import ConversationState

        assert ConversationState.IDLE is not None
        assert ConversationState.GREETING is not None
        assert ConversationState.CHAT is not None
        assert ConversationState.TASK is not None
        assert ConversationState.DEEP_TALK is not None
        assert ConversationState.FLIRT is not None
        assert ConversationState.CONFLICT is not None
        assert ConversationState.FAREWELL is not None


class TestStatePatterns:
    def test_patterns_defined(self):
        from src.soul.conversation_state import STATE_PATTERNS, ConversationState

        assert ConversationState.GREETING in STATE_PATTERNS
        assert ConversationState.TASK in STATE_PATTERNS
        assert ConversationState.FAREWELL in STATE_PATTERNS


class TestConversationStateMachineInit:
    def test_initial_state(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        assert machine.current_state == ConversationState.IDLE
        assert machine.turn_count == 0
        assert len(machine.state_history) == 0

    def test_state_start_time_set(self):
        from src.soul.conversation_state import ConversationStateMachine

        before = datetime.now()
        machine = ConversationStateMachine()
        after = datetime.now()

        assert before <= machine.state_start_time <= after


class TestConversationStateMachineDetectState:
    def test_detects_greeting(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Ola, tudo bem?")

        assert result == ConversationState.GREETING

    def test_detects_task(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Preciso que voce crie um script")

        assert result == ConversationState.TASK

    def test_detects_farewell(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Tchau, ate mais")

        assert result == ConversationState.FAREWELL

    def test_detects_deep_talk(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Estou me sentindo triste hoje")

        assert result == ConversationState.DEEP_TALK

    def test_detects_flirt(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Voce e muito linda")

        assert result == ConversationState.FLIRT

    def test_detects_conflict(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.detect_state("Isso e ridiculo, voce esta errada")

        assert result == ConversationState.CONFLICT

    def test_defaults_to_greeting_on_first_turns(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.turn_count = 0

        result = machine.detect_state("Blablabla")

        assert result == ConversationState.GREETING

    def test_defaults_to_chat_after_turns(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.turn_count = 5

        result = machine.detect_state("Blablabla")

        assert result == ConversationState.CHAT


class TestConversationStateMachineTransition:
    def test_transition_increments_turn(self):
        from src.soul.conversation_state import ConversationStateMachine

        machine = ConversationStateMachine()

        machine.transition("Ola")

        assert machine.turn_count == 1

    def test_transition_updates_state(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()

        result = machine.transition("Ola")

        assert machine.current_state == ConversationState.GREETING
        assert result["changed"] is True

    def test_transition_records_history(self):
        from src.soul.conversation_state import ConversationStateMachine

        machine = ConversationStateMachine()

        machine.transition("Ola")

        assert len(machine.state_history) == 1
        assert machine.state_history[0]["from"] == "IDLE"
        assert machine.state_history[0]["to"] == "GREETING"

    def test_no_change_if_same_state(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.current_state = ConversationState.GREETING

        result = machine.transition("Oi, ola")

        assert result["changed"] is False


class TestConversationStateMachineGetStateContext:
    def test_returns_hint_for_state(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.current_state = ConversationState.DEEP_TALK

        result = machine.get_state_context()

        assert "empatica" in result.lower()

    def test_idle_returns_empty(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.current_state = ConversationState.IDLE

        result = machine.get_state_context()

        assert result == ""


class TestConversationStateMachineGetStateDuration:
    def test_returns_timedelta(self):
        from src.soul.conversation_state import ConversationStateMachine

        machine = ConversationStateMachine()
        machine.state_start_time = datetime.now() - timedelta(seconds=60)

        duration = machine.get_state_duration()

        assert duration.total_seconds() >= 59


class TestConversationStateMachineGetHistory:
    def test_returns_copy(self):
        from src.soul.conversation_state import ConversationStateMachine

        machine = ConversationStateMachine()
        machine.state_history = [{"test": "data"}]

        history = machine.get_history()
        history.append({"new": "item"})

        assert len(machine.state_history) == 1


class TestConversationStateMachineReset:
    def test_resets_all_state(self):
        from src.soul.conversation_state import ConversationState, ConversationStateMachine

        machine = ConversationStateMachine()
        machine.current_state = ConversationState.TASK
        machine.turn_count = 10
        machine.state_history = [{"test": "data"}]

        machine.reset()

        assert machine.current_state == ConversationState.IDLE
        assert machine.turn_count == 0
        assert len(machine.state_history) == 0


class TestGlobalFunctions:
    def test_get_conversation_state_machine_singleton(self):
        import src.soul.conversation_state as module

        module._state_machine = None

        from src.soul.conversation_state import get_conversation_state_machine

        m1 = get_conversation_state_machine()
        m2 = get_conversation_state_machine()

        assert m1 is m2

    def test_reset_conversation_state(self):
        from src.soul.conversation_state import (
            ConversationState,
            get_conversation_state_machine,
            reset_conversation_state,
        )

        machine = get_conversation_state_machine()
        machine.current_state = ConversationState.TASK
        machine.turn_count = 5

        reset_conversation_state()

        assert machine.current_state == ConversationState.IDLE
        assert machine.turn_count == 0
