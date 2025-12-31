import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import unittest

from src.core.entity_loader import (
    ENTITIES_DIR,
    REGISTRY_PATH,
    EntityLoader,
    get_active_entity,
    set_active_entity,
)


class TestEntityLoader(unittest.TestCase):
    def test_load_luna(self):
        loader = EntityLoader("luna")
        self.assertEqual(loader.entity_id, "luna")
        self.assertIn("config", loader.entity_data)
        self.assertIn("soul_path", loader.entity_data)

    def test_get_soul_prompt(self):
        loader = EntityLoader("luna")
        soul = loader.get_soul_prompt()
        self.assertIsInstance(soul, str)
        self.assertGreater(len(soul), 100)

    def test_get_config(self):
        loader = EntityLoader("luna")
        config = loader.get_config()
        self.assertIsInstance(config, dict)
        self.assertIn("name", config)
        self.assertEqual(config.get("name"), "Luna")

    def test_get_color_theme(self):
        loader = EntityLoader("luna")
        theme = loader.get_color_theme()
        self.assertIsInstance(theme, dict)
        self.assertIn("primary_color", theme)
        self.assertIn("background", theme)

    def test_get_animation_path(self):
        loader = EntityLoader("luna")
        path = loader.get_animation_path("observando")
        self.assertIsInstance(path, Path)
        self.assertTrue(path.exists() or path.with_suffix(".txt.gz").exists())

    def test_list_available_entities(self):
        loader = EntityLoader("luna")
        available = loader.list_available_entities()
        self.assertIsInstance(available, list)
        self.assertGreater(len(available), 0)
        luna_found = any(e["id"] == "luna" for e in available)
        self.assertTrue(luna_found)

    def test_is_entity_available_luna(self):
        loader = EntityLoader("luna")
        self.assertTrue(loader.is_entity_available("luna"))

    def test_is_entity_available_invalid(self):
        loader = EntityLoader("luna")
        self.assertFalse(loader.is_entity_available("entidade_inexistente"))

    def test_fallback_to_luna(self):
        loader = EntityLoader("entidade_inexistente")
        self.assertIn("config", loader.entity_data)

    def test_unavailable_entity_fallback(self):
        loader = EntityLoader("juno")
        config = loader.get_config()
        self.assertIn("name", config)


class TestEntityLoaderRegistry(unittest.TestCase):
    def test_registry_exists(self):
        self.assertTrue(REGISTRY_PATH.exists())

    def test_registry_valid_json(self):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            registry = json.load(f)
        self.assertIn("entities", registry)
        self.assertIn("luna", registry["entities"])

    def test_entities_dir_exists(self):
        self.assertTrue(ENTITIES_DIR.exists())

    def test_luna_entity_dir_exists(self):
        luna_dir = ENTITIES_DIR / "luna"
        self.assertTrue(luna_dir.exists())

    def test_luna_config_exists(self):
        config_path = ENTITIES_DIR / "luna" / "config.json"
        self.assertTrue(config_path.exists())

    def test_luna_alma_exists(self):
        alma_path = ENTITIES_DIR / "luna" / "alma.txt"
        self.assertTrue(alma_path.exists())


class TestActiveEntity(unittest.TestCase):
    def test_get_active_entity(self):
        entity_id = get_active_entity()
        self.assertIsInstance(entity_id, str)
        self.assertIn(entity_id, ["luna", "juno", "eris", "mars", "lars", "somn"])

    def test_set_active_entity_valid(self):
        original = get_active_entity()
        result = set_active_entity("luna")
        self.assertTrue(result)
        self.assertEqual(get_active_entity(), "luna")
        if original != "luna":
            set_active_entity(original)

    def test_set_active_entity_invalid(self):
        original = get_active_entity()
        result = set_active_entity("entidade_inexistente")
        self.assertFalse(result)
        self.assertEqual(get_active_entity(), original)


class TestThemeManager(unittest.TestCase):
    def test_import_theme_manager(self):
        from src.ui.theme_manager import ThemeManager, get_theme_manager

        self.assertIsNotNone(ThemeManager)
        self.assertIsNotNone(get_theme_manager)

    def test_theme_manager_init(self):
        from src.ui.theme_manager import ThemeManager

        tm = ThemeManager("luna")
        self.assertEqual(tm.entity_id, "luna")
        self.assertIn("primary_color", tm.theme)

    def test_theme_manager_generate_css(self):
        from src.ui.theme_manager import ThemeManager

        tm = ThemeManager("luna")
        css = tm._generate_css_overrides()
        self.assertIsInstance(css, str)
        self.assertIn("Screen", css)
        self.assertIn(tm.get_color("primary_color"), css)

    def test_theme_manager_reload(self):
        from src.ui.theme_manager import ThemeManager

        tm = ThemeManager("luna")
        tm.reload_for_entity("luna")
        self.assertEqual(tm.entity_id, "luna")


class TestEntitySelector(unittest.TestCase):
    def test_import_entity_selector(self):
        from src.ui.entity_selector import EntitySelectorScreen

        self.assertIsNotNone(EntitySelectorScreen)


class TestAnimationControllerIntegration(unittest.TestCase):
    def test_animation_controller_import(self):
        from src.core.animation import AnimationController

        self.assertIsNotNone(AnimationController)


class TestPersonalidadeIntegration(unittest.TestCase):
    def test_personalidade_import(self):
        from src.soul.personalidade import DicionarioPersonalidade, get_personalidade

        self.assertIsNotNone(get_personalidade)
        self.assertIsNotNone(DicionarioPersonalidade)

    def test_get_personalidade(self):
        from src.soul.personalidade import get_personalidade

        p = get_personalidade()
        self.assertIsNotNone(p)


class TestScreensIntegration(unittest.TestCase):
    def test_canone_screen_import(self):
        from src.ui.screens import CanoneScreen

        self.assertIsNotNone(CanoneScreen)

    def test_history_screen_import(self):
        from src.ui.screens import HistoryScreen

        self.assertIsNotNone(HistoryScreen)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestEntityLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestEntityLoaderRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestActiveEntity))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEntitySelector))
    suite.addTests(loader.loadTestsFromTestCase(TestAnimationControllerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonalidadeIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestScreensIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
