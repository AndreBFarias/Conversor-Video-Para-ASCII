import pytest


class TestContextBuilder:
    def test_import(self):
        from src.soul.context_builder import ContextBudget, ContextBuilder

        assert ContextBuilder is not None
        assert ContextBudget is not None

    def test_build_context(self):
        from src.soul.context_builder import get_context_builder

        builder = get_context_builder("luna")
        ctx = builder.build("Ola", [])

        assert ctx.system_prompt
        assert ctx.total_estimated_tokens > 0

    def test_budget_truncation(self):
        from src.soul.context_builder import ContextBudget, get_context_builder

        small_budget = ContextBudget(total_tokens=100, system_prompt=50, memory=20, conversation=20, user_input=10)

        builder = get_context_builder("luna")
        builder.budget = small_budget

        ctx = builder.build("Uma mensagem muito longa que deveria ser truncada", [])

        assert ctx.total_estimated_tokens <= small_budget.total_tokens * 2


class TestResponsePipeline:
    def test_import(self):
        from src.soul.response_pipeline import PipelineResult, PipelineStage

        assert PipelineStage is not None
        assert PipelineResult is not None

    def test_pipeline_with_mock_llm(self):
        from src.soul.response_pipeline import get_response_pipeline

        pipeline = get_response_pipeline("luna")

        def mock_llm(prompt):
            return '{"fala_tts": "Test", "animacao": "Luna_observando", "log_terminal": ""}'

        pipeline.set_llm_caller(mock_llm)
        result = pipeline.process("Test")

        assert result.success
        assert result.parsed_response

    def test_pipeline_stages(self):
        from src.soul.response_pipeline import PipelineStage

        stages = list(PipelineStage)
        assert len(stages) == 5
        assert PipelineStage.CONTEXT_BUILD in stages
        assert PipelineStage.MEMORY_UPDATE in stages


class TestEntityHotSwap:
    def test_import(self):
        from src.soul.entity_hotswap import EntityHotSwap

        assert EntityHotSwap is not None

    def test_initialize(self):
        from src.soul.entity_hotswap import get_entity_hotswap, reset_hotswap

        reset_hotswap()
        hs = get_entity_hotswap()
        hs.initialize("luna")

        assert hs.current_entity == "luna"

    def test_can_swap_to(self):
        from src.soul.entity_hotswap import get_entity_hotswap

        hs = get_entity_hotswap()
        hs.initialize("luna")

        check = hs.can_swap_to("eris")
        assert "can_swap" in check
        assert "checks" in check

    def test_swap_entities(self):
        from src.soul.entity_hotswap import get_entity_hotswap

        hs = get_entity_hotswap()
        hs.initialize("luna")

        result = hs.swap("eris", reason="test")
        assert result["success"]
        assert hs.current_entity == "eris"

    def test_swap_history(self):
        from src.soul.entity_hotswap import get_entity_hotswap, reset_hotswap

        reset_hotswap()
        hs = get_entity_hotswap()
        hs.initialize("luna")
        hs.swap("eris", reason="test")

        history = hs.get_swap_history()
        assert len(history) >= 1
        assert history[-1]["to"] == "eris"


class TestPersonalityGuard:
    def test_import(self):
        from src.soul.personality_guard import ENTITY_MARKERS, PersonalityGuard

        assert PersonalityGuard is not None
        assert "luna" in ENTITY_MARKERS

    def test_validates_correct_personality(self):
        from src.soul.personality_guard import get_personality_guard

        guard = get_personality_guard("luna")
        check = guard.check_response("Nas sombras sussurro verdades...")

        assert check["valid"]
        assert check["score"] > 0

    def test_validate_animation(self):
        from src.soul.personality_guard import get_personality_guard

        guard = get_personality_guard("luna")

        assert guard.validate_animation("Luna_observando")
        assert not guard.validate_animation("Eris_observando")

    def test_fix_animation_prefix(self):
        from src.soul.personality_guard import get_personality_guard

        guard = get_personality_guard("eris")

        fixed = guard.fix_animation_prefix("Luna_curiosa")
        assert fixed == "Eris_curiosa"


class TestConversationState:
    def test_import(self):
        from src.soul.conversation_state import ConversationState

        assert ConversationState is not None

    def test_state_transitions(self):
        from src.soul.conversation_state import ConversationState, get_conversation_state_machine

        sm = get_conversation_state_machine()
        sm.reset()

        sm.transition("Oi!")
        assert sm.current_state == ConversationState.GREETING

        sm.transition("Pode criar um codigo?")
        assert sm.current_state == ConversationState.TASK

    def test_detect_deep_talk(self):
        from src.soul.conversation_state import ConversationState, get_conversation_state_machine

        sm = get_conversation_state_machine()
        sm.reset()

        sm.transition("Estou me sentindo triste...")
        assert sm.current_state == ConversationState.DEEP_TALK

    def test_detect_flirt(self):
        from src.soul.conversation_state import ConversationState, get_conversation_state_machine

        sm = get_conversation_state_machine()
        sm.reset()
        sm.turn_count = 5

        sm.transition("Voce e tao linda...")
        assert sm.current_state == ConversationState.FLIRT

    def test_state_context(self):
        from src.soul.conversation_state import ConversationState, get_conversation_state_machine

        sm = get_conversation_state_machine()
        sm.current_state = ConversationState.TASK

        context = sm.get_state_context()
        assert "tarefa" in context.lower()

    def test_history_tracking(self):
        from src.soul.conversation_state import get_conversation_state_machine

        sm = get_conversation_state_machine()
        sm.reset()

        sm.transition("Oi")
        sm.transition("Cria um script")

        history = sm.get_history()
        assert len(history) >= 1


class TestConscienciaIntegration:
    def test_imports_new_components(self):
        from src.soul.consciencia import Consciencia

        assert Consciencia is not None

    def test_pipeline_components_available(self):
        from src.soul.context_builder import get_context_builder
        from src.soul.conversation_state import get_conversation_state_machine
        from src.soul.entity_hotswap import get_entity_hotswap
        from src.soul.personality_guard import get_personality_guard
        from src.soul.response_pipeline import get_response_pipeline

        builder = get_context_builder("luna")
        pipeline = get_response_pipeline("luna")
        hotswap = get_entity_hotswap()
        guard = get_personality_guard("luna")
        state = get_conversation_state_machine()

        assert builder is not None
        assert pipeline is not None
        assert hotswap is not None
        assert guard is not None
        assert state is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
