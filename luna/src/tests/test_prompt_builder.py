from unittest.mock import MagicMock, patch

import pytest


class TestPromptBuilder:
    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_init_loads_entity_data(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul prompt"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")

        assert builder.entity_id == "luna"
        assert builder.entity_name == "Luna"

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_reload_for_entity(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Eris", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Eris soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        builder.reload_for_entity("eris")

        assert builder.entity_id == "eris"

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    @patch("src.soul.prompt_builder.config")
    def test_build_full_contains_entity_name(self, mock_config, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_config.ANIMATION_TO_EMOTION = {"Luna_neutra": "neutral"}

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {
            "name": "Luna",
            "persona": {"tone": {"primary": "ironico"}, "reference": "Morticia"},
        }
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        result = builder.build(simple=False)

        assert "LUNA" in result
        assert "JSON" in result

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_build_simple_is_shorter(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        full = builder.build(simple=False)
        simple = builder.build(simple=True)

        assert len(simple) < len(full)

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_get_json_schema_returns_valid_json(self, mock_loader, mock_personalidade):
        import json

        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        schema_str = builder._get_json_schema()

        schema = json.loads(schema_str)
        assert "fala_tts" in schema
        assert "log_terminal" in schema

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_inject_memory_context(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        result = builder.inject_memory_context("Base prompt", "Memory context")

        assert "Base prompt" in result
        assert "Memory context" in result
        assert "CONTEXTO DE MEMORIA" in result

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_inject_memory_empty_context(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        result = builder.inject_memory_context("Base prompt", "")

        assert result == "Base prompt"

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_inject_anchor(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = PromptBuilder("luna")
        result = builder.inject_anchor("Base prompt", "Anchor text")

        assert result.startswith("Anchor text")
        assert "Base prompt" in result


class TestGetPromptBuilder:
    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_factory_returns_builder(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import PromptBuilder, get_prompt_builder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        builder = get_prompt_builder("luna")

        assert isinstance(builder, PromptBuilder)

    @patch("src.soul.prompt_builder.get_personalidade")
    @patch("src.soul.prompt_builder.EntityLoader")
    def test_factory_different_entities(self, mock_loader, mock_personalidade):
        from src.soul.prompt_builder import get_prompt_builder

        mock_loader_instance = MagicMock()
        mock_loader_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_loader_instance

        mock_personalidade_instance = MagicMock()
        mock_personalidade_instance.get_soul_prompt.return_value = "Soul"
        mock_personalidade.return_value = mock_personalidade_instance

        luna = get_prompt_builder("luna")
        eris = get_prompt_builder("eris")

        assert luna is not eris


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
