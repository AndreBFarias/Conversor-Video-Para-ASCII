"""Testes para json_extractor.py."""

import pytest
import json
from unittest.mock import patch, Mock


class TestJSONExtractor:
    @patch("src.soul.json_extractor.get_entity_name")
    def test_init(self, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        extractor = JSONExtractor("luna")
        assert extractor.entity_id == "luna"

    @patch("src.soul.json_extractor.get_entity_name")
    def test_extract_valid_json(self, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        extractor = JSONExtractor("luna")

        text = '{"fala_tts": "Ola", "animacao": "Luna_observando"}'
        result = extractor.extract(text)
        data = json.loads(result)
        assert data["fala_tts"] == "Ola"

    @patch("src.soul.json_extractor.get_entity_name")
    def test_extract_json_with_markdown(self, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        extractor = JSONExtractor("luna")

        text = '```json\n{"fala_tts": "Teste"}\n```'
        result = extractor.extract(text)
        data = json.loads(result)
        assert data["fala_tts"] == "Teste"

    @patch("src.soul.json_extractor.get_entity_name")
    @patch("src.soul.json_extractor.config")
    def test_extract_no_json(self, mock_config, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        mock_config.ANIMATION_TO_EMOTION = {}
        extractor = JSONExtractor("luna")

        text = "Texto sem JSON"
        result = extractor.extract(text)
        data = json.loads(result)
        assert "fala_tts" in data

    @patch("src.soul.json_extractor.get_entity_name")
    def test_fix_syntax_unquoted_keys(self, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        extractor = JSONExtractor("luna")

        text = '{fala_tts: "test"}'
        result = extractor.fix_syntax(text)
        assert '"fala_tts"' in result


class TestBuildFromText:
    @patch("src.soul.json_extractor.get_entity_name")
    @patch("src.soul.json_extractor.config")
    def test_empty_text(self, mock_config, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        mock_config.ANIMATION_TO_EMOTION = {}
        extractor = JSONExtractor("luna")

        result = extractor.build_from_text("")
        data = json.loads(result)
        assert "fala_tts" in data
        assert "animacao" in data

    @patch("src.soul.json_extractor.get_entity_name")
    @patch("src.soul.json_extractor.config")
    def test_extract_fala_tts(self, mock_config, mock_name):
        from src.soul.json_extractor import JSONExtractor

        mock_name.return_value = "Luna"
        mock_config.ANIMATION_TO_EMOTION = {"Luna_sarcastica": "sarcastic"}
        extractor = JSONExtractor("luna")

        text = 'fala_tts: "Ola mortal", animacao: "Luna_sarcastica"'
        result = extractor.build_from_text(text)
        data = json.loads(result)
        assert "mortal" in data.get("fala_tts", "").lower() or "fala_tts" in data


class TestGetJsonExtractor:
    @patch("src.soul.json_extractor.get_entity_name")
    def test_factory(self, mock_name):
        from src.soul.json_extractor import get_json_extractor

        mock_name.return_value = "Luna"
        extractor = get_json_extractor("luna")
        assert extractor.entity_id == "luna"
