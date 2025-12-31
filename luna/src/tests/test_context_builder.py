from unittest.mock import Mock, patch

import pytest


class TestContextBudget:
    def test_context_budget_defaults(self):
        from src.soul.context_builder import ContextBudget

        budget = ContextBudget()
        assert budget.total_tokens == 4000
        assert budget.system_prompt == 1000
        assert budget.memory == 1000
        assert budget.conversation == 1500
        assert budget.user_input == 500

    def test_context_budget_custom(self):
        from src.soul.context_builder import ContextBudget

        budget = ContextBudget(total_tokens=8000, memory=2000)
        assert budget.total_tokens == 8000
        assert budget.memory == 2000
        assert budget.system_prompt == 1000


class TestBuiltContext:
    def test_built_context_creation(self):
        from src.soul.context_builder import BuiltContext

        context = BuiltContext(
            system_prompt="prompt",
            memory_context="memory",
            conversation_history="history",
            user_input="input",
            proactive_recall=None,
            emotional_context="[Estado emocional: neutro]",
            total_estimated_tokens=100,
        )
        assert context.system_prompt == "prompt"
        assert context.memory_context == "memory"
        assert context.proactive_recall is None
        assert context.emotional_context == "[Estado emocional: neutro]"
        assert context.total_estimated_tokens == 100


class TestContextBuilder:
    @pytest.fixture
    def mock_context_builder(self):
        with (
            patch("src.soul.context_builder.get_entity_smart_memory") as mock_memory,
            patch("src.soul.context_builder.get_cross_entity_memory") as mock_cross,
            patch("src.soul.context_builder.get_proactive_recall") as mock_proactive,
        ):
            mock_memory.return_value = Mock()
            mock_cross.return_value = Mock()
            mock_proactive.return_value = Mock()

            from src.soul.context_builder import ContextBuilder

            builder = ContextBuilder("luna")
            return builder

    def test_init_creates_instance(self, mock_context_builder):
        assert mock_context_builder is not None
        assert mock_context_builder.entity_id == "luna"

    def test_estimate_tokens(self, mock_context_builder):
        result = mock_context_builder._estimate_tokens("test text")
        assert result == len("test text") // 4

    def test_estimate_tokens_empty(self, mock_context_builder):
        result = mock_context_builder._estimate_tokens("")
        assert result == 0

    def test_truncate_to_budget_short_text(self, mock_context_builder):
        short_text = "Short text"
        result = mock_context_builder._truncate_to_budget(short_text, 100)
        assert result == short_text

    def test_truncate_to_budget_long_text(self, mock_context_builder):
        long_text = "a" * 1000
        result = mock_context_builder._truncate_to_budget(long_text, 50)
        assert result.endswith("...")
        assert len(result) < len(long_text)

    def test_get_system_prompt(self, mock_context_builder):
        with patch("src.core.entity_loader.EntityLoader") as mock_loader:
            mock_loader.return_value.get_soul_prompt.return_value = "Soul prompt"
            result = mock_context_builder._get_system_prompt()
            assert result is not None

    def test_get_memory_context(self, mock_context_builder):
        mock_context_builder.memory.retrieve.return_value = "Memory content"
        mock_context_builder.cross_memory.get_shared_memories.return_value = []

        result = mock_context_builder._get_memory_context("query")
        assert "Memory content" in result

    def test_get_memory_context_with_shared(self, mock_context_builder):
        mock_context_builder.memory.retrieve.return_value = "Memory"
        mock_context_builder.cross_memory.get_shared_memories.return_value = [
            {"content": "Shared info 1"},
            {"content": "Shared info 2"},
        ]

        result = mock_context_builder._get_memory_context("query")
        assert "Memory" in result
        assert "INFO COMPARTILHADA" in result

    def test_get_conversation_history_empty(self, mock_context_builder):
        result = mock_context_builder._get_conversation_history([])
        assert result == ""

    def test_get_conversation_history_with_messages(self, mock_context_builder):
        history = [
            {"role": "user", "content": "Ola"},
            {"role": "assistant", "content": "Oi"},
        ]
        result = mock_context_builder._get_conversation_history(history)
        assert "user: Ola" in result
        assert "assistant: Oi" in result

    def test_get_conversation_history_truncates(self, mock_context_builder):
        history = [{"role": "user", "content": f"Msg {i}"} for i in range(20)]
        result = mock_context_builder._get_conversation_history(history)
        lines = result.strip().split("\n")
        assert len(lines) <= 10

    def test_get_proactive_recall_none(self, mock_context_builder):
        mock_context_builder.proactive.find_relevant_memory.return_value = None
        result = mock_context_builder._get_proactive_recall("input", "context")
        assert result is None


class TestContextBuilderSingleton:
    @patch("src.soul.context_builder.get_entity_smart_memory")
    @patch("src.soul.context_builder.get_cross_entity_memory")
    @patch("src.soul.context_builder.get_proactive_recall")
    def test_get_context_builder_returns_instance(self, mock_proactive, mock_cross, mock_memory):
        mock_memory.return_value = Mock()
        mock_cross.return_value = Mock()
        mock_proactive.return_value = Mock()

        from src.soul.context_builder import get_context_builder

        builder1 = get_context_builder("luna")
        builder2 = get_context_builder("luna")

        assert builder1 is not None
        assert builder2 is not None
