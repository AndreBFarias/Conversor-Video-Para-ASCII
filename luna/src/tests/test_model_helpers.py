"""Testes para model_helpers.py."""

import pytest
from unittest.mock import patch, Mock


class TestGetModelSizeGb:
    def test_with_size_suffix(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("llama3.2:1b") == 1.0
        assert get_model_size_gb("llama3.2:3b") == 3.0
        assert get_model_size_gb("llama3:8b") == 8.0

    def test_with_decimal_size(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("qwen2:0.5b") == 0.5
        assert get_model_size_gb("qwen2:1.5b") == 1.5

    def test_with_keywords(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("tinyllama") == 1.0
        assert get_model_size_gb("phi3:mini") == 2.0
        assert get_model_size_gb("llava-phi3") == 3.8

    def test_default_size(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("unknown-model") == 7.0
        assert get_model_size_gb("") == 7.0
        assert get_model_size_gb(None) == 7.0


class TestIsSmallModel:
    def test_small_models(self):
        from src.soul.model_helpers import is_small_model

        assert is_small_model("llama3.2:3b") is True
        assert is_small_model("phi3:mini") is True
        assert is_small_model("tinyllama") is True

    def test_large_models(self):
        from src.soul.model_helpers import is_small_model

        assert is_small_model("llama3:8b") is False
        assert is_small_model("dolphin-mistral:7b") is False


class TestNeedsCompactPrompt:
    def test_compact_models(self):
        from src.soul.model_helpers import needs_compact_prompt

        assert needs_compact_prompt("llama3.2:1b") is True
        assert needs_compact_prompt("llama3.2:3b") is True
        assert needs_compact_prompt("tinyllama") is True

    def test_non_compact_models(self):
        from src.soul.model_helpers import needs_compact_prompt

        assert needs_compact_prompt("llama3:8b") is False
        assert needs_compact_prompt("dolphin-mistral:7b") is False


class TestSanitizeForLog:
    def test_empty_string(self):
        from src.soul.model_helpers import sanitize_for_log

        assert sanitize_for_log("") == ""
        assert sanitize_for_log(None) == ""

    def test_sanitize_email(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("email teste@exemplo.com ok")
        assert "[EMAIL]" in result
        assert "teste@exemplo.com" not in result

    def test_sanitize_cpf(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("cpf 123.456.789-00")
        assert "[CPF]" in result

    def test_truncate(self):
        from src.soul.model_helpers import sanitize_for_log

        long_text = "a" * 100
        result = sanitize_for_log(long_text, max_len=50)
        assert len(result) == 53
        assert result.endswith("...")


class TestRemoveEmojis:
    def test_with_emojis(self):
        from src.soul.model_helpers import remove_emojis

        result = remove_emojis("Hello world!")
        assert result == "Hello world!"

    def test_without_emojis(self):
        from src.soul.model_helpers import remove_emojis

        result = remove_emojis("Texto normal")
        assert result == "Texto normal"


class TestGetUserProfile:
    @patch("src.soul.model_helpers.PROFILE_PATH")
    @patch("src.soul.model_helpers.get_user_context")
    def test_no_file(self, mock_context, mock_path):
        from src.soul.model_helpers import get_user_profile

        mock_path.exists.return_value = False
        mock_context.return_value = {"user_name": "Viajante"}

        result = get_user_profile()
        assert result == {"user_name": "Viajante"}


class TestGetUserName:
    @patch("src.soul.model_helpers.get_user_profile")
    def test_get_user_name(self, mock_profile):
        from src.soul.model_helpers import get_user_name

        mock_profile.return_value = {"user_name": "TestUser"}
        result = get_user_name()
        assert result == "TestUser"
