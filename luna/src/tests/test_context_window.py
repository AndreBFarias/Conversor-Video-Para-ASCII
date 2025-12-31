from __future__ import annotations

import pytest


class TestModelSize:
    def test_model_sizes_exist(self):
        from src.soul.context_window.config import ModelSize

        assert ModelSize.TINY.value == "tiny"
        assert ModelSize.SMALL.value == "small"
        assert ModelSize.MEDIUM.value == "medium"
        assert ModelSize.LARGE.value == "large"
        assert ModelSize.XLARGE.value == "xlarge"


class TestModelProfile:
    def test_profile_defaults(self):
        from src.soul.context_window.config import ModelProfile, ModelSize

        profile = ModelProfile(
            name="test",
            context_window=8192,
            size=ModelSize.SMALL,
        )

        assert profile.name == "test"
        assert profile.context_window == 8192
        assert profile.tokens_per_char == 0.25
        assert profile.supports_streaming is True

    def test_effective_context(self):
        from src.soul.context_window.config import ModelProfile, ModelSize

        profile = ModelProfile(
            name="test",
            context_window=10000,
            size=ModelSize.MEDIUM,
        )

        assert profile.effective_context == 9000

    def test_estimate_tokens(self):
        from src.soul.context_window.config import ModelProfile, ModelSize

        profile = ModelProfile(
            name="test",
            context_window=8192,
            size=ModelSize.SMALL,
            tokens_per_char=0.25,
        )

        text = "a" * 100
        tokens = profile.estimate_tokens(text)

        assert tokens == 25


class TestGetModelProfile:
    def test_get_known_model(self):
        from src.soul.context_window.config import get_model_profile

        profile = get_model_profile("llama3.2")

        assert profile.name == "llama3.2"
        assert profile.context_window == 8192

    def test_get_model_with_tag(self):
        from src.soul.context_window.config import get_model_profile

        profile = get_model_profile("llama3.2:1b")

        assert profile.name == "llama3.2:1b"

    def test_get_gemini_model(self):
        from src.soul.context_window.config import get_model_profile

        profile = get_model_profile("gemini-2.0-flash")

        assert profile.context_window == 1048576

    def test_get_unknown_returns_default(self):
        from src.soul.context_window.config import ModelSize, get_model_profile

        profile = get_model_profile("unknown-model-xyz")

        assert profile.name == "default"
        assert profile.size == ModelSize.SMALL


class TestBudgetAllocation:
    def test_default_allocation(self):
        from src.soul.context_window.config import BudgetAllocation

        budget = BudgetAllocation()

        assert budget.system_prompt_pct == 0.25
        assert budget.memory_pct == 0.20
        assert budget.conversation_pct == 0.40
        assert budget.user_input_pct == 0.10
        assert budget.reserve_pct == 0.05


class TestHistoryLimits:
    def test_default_limits(self):
        from src.soul.context_window.config import HistoryLimits

        limits = HistoryLimits()

        assert limits.max_turns == 10
        assert limits.max_chars_per_turn == 300
        assert limits.summary_threshold_pct == 0.80
        assert limits.summary_compress_pct == 0.30


class TestContextWindowConfig:
    def test_config_budgets(self):
        from src.soul.context_window.config import (
            ContextWindowConfig,
            ModelProfile,
            ModelSize,
        )

        profile = ModelProfile(
            name="test",
            context_window=10000,
            size=ModelSize.MEDIUM,
        )
        config = ContextWindowConfig(model_profile=profile)

        assert config.total_budget == 9000
        assert config.system_prompt_budget == 2250
        assert config.memory_budget == 1800
        assert config.conversation_budget == 3600
        assert config.user_input_budget == 900

    def test_adjust_for_tiny(self):
        from src.soul.context_window.config import (
            ContextWindowConfig,
            ModelProfile,
            ModelSize,
        )

        profile = ModelProfile(
            name="tiny",
            context_window=4096,
            size=ModelSize.TINY,
        )
        config = ContextWindowConfig(model_profile=profile)
        config.adjust_for_size()

        assert config.history_limits.max_turns == 3
        assert config.history_limits.max_chars_per_turn == 100
        assert config.memory_max_chars == 300

    def test_adjust_for_xlarge(self):
        from src.soul.context_window.config import (
            ContextWindowConfig,
            ModelProfile,
            ModelSize,
        )

        profile = ModelProfile(
            name="xlarge",
            context_window=1000000,
            size=ModelSize.XLARGE,
        )
        config = ContextWindowConfig(model_profile=profile)
        config.adjust_for_size()

        assert config.history_limits.max_turns == 50
        assert config.history_limits.max_chars_per_turn == 1000
        assert config.memory_max_chars == 2000

    def test_get_budget_summary(self):
        from src.soul.context_window.config import get_context_config

        config = get_context_config("llama3.2")
        summary = config.get_budget_summary()

        assert "model" in summary
        assert "size" in summary
        assert "budgets" in summary
        assert "limits" in summary


class TestGetContextConfig:
    def test_caches_config(self):
        from src.soul.context_window.config import get_context_config

        config1 = get_context_config("llama3.2")
        config2 = get_context_config("llama3.2")

        assert config1 is config2

    def test_different_models_different_configs(self):
        from src.soul.context_window.config import get_context_config

        config1 = get_context_config("llama3.2")
        config2 = get_context_config("gemini-2.0-flash")

        assert config1 is not config2


