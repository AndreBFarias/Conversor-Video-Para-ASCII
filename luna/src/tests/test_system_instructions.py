"""Testes para system_instructions.py."""

import pytest
from unittest.mock import patch, Mock


class TestGetEntityPersona:
    @patch("src.soul.system_instructions.EntityLoader")
    def test_get_entity_persona(self, mock_loader):
        from src.soul.system_instructions import get_entity_persona

        mock_loader.return_value.get_config.return_value = {
            "name": "Luna",
            "persona": {
                "reference": "Test Reference",
                "tone": {"primary": "ironica", "secondary": "sarcastica"},
                "problem_solving_style": "direta",
                "archetype": ["gotica"],
            },
        }

        result = get_entity_persona("luna")
        assert result["name"] == "Luna"
        assert result["reference"] == "Test Reference"
        assert result["tone_primary"] == "ironica"

    @patch("src.soul.system_instructions.EntityLoader")
    def test_get_entity_persona_fallback(self, mock_loader):
        from src.soul.system_instructions import get_entity_persona

        mock_loader.side_effect = Exception("Test error")

        result = get_entity_persona("luna")
        assert result["name"] == "Luna"
        assert "Jessica Rabbit" in result["reference"]


class TestSystemInstructionBuilder:
    @patch("src.soul.system_instructions.get_entity_persona")
    @patch("src.soul.system_instructions.get_user_name")
    def test_init(self, mock_user, mock_persona):
        from src.soul.system_instructions import SystemInstructionBuilder

        mock_persona.return_value = {
            "name": "Luna",
            "reference": "Test",
            "tone_primary": "ironica",
            "tone_secondary": "sarcastica",
            "problem_solving": "direta",
            "archetype": "gotica",
        }
        mock_user.return_value = "TestUser"

        builder = SystemInstructionBuilder("luna", "Test prompt", "gemini")
        assert builder.entity_id == "luna"
        assert builder.provider == "gemini"

    @patch("src.soul.system_instructions.get_entity_persona")
    @patch("src.soul.system_instructions.get_user_name")
    @patch("src.soul.system_instructions.config")
    def test_build_gemini(self, mock_config, mock_user, mock_persona):
        from src.soul.system_instructions import SystemInstructionBuilder

        mock_config.ANIMATION_TO_EMOTION = {"Luna_observando": "neutral"}
        mock_persona.return_value = {
            "name": "Luna",
            "reference": "Test",
            "tone_primary": "ironica",
            "tone_secondary": "sarcastica",
            "problem_solving": "direta",
            "archetype": "gotica",
        }
        mock_user.return_value = "TestUser"

        builder = SystemInstructionBuilder("luna", "Test prompt", "gemini")
        result = builder.build_gemini()

        assert "Luna" in result
        assert "JSON" in result
        assert "TestUser" in result

    @patch("src.soul.system_instructions.get_entity_persona")
    @patch("src.soul.system_instructions.get_user_name")
    @patch("src.soul.system_instructions.config")
    def test_build_local(self, mock_config, mock_user, mock_persona):
        from src.soul.system_instructions import SystemInstructionBuilder

        mock_config.ANIMATION_TO_EMOTION = {"Luna_observando": "neutral"}
        mock_persona.return_value = {
            "name": "Luna",
            "reference": "Test",
            "tone_primary": "ironica",
            "tone_secondary": "sarcastica",
            "problem_solving": "direta",
            "archetype": "gotica",
        }
        mock_user.return_value = "TestUser"

        builder = SystemInstructionBuilder("luna", "Test prompt", "local")
        result = builder.build_local()

        assert "Luna" in result
        assert "JSON" in result

    @patch("src.soul.system_instructions.get_entity_persona")
    @patch("src.soul.system_instructions.get_user_name")
    @patch("src.soul.system_instructions.config")
    @patch("src.soul.system_instructions.get_simple_prompt_format")
    def test_build_simple(self, mock_format, mock_config, mock_user, mock_persona):
        from src.soul.system_instructions import SystemInstructionBuilder

        mock_config.ANIMATION_TO_EMOTION = {"Luna_observando": "neutral"}
        mock_persona.return_value = {
            "name": "Luna",
            "reference": "Test",
            "tone_primary": "ironica",
            "tone_secondary": "sarcastica",
            "problem_solving": "direta",
            "archetype": "gotica",
        }
        mock_user.return_value = "TestUser"
        mock_format.return_value = "Simple format"

        builder = SystemInstructionBuilder("luna", "Test prompt", "local")
        result = builder.build_simple()

        assert "Luna" in result
        assert "TestUser" in result


class TestGetInstructionBuilder:
    @patch("src.soul.system_instructions.SystemInstructionBuilder")
    def test_factory(self, mock_builder):
        from src.soul.system_instructions import get_instruction_builder

        result = get_instruction_builder("luna", "Test prompt", "gemini")
        mock_builder.assert_called_once_with("luna", "Test prompt", "gemini")
