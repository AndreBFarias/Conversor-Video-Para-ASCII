import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config


class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def ok(msg: str) -> str:
    return f"{Colors.OK}[OK]{Colors.RESET} {msg}"


def fail(msg: str) -> str:
    return f"{Colors.FAIL}[FAIL]{Colors.RESET} {msg}"


def warn(msg: str) -> str:
    return f"{Colors.WARN}[WARN]{Colors.RESET} {msg}"


def info(msg: str) -> str:
    return f"{Colors.INFO}[INFO]{Colors.RESET} {msg}"


class TestGlitchConfig:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestGlitchConfig ==={Colors.RESET}")
        self.test_glitch_config_exists()
        self.test_glitch_config_defaults()
        self.test_glitch_palettes_exist()
        self.test_glitch_palette_structure()
        self.test_glitch_colors_active()
        return self.results

    def test_glitch_config_exists(self):
        try:
            assert hasattr(config, "GLITCH_CONFIG"), "GLITCH_CONFIG nao existe"
            assert isinstance(config.GLITCH_CONFIG, dict), "GLITCH_CONFIG nao e dict"
            self.results["glitch_config_exists"] = True
            print(ok("GLITCH_CONFIG existe e e dict"))
        except AssertionError as e:
            self.results["glitch_config_exists"] = False
            print(fail(str(e)))

    def test_glitch_config_defaults(self):
        try:
            required_keys = [
                "PISCANDO_FPS",
                "TV_TRANSITION_DURATION",
                "EFFECT_DURATION_AVG",
                "EFFECT_INTERVAL",
                "BANNER_TRIGGER",
                "BUTTON_TRIGGER",
            ]
            for key in required_keys:
                assert key in config.GLITCH_CONFIG, f"Chave {key} falta em GLITCH_CONFIG"
                assert isinstance(config.GLITCH_CONFIG[key], float), f"{key} deveria ser float"

            assert config.GLITCH_CONFIG["PISCANDO_FPS"] > 0, "FPS deve ser > 0"
            assert 0 <= config.GLITCH_CONFIG["BANNER_TRIGGER"] <= 1, "BANNER_TRIGGER deve estar entre 0-1"
            assert 0 <= config.GLITCH_CONFIG["BUTTON_TRIGGER"] <= 1, "BUTTON_TRIGGER deve estar entre 0-1"

            self.results["glitch_config_defaults"] = True
            print(ok("GLITCH_CONFIG tem todas as chaves com valores validos"))
        except AssertionError as e:
            self.results["glitch_config_defaults"] = False
            print(fail(str(e)))

    def test_glitch_palettes_exist(self):
        try:
            assert hasattr(config, "GLITCH_PALETTES"), "GLITCH_PALETTES nao existe"
            assert isinstance(config.GLITCH_PALETTES, dict), "GLITCH_PALETTES nao e dict"

            required_palettes = ["dracula", "neon", "monokai", "blood"]
            for palette in required_palettes:
                assert palette in config.GLITCH_PALETTES, f"Paleta {palette} falta"

            self.results["glitch_palettes_exist"] = True
            print(ok(f"GLITCH_PALETTES tem {len(config.GLITCH_PALETTES)} paletas"))
        except AssertionError as e:
            self.results["glitch_palettes_exist"] = False
            print(fail(str(e)))

    def test_glitch_palette_structure(self):
        try:
            required_keys = ["tv_base", "tv_accent", "text_primary", "text_secondary"]
            for name, palette in config.GLITCH_PALETTES.items():
                for key in required_keys:
                    assert key in palette, f"Paleta {name} falta chave {key}"
                assert isinstance(palette["tv_base"], list), f"tv_base em {name} deve ser lista"
                assert len(palette["tv_base"]) >= 4, f"tv_base em {name} deve ter 4+ cores"

            self.results["glitch_palette_structure"] = True
            print(ok("Todas as paletas tem estrutura correta"))
        except AssertionError as e:
            self.results["glitch_palette_structure"] = False
            print(fail(str(e)))

    def test_glitch_colors_active(self):
        try:
            assert hasattr(config, "GLITCH_COLORS"), "GLITCH_COLORS nao existe"
            assert isinstance(config.GLITCH_COLORS, dict), "GLITCH_COLORS nao e dict"
            assert "tv_accent" in config.GLITCH_COLORS, "GLITCH_COLORS falta tv_accent"

            self.results["glitch_colors_active"] = True
            print(ok("GLITCH_COLORS ativo com paleta configurada"))
        except AssertionError as e:
            self.results["glitch_colors_active"] = False
            print(fail(str(e)))


