import pytest

from src.core.entity_loader import EntityLoader, get_active_entity, set_active_entity


class TestEntitySwitch:
    def test_get_active_entity_returns_string(self):
        entity = get_active_entity()
        assert isinstance(entity, str)
        assert len(entity) > 0

    def test_switch_preserves_user_data(self):
        original = get_active_entity()
        set_active_entity("eris")
        set_active_entity(original)
        assert get_active_entity() == original

    def test_invalid_entity_uses_fallback(self):
        loader = EntityLoader("nonexistent_entity_xyz")
        soul = loader.get_soul_prompt()
        assert soul is not None and len(soul) > 0

    def test_entity_loader_returns_soul_prompt(self):
        loader = EntityLoader("luna")
        soul = loader.get_soul_prompt()
        assert isinstance(soul, str)
        assert len(soul) > 0

    def test_entity_loader_returns_config(self):
        loader = EntityLoader("luna")
        config = loader.get_config()
        assert isinstance(config, dict)
        assert "name" in config or "persona" in config

    def test_animation_path_exists_or_fallback(self):
        loader = EntityLoader("luna")
        path = loader.get_animation_path("observando")
        assert path is not None
        if path.exists():
            assert path.suffix in [".txt", ".gz"]

    def test_switch_to_eris(self):
        original = get_active_entity()
        try:
            set_active_entity("eris")
            assert get_active_entity() == "eris"
            loader = EntityLoader("eris")
            assert loader.entity_id == "eris"
        finally:
            set_active_entity(original)

    def test_switch_to_juno(self):
        original = get_active_entity()
        try:
            set_active_entity("juno")
            assert get_active_entity() == "juno"
            loader = EntityLoader("juno")
            assert loader.entity_id == "juno"
        finally:
            set_active_entity(original)

    def test_color_theme_returns_dict(self):
        loader = EntityLoader("luna")
        theme = loader.get_color_theme()
        assert isinstance(theme, dict)

    def test_all_available_entities(self):
        entities = ["luna", "eris", "juno", "lars", "mars", "somn"]
        original = get_active_entity()
        try:
            for entity_id in entities:
                loader = EntityLoader(entity_id)
                assert loader.entity_id in [entity_id, "luna"]
        finally:
            set_active_entity(original)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
