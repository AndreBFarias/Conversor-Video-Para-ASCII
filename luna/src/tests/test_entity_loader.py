import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEntityLoader:
    def test_load_luna_default(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        assert loader.entity_id == "luna"
        assert loader.entity_data is not None
        assert loader.entity_data.get("id") == "luna"

    def test_load_entity_returns_dict(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        data = loader.entity_data
        assert isinstance(data, dict)
        assert "id" in data
        assert "config" in data

    def test_get_soul_prompt_returns_string(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        prompt = loader.get_soul_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_config_returns_dict(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        config = loader.get_config()
        assert isinstance(config, dict)

    def test_get_voice_config_returns_dict(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        voice = loader.get_voice_config()
        assert isinstance(voice, dict)

    def test_get_color_theme_returns_dict(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        theme = loader.get_color_theme()
        assert isinstance(theme, dict)
        assert "primary_color" in theme or len(theme) > 0

    def test_get_full_color_theme_has_defaults(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        theme = loader.get_full_color_theme()
        assert isinstance(theme, dict)
        assert "background_alt" in theme or "primary_color" in theme

    def test_get_animation_path_returns_path(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        path = loader.get_animation_path("observando")
        assert isinstance(path, Path)

    def test_get_animation_path_fallback(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        path = loader.get_animation_path("emocao_que_nao_existe_xyz")
        assert isinstance(path, Path)
        assert "observando" in str(path).lower() or path.exists()

    def test_list_available_entities_returns_list(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        entities = loader.list_available_entities()
        assert isinstance(entities, list)
        assert len(entities) > 0
        assert any(e.get("id") == "luna" for e in entities)

    def test_is_entity_available_luna(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        assert loader.is_entity_available("luna") is True

    def test_is_entity_available_fake_entity(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        assert loader.is_entity_available("entidade_fake_xyz") is False

    def test_get_banner_ascii_returns_list(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        banner = loader.get_banner_ascii()
        assert isinstance(banner, list)
        assert len(banner) > 0

    def test_get_gradient_returns_list(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        gradient = loader.get_gradient()
        assert isinstance(gradient, list)
        assert len(gradient) > 0
        assert all(g.startswith("#") for g in gradient)


class TestEntityLoaderFallback:
    def test_nonexistent_entity_falls_back(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("entidade_fake_xyz")
        assert loader.entity_data is not None
        assert loader.entity_data.get("id") in ["luna", "entidade_fake_xyz"]

    def test_minimal_entity_data_structure(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        minimal = loader._get_minimal_entity_data("luna")
        assert "id" in minimal
        assert "config" in minimal
        assert "registry_info" in minimal


class TestEntityLoaderHelpers:
    def test_hex_to_rgb(self):
        from src.core.entity_loader import hex_to_rgb

        rgb = hex_to_rgb("#ff0000")
        assert rgb == (255, 0, 0)

    def test_rgb_to_hex(self):
        from src.core.entity_loader import rgb_to_hex

        hex_color = rgb_to_hex(255, 0, 0)
        assert hex_color == "#ff0000"

    def test_lighten_color(self):
        from src.core.entity_loader import lighten_color

        lighter = lighten_color("#000000", 50)
        assert lighter != "#000000"
        assert lighter.startswith("#")

    def test_darken_color(self):
        from src.core.entity_loader import darken_color

        darker = darken_color("#ffffff", 50)
        assert darker != "#ffffff"
        assert darker.startswith("#")


class TestActiveEntityFunctions:
    def test_get_active_entity_returns_string(self):
        from src.core.entity_loader import get_active_entity

        entity = get_active_entity()
        assert isinstance(entity, str)
        assert len(entity) > 0

    def test_get_entity_phrases_returns_dict(self):
        from src.core.entity_loader import get_entity_phrases

        phrases = get_entity_phrases("luna")
        assert isinstance(phrases, dict)

    def test_get_entity_name_returns_string(self):
        from src.core.entity_loader import get_entity_name

        name = get_entity_name("luna")
        assert isinstance(name, str)
        assert name == "Luna"

    def test_get_active_loader_returns_loader(self):
        from src.core.entity_loader import EntityLoader, get_active_loader

        loader = get_active_loader()
        assert isinstance(loader, EntityLoader)

    def test_reload_active_loader_returns_new_loader(self):
        from src.core.entity_loader import EntityLoader, reload_active_loader

        loader = reload_active_loader()
        assert isinstance(loader, EntityLoader)


class TestSetActiveEntity:
    @patch("src.core.entity_loader.helpers.update_json_safe")
    @patch("src.core.entity_loader.helpers.read_json_safe")
    @patch("src.core.entity_loader.helpers.PROFILE_PATH")
    def test_set_active_entity_invalid(self, mock_path, mock_read, mock_update):
        from src.core.entity_loader import set_active_entity

        mock_path.exists.return_value = True
        mock_read.return_value = {}

        result = set_active_entity("entidade_fake_xyz", reload_config=False)
        assert result is False
