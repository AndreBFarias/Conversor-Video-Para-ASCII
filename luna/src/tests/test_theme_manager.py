from unittest.mock import patch


class TestDraculaFallback:
    def test_contains_required_colors(self):
        from src.ui.theme_manager import DRACULA_FALLBACK

        assert "primary_color" in DRACULA_FALLBACK
        assert "secondary_color" in DRACULA_FALLBACK
        assert "accent_color" in DRACULA_FALLBACK
        assert "background" in DRACULA_FALLBACK
        assert "text_primary" in DRACULA_FALLBACK

    def test_colors_are_hex(self):
        from src.ui.theme_manager import DRACULA_FALLBACK

        for key, value in DRACULA_FALLBACK.items():
            assert value.startswith("#")
            assert len(value) == 7


class TestThemeManagerInit:
    def test_creates_with_default_entity(self):
        with patch("src.ui.theme_manager.core.get_active_entity") as mock_get:
            with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
                mock_get.return_value = "luna"
                mock_loader.return_value.get_full_color_theme.return_value = {}

                from src.ui.theme_manager import ThemeManager

                tm = ThemeManager()

                assert tm.entity_id == "luna"

    def test_creates_with_specified_entity(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("eris")

            assert tm.entity_id == "eris"


class TestThemeManagerLoadTheme:
    def test_returns_theme_from_loader(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {
                "primary_color": "#123456",
            }

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")

            assert tm.theme["primary_color"] == "#123456"

    def test_returns_fallback_on_empty(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import DRACULA_FALLBACK, ThemeManager

            tm = ThemeManager("luna")

            assert tm.theme == DRACULA_FALLBACK

    def test_returns_fallback_on_error(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.side_effect = Exception("Test")

            from src.ui.theme_manager import DRACULA_FALLBACK, ThemeManager

            tm = ThemeManager("luna")

            assert tm.theme == DRACULA_FALLBACK


class TestThemeManagerReload:
    def test_reloads_for_new_entity(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {"primary_color": "#111111"}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")
            tm.reload_for_entity("eris")

            assert tm.entity_id == "eris"
            assert tm._css_cache is None


class TestThemeManagerGetColor:
    def test_gets_color_from_theme(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {
                "primary_color": "#abcdef",
            }

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")

            assert tm.get_color("primary_color") == "#abcdef"

    def test_falls_back_to_dracula(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import DRACULA_FALLBACK, ThemeManager

            tm = ThemeManager("luna")

            assert tm.get_color("primary_color") == DRACULA_FALLBACK["primary_color"]

    def test_returns_white_for_unknown(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")

            assert tm.get_color("nonexistent_key") == "#ffffff"


class TestThemeManagerGenerateCSSOverrides:
    def test_generates_css_string(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {
                "primary_color": "#bd93f9",
            }

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")
            css = tm._generate_css_overrides()

            assert isinstance(css, str)
            assert "luna" in css

    def test_includes_screen_styles(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")
            css = tm._generate_css_overrides()

            assert "Screen" in css
            assert "background" in css


class TestThemeManagerGetCachedCSS:
    def test_returns_none_initially(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")

            assert tm.get_cached_css() is None

    def test_returns_cached_after_generation(self):
        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            from src.ui.theme_manager import ThemeManager

            tm = ThemeManager("luna")
            tm._css_cache = "cached css"

            assert tm.get_cached_css() == "cached css"


class TestGetThemeManager:
    def test_returns_instance(self):
        import src.ui.theme_manager.singletons as singletons_module

        singletons_module._theme_manager = None

        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}
            result = singletons_module.get_theme_manager()

            assert result is not None

        singletons_module._theme_manager = None

    def test_returns_same_instance(self):
        import src.ui.theme_manager.singletons as singletons_module

        singletons_module._theme_manager = None

        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            first = singletons_module.get_theme_manager()
            second = singletons_module.get_theme_manager()

            assert first is second

        singletons_module._theme_manager = None


class TestReloadThemeForEntity:
    def test_creates_new_if_none(self):
        import src.ui.theme_manager.singletons as singletons_module

        singletons_module._theme_manager = None

        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            result = singletons_module.reload_theme_for_entity("eris")

            assert result.entity_id == "eris"

        singletons_module._theme_manager = None

    def test_reloads_existing(self):
        import src.ui.theme_manager.singletons as singletons_module
        from src.ui.theme_manager import ThemeManager

        with patch("src.ui.theme_manager.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {}

            singletons_module._theme_manager = ThemeManager("luna")
            original = singletons_module._theme_manager

            result = singletons_module.reload_theme_for_entity("juno")

            assert result is original
            assert result.entity_id == "juno"

        singletons_module._theme_manager = None


class TestGenerateGlitchPaletteFromTheme:
    def test_returns_dict(self):
        from src.ui.theme_manager import generate_glitch_palette_from_theme

        result = generate_glitch_palette_from_theme({})

        assert isinstance(result, dict)

    def test_contains_required_keys(self):
        from src.ui.theme_manager import generate_glitch_palette_from_theme

        result = generate_glitch_palette_from_theme({})

        assert "tv_base" in result
        assert "tv_accent" in result
        assert "glitch_primary" in result
        assert "text_primary" in result

    def test_uses_provided_colors(self):
        from src.ui.theme_manager import generate_glitch_palette_from_theme

        theme = {
            "primary_color": "#111111",
            "secondary_color": "#222222",
        }
        result = generate_glitch_palette_from_theme(theme)

        assert result["glitch_primary"] == "#111111"
        assert result["glitch_secondary"] == "#222222"

    def test_uses_tv_static_config(self):
        from src.ui.theme_manager import generate_glitch_palette_from_theme

        theme = {
            "tv_static": {
                "base": ["#aaa", "#bbb"],
                "accent": "#ccc",
            }
        }
        result = generate_glitch_palette_from_theme(theme)

        assert result["tv_base"] == ["#aaa", "#bbb"]
        assert result["tv_accent"] == "#ccc"


class TestUpdateGlitchColorsForEntity:
    def test_updates_config(self):
        with patch("src.ui.theme_manager.glitch.EntityLoader") as mock_loader:
            mock_loader.return_value.get_color_theme.return_value = {
                "primary_color": "#123456",
            }

            import config
            from src.ui.theme_manager import update_glitch_colors_for_entity

            original = getattr(config, "GLITCH_COLORS", None)
            update_glitch_colors_for_entity("luna")

            assert config.GLITCH_COLORS is not None
            assert config.GLITCH_COLORS["glitch_primary"] == "#123456"

            if original is not None:
                config.GLITCH_COLORS = original

    def test_handles_missing_theme(self):
        with patch("src.ui.theme_manager.glitch.EntityLoader") as mock_loader:
            mock_loader.return_value.get_color_theme.return_value = {}

            from src.ui.theme_manager import update_glitch_colors_for_entity

            result = update_glitch_colors_for_entity("unknown_entity")
            assert result is None

    def test_handles_error(self):
        with patch("src.ui.theme_manager.glitch.EntityLoader") as mock_loader:
            mock_loader.side_effect = Exception("Test error")

            from src.ui.theme_manager import update_glitch_colors_for_entity

            result = update_glitch_colors_for_entity("error_entity")
            assert result is None
