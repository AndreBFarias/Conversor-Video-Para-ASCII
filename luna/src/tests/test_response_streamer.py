"""Testes para response_streamer.py."""

import pytest
from unittest.mock import patch, Mock


class TestResponseStreamer:
    @patch("src.soul.response_streamer.get_parser")
    def test_init(self, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        streamer = ResponseStreamer(
            entity_id="luna",
            provider="local",
            model_name="test-model",
            gemini_client=None,
            ollama_client=Mock(),
            system_instruction="Test instruction",
        )

        assert streamer.entity_id == "luna"
        assert streamer.provider == "local"
        assert streamer.model_name == "test-model"

    @patch("src.soul.response_streamer.get_parser")
    @patch("src.soul.response_streamer.get_entity_name")
    def test_fallback_response(self, mock_name, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        mock_name.return_value = "Luna"
        streamer = ResponseStreamer("luna", "local", "test", None, Mock(), "")

        result = streamer._fallback_response("Test error")
        assert "fala_tts" in result
        assert "animacao" in result
        assert "Luna" in result["animacao"]

    @patch("src.soul.response_streamer.get_parser")
    def test_validate_schema_valid(self, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        streamer = ResponseStreamer("luna", "local", "test", None, Mock(), "")

        valid_data = {
            "fala_tts": "Ola",
            "log_terminal": "[Luna] Ola",
            "animacao": "Luna_observando",
            "comando_visao": False,
        }
        assert streamer._validate_schema(valid_data) is True

    @patch("src.soul.response_streamer.get_parser")
    def test_validate_schema_invalid(self, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        streamer = ResponseStreamer("luna", "local", "test", None, Mock(), "")

        invalid_data = {"fala_tts": "Ola"}
        assert streamer._validate_schema(invalid_data) is False

    @patch("src.soul.response_streamer.get_parser")
    def test_has_provider_with_ollama(self, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        streamer = ResponseStreamer("luna", "local", "test", None, Mock(), "")
        assert streamer._has_provider() is True

    @patch("src.soul.response_streamer.get_parser")
    def test_has_provider_without_providers(self, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        streamer = ResponseStreamer("luna", "local", "test", None, None, "")
        assert streamer._has_provider() is False


class TestCreateResponseStreamer:
    @patch("src.soul.response_streamer.get_parser")
    def test_factory(self, mock_parser):
        from src.soul.response_streamer import create_response_streamer

        streamer = create_response_streamer(
            entity_id="luna",
            provider="gemini",
            model_name="gemini-1.5-flash",
            gemini_client=Mock(),
            ollama_client=None,
            system_instruction="Test",
        )

        assert streamer.entity_id == "luna"
        assert streamer.provider == "gemini"


class TestStreamNoProvider:
    @patch("src.soul.response_streamer.get_parser")
    @patch("src.soul.response_streamer.get_entity_name")
    def test_stream_offline(self, mock_name, mock_parser):
        from src.soul.response_streamer import ResponseStreamer

        mock_name.return_value = "Luna"
        streamer = ResponseStreamer("luna", "local", "test", None, None, "")

        results = list(streamer.stream("Ola"))
        assert len(results) == 1
        assert "offline" in results[0][0].lower()
        assert results[0][1] is True
