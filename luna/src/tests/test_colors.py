from unittest.mock import patch


class TestGetUIColors:
    def test_returns_cached_value(self):
        import src.ui.colors as colors_module

        colors_module._color_cache = {"test": "value"}

        result = colors_module.get_ui_colors()

        assert result == {"test": "value"}
        colors_module._color_cache = None

    def test_loads_from_entity_loader(self):
        import src.ui.colors as colors_module

        colors_module._color_cache = None

        with patch("src.core.entity_loader.get_active_loader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {
                "primary_color": "#111111",
                "secondary_color": "#222222",
            }

            result = colors_module.get_ui_colors()

            assert result["primary"] == "#111111"
            assert result["secondary"] == "#222222"

        colors_module._color_cache = None

    def test_returns_fallback_on_error(self):
        import src.ui.colors as colors_module

        colors_module._color_cache = None

        with patch("src.core.entity_loader.get_active_loader") as mock_loader:
            mock_loader.side_effect = Exception("Test error")

            result = colors_module.get_ui_colors()

            assert result["primary"] == "#bd93f9"

        colors_module._color_cache = None


class TestGetTVStaticColors:
    def test_returns_cached_value(self):
        import src.ui.colors as colors_module

        colors_module._tv_static_cache = {"cached": "data"}

        result = colors_module.get_tv_static_colors()

        assert result == {"cached": "data"}
        colors_module._tv_static_cache = None

    def test_loads_from_entity_loader(self):
        import src.ui.colors as colors_module

        colors_module._tv_static_cache = None

        with patch("src.core.entity_loader.get_active_loader") as mock_loader:
            mock_loader.return_value.get_full_color_theme.return_value = {
                "tv_static": {
                    "base": ["#aaa", "#bbb"],
                    "accent": "#ccc",
                },
                "glow_color": "#ddd",
            }

            result = colors_module.get_tv_static_colors()

            assert result["base"] == ["#aaa", "#bbb"]
            assert result["accent"] == "#ccc"

        colors_module._tv_static_cache = None

    def test_returns_fallback_on_error(self):
        import src.ui.colors as colors_module

        colors_module._tv_static_cache = None

        with patch("src.core.entity_loader.get_active_loader") as mock_loader:
            mock_loader.side_effect = Exception("Test error")

            result = colors_module.get_tv_static_colors()

            assert "base" in result
            assert result["accent"] == "#bd93f9"

        colors_module._tv_static_cache = None


class TestGetGlitchColors:
    def test_combines_ui_and_tv_colors(self):
        import src.ui.colors as colors_module

        colors_module._color_cache = {
            "primary": "#p1",
            "secondary": "#s1",
            "accent": "#a1",
            "text_primary": "#tp1",
            "text_secondary": "#ts1",
        }
        colors_module._tv_static_cache = {
            "base": ["#b1"],
            "accent": "#ta1",
            "secondary": "#ts1",
        }

        result = colors_module.get_glitch_colors()

        assert result["tv_base"] == ["#b1"]
        assert result["glitch_primary"] == "#p1"
        assert result["text_primary"] == "#tp1"

        colors_module._color_cache = None
        colors_module._tv_static_cache = None


class TestInvalidateColorCache:
    def test_clears_caches(self):
        import src.ui.colors as colors_module

        colors_module._color_cache = {"data": "here"}
        colors_module._tv_static_cache = {"more": "data"}

        colors_module.invalidate_color_cache()

        assert colors_module._color_cache is None
        assert colors_module._tv_static_cache is None


class TestGetFallbackColors:
    def test_returns_dict(self):
        from src.ui.colors import _get_fallback_colors

        result = _get_fallback_colors()

        assert isinstance(result, dict)

    def test_contains_required_keys(self):
        from src.ui.colors import _get_fallback_colors

        result = _get_fallback_colors()

        assert "primary" in result
        assert "secondary" in result
        assert "accent" in result
        assert "background" in result
        assert "text_primary" in result


class TestHexToRgb:
    def test_converts_with_hash(self):
        from src.ui.colors import hex_to_rgb

        result = hex_to_rgb("#ff5500")

        assert result == (255, 85, 0)

    def test_converts_without_hash(self):
        from src.ui.colors import hex_to_rgb

        result = hex_to_rgb("00ff00")

        assert result == (0, 255, 0)

    def test_converts_black(self):
        from src.ui.colors import hex_to_rgb

        result = hex_to_rgb("#000000")

        assert result == (0, 0, 0)

    def test_converts_white(self):
        from src.ui.colors import hex_to_rgb

        result = hex_to_rgb("#ffffff")

        assert result == (255, 255, 255)


class TestRgbToHex:
    def test_converts_basic(self):
        from src.ui.colors import rgb_to_hex

        result = rgb_to_hex(255, 128, 0)

        assert result == "#ff8000"

    def test_clamps_high_values(self):
        from src.ui.colors import rgb_to_hex

        result = rgb_to_hex(300, 256, 1000)

        assert result == "#ffffff"

    def test_clamps_negative_values(self):
        from src.ui.colors import rgb_to_hex

        result = rgb_to_hex(-10, -5, -100)

        assert result == "#000000"

    def test_returns_black(self):
        from src.ui.colors import rgb_to_hex

        result = rgb_to_hex(0, 0, 0)

        assert result == "#000000"


class TestLightenColor:
    def test_lightens_color(self):
        from src.ui.colors import lighten_color

        result = lighten_color("#808080", 20)

        assert result == "#949494"

    def test_default_amount(self):
        from src.ui.colors import lighten_color

        original = "#505050"
        result = lighten_color(original)

        assert result != original

    def test_clamps_to_white(self):
        from src.ui.colors import lighten_color

        result = lighten_color("#f0f0f0", 50)

        assert result == "#ffffff"


class TestDarkenColor:
    def test_darkens_color(self):
        from src.ui.colors import darken_color

        result = darken_color("#808080", 20)

        assert result == "#6c6c6c"

    def test_default_amount(self):
        from src.ui.colors import darken_color

        original = "#505050"
        result = darken_color(original)

        assert result != original

    def test_clamps_to_black(self):
        from src.ui.colors import darken_color

        result = darken_color("#101010", 50)

        assert result == "#000000"


class TestHexToRgba:
    def test_converts_with_alpha(self):
        from src.ui.colors import hex_to_rgba

        result = hex_to_rgba("#ff0000", 0.5)

        assert result == "rgba(255, 0, 0, 0.5)"

    def test_converts_full_opacity(self):
        from src.ui.colors import hex_to_rgba

        result = hex_to_rgba("#00ff00", 1.0)

        assert result == "rgba(0, 255, 0, 1.0)"

    def test_converts_transparent(self):
        from src.ui.colors import hex_to_rgba

        result = hex_to_rgba("#0000ff", 0.0)

        assert result == "rgba(0, 0, 255, 0.0)"