class TestVisaoModule:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestVisaoModule ==={Colors.RESET}")
        self.test_visao_import()
        self.test_visao_instantiate()
        self.test_vision_cache_ttl()
        self.test_vision_provider_config()
        return self.results

    def test_visao_import(self):
        try:
            from src.soul.visao import Visao

            self.results["visao_import"] = True
            print(ok("Modulo visao importado"))
        except ImportError as e:
            self.results["visao_import"] = False
            print(fail(f"Falha ao importar visao: {e}"))
        assert self.results.get("visao_import"), "Falha ao importar Visao"

    def test_visao_instantiate(self):
        try:
            from src.soul.visao import Visao

            visao = Visao()
            assert visao is not None, "Visao retornou None"
            self.results["visao_instantiate"] = True
            print(ok("Visao instanciado com sucesso"))
        except Exception as e:
            self.results["visao_instantiate"] = False
            print(fail(f"Falha ao instanciar Visao: {e}"))

    def test_vision_cache_ttl(self):
        try:
            from src.soul.visao import Visao

            visao = Visao()
            assert hasattr(visao, "vision_cache_ttl"), "vision_cache_ttl nao existe"
            assert visao.vision_cache_ttl > 0, "TTL deve ser > 0"
            self.results["vision_cache_ttl"] = True
            print(ok(f"Cache TTL: {visao.vision_cache_ttl}s"))
        except Exception as e:
            self.results["vision_cache_ttl"] = False
            print(warn(f"vision_cache_ttl: {e}"))

    def test_vision_provider_config(self):
        try:
            assert hasattr(config, "VISION_PROVIDER"), "VISION_PROVIDER nao existe"
            assert config.VISION_PROVIDER in ["local", "gemini"], f"Provider invalido: {config.VISION_PROVIDER}"
            self.results["vision_provider_config"] = True
            print(ok(f"VISION_PROVIDER: {config.VISION_PROVIDER}"))
        except AssertionError as e:
            self.results["vision_provider_config"] = False
            print(fail(str(e)))


