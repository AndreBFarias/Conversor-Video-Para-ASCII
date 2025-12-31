"""Testes para llm_caller.py."""

import pytest
from unittest.mock import patch, Mock, MagicMock


class TestLLMCaller:
    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_init(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        caller = LLMCaller(
            provider="local",
            model_name="test-model",
            gemini_client=None,
            ollama_client=Mock(),
            app=Mock(),
        )

        assert caller.provider == "local"
        assert caller.model_name == "test-model"

    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_set_system_instruction(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        caller = LLMCaller("local", "test", None, Mock(), Mock())
        caller.set_system_instruction("Test instruction")
        assert caller._system_instruction == "Test instruction"

    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_get_cache_key(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        caller = LLMCaller("local", "test", None, Mock(), Mock())

        key1 = caller._get_cache_key("prompt1")
        key2 = caller._get_cache_key("prompt2")
        key3 = caller._get_cache_key("prompt1")

        assert key1 != key2
        assert key1 == key3

    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_has_provider_with_ollama(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        caller = LLMCaller("local", "test", None, Mock(), Mock())
        assert caller.has_provider() is True

    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_has_provider_without_providers(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        caller = LLMCaller("local", "test", None, None, Mock())
        assert caller.has_provider() is False


class TestCreateLLMCaller:
    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_factory(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import create_llm_caller

        caller = create_llm_caller(
            provider="gemini",
            model_name="gemini-1.5-flash",
            gemini_client=Mock(),
            ollama_client=None,
            app=Mock(),
        )

        assert caller.provider == "gemini"
        assert caller.model_name == "gemini-1.5-flash"


class TestCacheHit:
    @patch("src.soul.llm_caller.get_metrics")
    @patch("src.soul.llm_caller.get_api_tracker")
    @patch("src.soul.llm_caller.get_parser")
    def test_cache_returns_cached_response(self, mock_parser, mock_tracker, mock_metrics):
        from src.soul.llm_caller import LLMCaller

        mock_metrics.return_value = Mock()
        caller = LLMCaller("local", "test", None, Mock(), Mock())

        cache_key = caller._get_cache_key("test prompt")
        caller.response_cache[cache_key] = '{"fala_tts": "cached"}'

        result = caller.call("test prompt")
        assert "cached" in result
