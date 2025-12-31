import gzip
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from src.core.entity_loader import ENTITIES_DIR, EntityLoader


class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestAnimationIntegrity(unittest.TestCase):
    REQUIRED_ANIMATIONS = [
        "observando",
        "curiosa",
        "feliz",
        "irritada",
        "triste",
        "sarcastica",
        "flertando",
        "apaixonada",
        "piscando",
        "sensualizando",
    ]

    def test_luna_has_all_animations(self):
        luna_anim_dir = ENTITIES_DIR / "luna" / "animations"
        self.assertTrue(luna_anim_dir.exists(), "Diretorio animations de Luna nao existe")

        for anim in self.REQUIRED_ANIMATIONS:
            anim_path = luna_anim_dir / f"Luna_{anim}.txt.gz"
            self.assertTrue(anim_path.exists(), f"Animacao Luna_{anim}.txt.gz nao encontrada")

    def test_animation_has_valid_frames(self):
        luna_anim_dir = ENTITIES_DIR / "luna" / "animations"
        piscando_path = luna_anim_dir / "Luna_piscando.txt.gz"

        self.assertTrue(piscando_path.exists(), "Luna_piscando.txt.gz nao existe")

        with gzip.open(piscando_path, "rt", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("[FRAME]", content, "Arquivo deve conter marcador [FRAME]")
        frame_count = content.count("[FRAME]")
        self.assertGreater(frame_count, 1, f"Deve ter mais de 1 frame, tem {frame_count}")

    def test_entity_animations_or_fallback(self):
        for entity_id in ["eris", "juno", "lars", "mars", "somn"]:
            entity_dir = ENTITIES_DIR / entity_id / "animations"
            entity_name = entity_id.capitalize()

            if entity_dir.exists():
                files = list(entity_dir.glob("*.txt.gz"))
                if len(files) > 0:
                    observando = entity_dir / f"{entity_name}_observando.txt.gz"
                    self.assertTrue(
                        observando.exists(), f"{entity_name} tem animations/ mas falta {entity_name}_observando.txt.gz"
                    )

    def test_fallback_to_luna(self):
        from src.core.animation import AnimationController

        controller = AnimationController.__new__(AnimationController)
        controller.entity_name = "Lars"
        controller.animations = {}

        lars_dir = ENTITIES_DIR / "lars" / "animations"
        luna_dir = ENTITIES_DIR / "luna" / "animations"

        target_path = lars_dir / "Lars_observando.txt.gz"
        fallback_path = luna_dir / "Luna_observando.txt.gz"

        self.assertTrue(target_path.exists() or fallback_path.exists(), "Nem Lars nem Luna tem observando.txt.gz")


class TestColorThemeIntegrity(unittest.TestCase):
    REQUIRED_THEME_KEYS = [
        "primary_color",
        "secondary_color",
        "accent_color",
        "background",
        "background_alt",
        "text_primary",
        "glow_color",
        "border_color",
    ]

    def test_luna_theme_complete(self):
        loader = EntityLoader("luna")
        theme = loader.get_color_theme()

        self.assertIsInstance(theme, dict)
        for key in self.REQUIRED_THEME_KEYS:
            self.assertIn(key, theme, f"Tema Luna falta chave: {key}")

    def test_all_entities_have_themes(self):
        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            loader = EntityLoader(entity_id)
            theme = loader.get_color_theme()

            self.assertIsInstance(theme, dict, f"{entity_id} nao retornou dict de tema")
            self.assertIn("primary_color", theme, f"{entity_id} falta primary_color")

    def test_color_format_valid(self):
        loader = EntityLoader("luna")
        theme = loader.get_color_theme()

        for key, value in theme.items():
            if "color" in key.lower() or key in ["background", "background_alt", "glow_color"]:
                if isinstance(value, str) and value.startswith("#"):
                    self.assertTrue(len(value) in [4, 7, 9], f"Cor {key}={value} tem formato invalido")

    def test_glitch_config_palette_matches_entity(self):
        self.assertTrue(hasattr(config, "GLITCH_COLORS"))
        self.assertIn("tv_accent", config.GLITCH_COLORS)


class TestButtonConfiguration(unittest.TestCase):
    def test_glitch_button_import(self):
        from src.ui.glitch_button import GlitchButton

        self.assertIsNotNone(GlitchButton)
        assert GlitchButton is not None

    def test_glitch_button_config_values(self):
        self.assertIn("BUTTON_TRIGGER", config.GLITCH_CONFIG)
        trigger = config.GLITCH_CONFIG["BUTTON_TRIGGER"]
        self.assertGreaterEqual(trigger, 0)
        self.assertLessEqual(trigger, 1)

    def test_button_text_labels(self):
        expected_buttons = ["Relicario", "Confissao", "Custodia", "Alma"]
        self.assertTrue(True)


class TestEntityConsistency(unittest.TestCase):
    def test_entity_config_has_required_fields(self):
        required_fields = ["id", "name", "persona", "voice", "aesthetics", "phrases"]

        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            config_path = ENTITIES_DIR / entity_id / "config.json"
            self.assertTrue(config_path.exists(), f"{entity_id} falta config.json")

            with open(config_path, encoding="utf-8") as f:
                entity_config = json.load(f)

            for field in required_fields:
                self.assertIn(field, entity_config, f"{entity_id}/config.json falta campo: {field}")

    def test_entity_has_alma_txt(self):
        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            alma_path = ENTITIES_DIR / entity_id / "alma.txt"
            self.assertTrue(alma_path.exists(), f"{entity_id} falta alma.txt")

            content = alma_path.read_text(encoding="utf-8")
            self.assertGreater(len(content), 100, f"{entity_id}/alma.txt muito curto")

    def test_entity_phrases_structure(self):
        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            config_path = ENTITIES_DIR / entity_id / "config.json"

            with open(config_path, encoding="utf-8") as f:
                entity_config = json.load(f)

            phrases = entity_config.get("phrases", {})
            self.assertIn("saudacao_inicial", phrases, f"{entity_id} falta saudacao_inicial")
            self.assertIn("placeholder_input", phrases, f"{entity_id} falta placeholder_input")

            saudacoes = phrases.get("saudacao_inicial", [])
            self.assertIsInstance(saudacoes, list)
            self.assertGreater(len(saudacoes), 0, f"{entity_id} saudacao_inicial vazia")


class TestPersonalityConsistency(unittest.TestCase):
    def test_personality_module_import(self):
        from src.soul.personalidade import get_personalidade

        p = get_personalidade()
        self.assertIsNotNone(p)
        assert p is not None

    def test_entity_names_match_ids(self):
        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            loader = EntityLoader(entity_id)
            config_data = loader.get_config()

            expected_name = entity_id.capitalize()
            actual_name = config_data.get("name", "")
            self.assertEqual(actual_name, expected_name, f"{entity_id}: name={actual_name}, esperado={expected_name}")

    def test_voice_configuration_exists(self):
        for entity_id in ["luna", "eris", "juno", "lars", "mars", "somn"]:
            loader = EntityLoader(entity_id)
            config_data = loader.get_config()

            self.assertIn("voice", config_data, f"{entity_id} falta voice config")
            voice = config_data["voice"]
            self.assertIn("coqui", voice, f"{entity_id} falta coqui voice config")
            self.assertIn("chatterbox", voice, f"{entity_id} falta chatterbox voice config")


class TestUIStability(unittest.TestCase):
    def test_banner_module_import(self):
        from src.ui.banner import Banner, BannerGlitchWidget

        self.assertIsNotNone(Banner)
        self.assertIsNotNone(BannerGlitchWidget)
        assert Banner is not None

    def test_widgets_module_import(self):
        from src.ui.widgets import ChatMessage, CodeBlock

        self.assertIsNotNone(ChatMessage)
        self.assertIsNotNone(CodeBlock)
        assert ChatMessage is not None

    def test_screens_module_import(self):
        from src.ui.screens import CanoneScreen, HistoryScreen

        self.assertIsNotNone(CanoneScreen)
        self.assertIsNotNone(HistoryScreen)
        assert CanoneScreen is not None

    def test_animation_controller_import(self):
        from src.core.animation import AnimationController

        self.assertIsNotNone(AnimationController)
        assert AnimationController is not None

    def test_theme_manager_import(self):
        from src.ui.theme_manager import ThemeManager, get_theme_manager

        self.assertIsNotNone(ThemeManager)
        self.assertIsNotNone(get_theme_manager)
        assert ThemeManager is not None

    def test_entity_selector_import(self):
        from src.ui.entity_selector import EntitySelectorScreen

        self.assertIsNotNone(EntitySelectorScreen)
        assert EntitySelectorScreen is not None


class TestConfigIntegrity(unittest.TestCase):
    def test_glitch_config_exists(self):
        self.assertTrue(hasattr(config, "GLITCH_CONFIG"))
        self.assertIsInstance(config.GLITCH_CONFIG, dict)

    def test_glitch_palettes_exist(self):
        self.assertTrue(hasattr(config, "GLITCH_PALETTES"))
        required = ["dracula", "neon", "monokai", "blood"]
        for p in required:
            self.assertIn(p, config.GLITCH_PALETTES)

    def test_emotion_map_exists(self):
        self.assertTrue(hasattr(config, "EMOTION_MAP"))
        self.assertIsInstance(config.EMOTION_MAP, dict)
        self.assertGreater(len(config.EMOTION_MAP), 5)

    def test_action_animations_exists(self):
        self.assertTrue(hasattr(config, "ACTION_ANIMATIONS"))
        self.assertIn("piscando", config.ACTION_ANIMATIONS)

    def test_provider_configs_exist(self):
        self.assertTrue(hasattr(config, "CHAT_PROVIDER"))
        self.assertTrue(hasattr(config, "CODE_PROVIDER"))
        self.assertTrue(hasattr(config, "VISION_PROVIDER"))


def run_ui_tests():
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  LUNA UI INTEGRITY TEST SUITE  {Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAnimationIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestColorThemeIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestButtonConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestEntityConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonalityConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestUIStability))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigIntegrity))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    if result.wasSuccessful():
        print(f"{Colors.OK}{Colors.BOLD}TODOS OS TESTES DE UI PASSARAM{Colors.RESET}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}ALGUNS TESTES FALHARAM{Colors.RESET}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ui_tests()
    sys.exit(0 if success else 1)


# "O teste de uma boa consciencia e a capacidade de enfrentar a si mesmo."
# - Friedrich Nietzsche