class TestAnimationController:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestAnimationController ==={Colors.RESET}")
        self.test_animation_import()
        self.test_emotion_map_exists()
        self.test_action_animations_exists()
        self.test_piscando_animation_file()
        return self.results

    def test_animation_import(self):
        try:
            from src.core.animation import AnimationController

            self.results["animation_import"] = True
            print(ok("AnimationController importado"))
        except ImportError as e:
            self.results["animation_import"] = False
            print(fail(f"Falha ao importar: {e}"))
        assert self.results.get("animation_import"), "Falha ao importar AnimationController"

    def test_emotion_map_exists(self):
        try:
            assert hasattr(config, "EMOTION_MAP"), "EMOTION_MAP nao existe"
            assert isinstance(config.EMOTION_MAP, dict), "EMOTION_MAP nao e dict"
            assert len(config.EMOTION_MAP) >= 5, "EMOTION_MAP deve ter pelo menos 5 emocoes"
            self.results["emotion_map_exists"] = True
            print(ok(f"EMOTION_MAP tem {len(config.EMOTION_MAP)} emocoes"))
        except AssertionError as e:
            self.results["emotion_map_exists"] = False
            print(fail(str(e)))

    def test_action_animations_exists(self):
        try:
            assert hasattr(config, "ACTION_ANIMATIONS"), "ACTION_ANIMATIONS nao existe"
            assert isinstance(config.ACTION_ANIMATIONS, dict), "ACTION_ANIMATIONS nao e dict"
            assert "piscando" in config.ACTION_ANIMATIONS, "piscando deve estar em ACTION_ANIMATIONS"
            self.results["action_animations_exists"] = True
            print(ok(f"ACTION_ANIMATIONS tem {len(config.ACTION_ANIMATIONS)} acoes"))
        except AssertionError as e:
            self.results["action_animations_exists"] = False
            print(fail(str(e)))

    def test_piscando_animation_file(self):
        try:
            import gzip

            piscando_path = config.ACTION_ANIMATIONS.get("piscando")
            assert piscando_path is not None, "piscando nao definido"
            assert piscando_path.exists(), f"Arquivo nao existe: {piscando_path}"

            if str(piscando_path).endswith(".gz"):
                with gzip.open(piscando_path, "rt", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = piscando_path.read_text()
            assert "[FRAME]" in content, "Arquivo deve conter [FRAME]"

            self.results["piscando_animation_file"] = True
            print(ok("piscando.txt.gz existe e tem frames"))
        except Exception as e:
            self.results["piscando_animation_file"] = False
            print(fail(str(e)))


class TestCanoneScreen:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestCanoneScreen ==={Colors.RESET}")
        self.test_canone_import()
        self.test_env_get_function()
        return self.results

    def test_canone_import(self):
        try:
            from src.ui.screens import CanoneScreen

            self.results["canone_import"] = True
            print(ok("CanoneScreen importado"))
        except ImportError as e:
            self.results["canone_import"] = False
            print(fail(f"Falha ao importar: {e}"))
        assert self.results.get("canone_import"), "Falha ao importar CanoneScreen"

    def test_env_get_function(self):
        try:
            from src.ui.screens import CanoneScreen

            screen = CanoneScreen.__new__(CanoneScreen)
            screen._env_values = {}
            result = screen._get_env("TEST_VAR_INEXISTENTE", "default_value")
            assert result == "default_value", f"Esperado default_value, recebeu {result}"
            self.results["env_get_function"] = True
            print(ok("_get_env funciona com valores padrao"))
        except Exception as e:
            self.results["env_get_function"] = False
            print(fail(str(e)))


class TestGlitchButton:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestGlitchButton ==={Colors.RESET}")
        self.test_glitch_button_import()
        self.test_glitch_button_uses_config()
        return self.results

    def test_glitch_button_import(self):
        try:
            from src.ui.glitch_button import GlitchButton

            self.results["glitch_button_import"] = True
            print(ok("GlitchButton importado"))
        except ImportError as e:
            self.results["glitch_button_import"] = False
            print(fail(f"Falha ao importar: {e}"))
        assert self.results.get("glitch_button_import"), "Falha ao importar GlitchButton"

    def test_glitch_button_uses_config(self):
        try:
            import src.ui.glitch_button as gb_module

            source = open(gb_module.__file__).read()

            assert "import config" in source, "GlitchButton deve importar config"
            assert "config.GLITCH_CONFIG" in source, "Deve usar config.GLITCH_CONFIG"
            assert "config.GLITCH_COLORS" in source, "Deve usar config.GLITCH_COLORS"

            self.results["glitch_button_uses_config"] = True
            print(ok("GlitchButton usa config.GLITCH_CONFIG e GLITCH_COLORS"))
        except Exception as e:
            self.results["glitch_button_uses_config"] = False
            print(fail(str(e)))


class TestBanner:
    def __init__(self):
        self.results = {}

    def run_all(self):
        print(f"\n{Colors.BOLD}=== TestBanner ==={Colors.RESET}")
        self.test_banner_import()
        self.test_banner_uses_config()
        return self.results

    def test_banner_import(self):
        try:
            from src.ui.banner import Banner

            self.results["banner_import"] = True
            print(ok("Banner importado"))
        except ImportError as e:
            self.results["banner_import"] = False
            print(fail(f"Falha ao importar: {e}"))
        assert self.results.get("banner_import"), "Falha ao importar Banner"

    def test_banner_uses_config(self):
        try:
            import src.ui.banner as banner_module

            source = open(banner_module.__file__).read()

            assert "import config" in source, "Banner deve importar config"
            assert "config.GLITCH_CONFIG" in source, "Deve usar config.GLITCH_CONFIG"

            self.results["banner_uses_config"] = True
            print(ok("BannerWidget usa config.GLITCH_CONFIG"))
        except Exception as e:
            self.results["banner_uses_config"] = False
            print(fail(str(e)))


def run_all_tests():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  TESTES AUTOMATIZADOS - LUNA FEATURES  {Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

    all_results = {}

    glitch_tests = TestGlitchConfig()
    all_results["glitch_config"] = glitch_tests.run_all()

    visao_tests = TestVisaoModule()
    all_results["visao"] = visao_tests.run_all()

    animation_tests = TestAnimationController()
    all_results["animation"] = animation_tests.run_all()

    canone_tests = TestCanoneScreen()
    all_results["canone"] = canone_tests.run_all()

    glitch_button_tests = TestGlitchButton()
    all_results["glitch_button"] = glitch_button_tests.run_all()

    banner_tests = TestBanner()
    all_results["banner"] = banner_tests.run_all()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  RESUMO  {Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

    total_passed = 0
    total_failed = 0

    for category, results in all_results.items():
        passed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        total_passed += passed
        total_failed += failed

        status = f"{Colors.OK}PASSOU{Colors.RESET}" if failed == 0 else f"{Colors.FAIL}FALHOU{Colors.RESET}"
        print(f"  {category}: {passed}/{passed+failed} {status}")

    print(f"\n{Colors.BOLD}Total: {total_passed} passed, {total_failed} failed{Colors.RESET}")

    if total_failed == 0:
        print(f"\n{Colors.OK}{Colors.BOLD}TODOS OS TESTES PASSARAM{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}ALGUNS TESTES FALHARAM{Colors.RESET}")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)


# "A duvida e o principio da sabedoria."
# - Aristoteles