class TestSummaryResult:
    def test_summary_result_fields(self):
        from src.soul.context_window.progressive_summary import SummaryResult

        result = SummaryResult(
            original_tokens=1000,
            compressed_tokens=300,
            summary_text="Summary here",
            messages_summarized=10,
            compression_ratio=0.3,
        )

        assert result.tokens_saved == 700
        assert result.summary_text == "Summary here"


class TestProgressiveSummary:
    def test_should_compress(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        threshold = config.summary_threshold

        assert summary.should_compress(threshold - 100) is False
        assert summary.should_compress(threshold) is True
        assert summary.should_compress(threshold + 100) is True

    def test_get_compression_count(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        history = [{"content": "msg"} for _ in range(10)]
        count = summary.get_compression_count(history)

        assert count == 3

    def test_compress_returns_remaining(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

        remaining, result = summary.compress(history, force=True)

        assert len(remaining) < len(history)
        assert result is not None
        assert result.messages_summarized > 0

    def test_no_compress_when_not_needed(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("gemini-2.0-flash")
        summary = ProgressiveSummary(config)

        history = [{"role": "user", "content": "Short"}]

        remaining, result = summary.compress(history, force=False)

        assert remaining == history
        assert result is None

    def test_extractive_summary(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config, llm_summarizer=None)

        history = [
            {"role": "user", "content": "Hello, how are you today?"},
            {"role": "assistant", "content": "I am doing well, thank you for asking."},
        ]

        remaining, result = summary.compress(history, force=True)

        assert result is not None
        assert "[user]" in result.summary_text.lower()

    def test_get_summary_context_empty(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        context = summary.get_summary_context()
        assert context == ""

    def test_get_stats_empty(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        stats = summary.get_stats()

        assert stats["total_compressions"] == 0
        assert stats["total_tokens_saved"] == 0

    def test_clear(self):
        from src.soul.context_window.config import get_context_config
        from src.soul.context_window.progressive_summary import ProgressiveSummary

        config = get_context_config("llama3.2")
        summary = ProgressiveSummary(config)

        history = [{"role": "user", "content": f"Msg {i}"} for i in range(10)]
        summary.compress(history, force=True)

        summary.clear()

        assert summary.get_summary_context() == ""
        assert summary.get_stats()["total_compressions"] == 0


class TestContextUsage:
    def test_total_tokens(self):
        from src.soul.context_window.manager import ContextUsage

        usage = ContextUsage(
            system_prompt_tokens=100,
            memory_tokens=200,
            conversation_tokens=300,
            user_input_tokens=50,
            summary_tokens=25,
            emotional_tokens=10,
            proactive_tokens=15,
        )

        assert usage.total_tokens == 700


class TestContextWindowManager:
    def test_init(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test_entity",
            model_name="llama3.2",
        )

        assert manager.entity_id == "test_entity"
        assert manager.model_name == "llama3.2"

    def test_add_and_get_history(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        manager.add_turn("user", "Hello")
        manager.add_turn("assistant", "Hi there")

        history = manager.get_history()

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_get_history_with_limit(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        for i in range(10):
            manager.add_turn("user", f"Message {i}")

        history = manager.get_history(limit=3)

        assert len(history) == 3
        assert history[0]["content"] == "Message 7"

    def test_clear_history(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        manager.add_turn("user", "Hello")
        manager.clear_history()

        assert len(manager.get_history()) == 0

    def test_build_context(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        manager.add_turn("user", "Previous message")

        result = manager.build_context(
            system_prompt="You are a helpful assistant",
            memory_context="User likes coffee",
            user_input="Hello",
        )

        assert result.system_prompt == "You are a helpful assistant"
        assert result.memory_context == "User likes coffee"
        assert result.user_input == "Hello"
        assert result.usage.total_tokens > 0

    def test_build_prompt(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        prompt = manager.build_prompt(
            system_prompt="System",
            memory_context="Memory",
            user_input="Input",
        )

        assert "System" in prompt
        assert "Memory" in prompt
        assert "Input" in prompt

    def test_get_usage_stats(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        manager.build_context(
            system_prompt="System",
            memory_context="Memory",
            user_input="Input",
        )

        stats = manager.get_usage_stats()

        assert "model" in stats
        assert "total_budget" in stats
        assert "used_tokens" in stats
        assert "usage_percentage" in stats
        assert "breakdown" in stats

    def test_get_limits(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        limits = manager.get_limits()

        assert "max_turns" in limits
        assert "max_chars_per_turn" in limits
        assert "memory_max_chars" in limits

    def test_truncation(self):
        from src.soul.context_window.manager import ContextWindowManager

        manager = ContextWindowManager(
            entity_id="test",
            model_name="llama3.2",
        )

        long_input = "x" * 10000

        result = manager.build_context(
            system_prompt="Short",
            memory_context="Short",
            user_input=long_input,
        )

        assert len(result.user_input) < len(long_input)
        assert result.user_input.endswith("...")


class TestGetContextWindowManager:
    def test_caches_manager(self):
        from src.soul.context_window.manager import get_context_window_manager

        manager1 = get_context_window_manager("entity1", "llama3.2")
        manager2 = get_context_window_manager("entity1", "llama3.2")

        assert manager1 is manager2

    def test_different_entities_different_managers(self):
        from src.soul.context_window.manager import get_context_window_manager

        manager1 = get_context_window_manager("entity1", "llama3.2")
        manager2 = get_context_window_manager("entity2", "llama3.2")

        assert manager1 is not manager2

    def test_different_models_different_managers(self):
        from src.soul.context_window.manager import get_context_window_manager

        manager1 = get_context_window_manager("entity1", "llama3.2")
        manager2 = get_context_window_manager("entity1", "gemini-2.0-flash")

        assert manager1 is not manager2
