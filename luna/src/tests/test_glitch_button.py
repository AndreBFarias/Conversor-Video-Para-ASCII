from unittest.mock import patch


class TestGlitchChars:
    def test_glitch_chars_exist(self):
        from src.ui.glitch_button import GLITCH_CHARS

        assert len(GLITCH_CHARS) > 0

    def test_glitch_chars_are_string(self):
        from src.ui.glitch_button import GLITCH_CHARS

        assert isinstance(GLITCH_CHARS, str)


class TestGlitchButtonInit:
    def test_creates_with_label(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")

        assert button._original_label == "Test"

    def test_initial_state(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")

        assert button._in_glitch is False
        assert button._glitch_frames == 0
        assert button._is_active is False
        assert button._click_glitch_remaining == 0

    def test_timer_is_none_before_mount(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")

        assert button._glitch_timer is None


class TestGlitchButtonShouldGlitch:
    def test_returns_true_for_click_glitch(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._click_glitch_remaining = 5

        assert button._should_glitch() is True

    def test_returns_true_when_active(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._is_active = True

        assert button._should_glitch() is True

    def test_returns_false_when_inactive(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._is_active = False
        button._click_glitch_remaining = 0

        assert button._should_glitch() is False


class TestGlitchButtonRenderNormal:
    def test_restores_original_label(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Original")
        button.label = "Changed"

        button._render_normal()

        assert str(button.label) == "Original"


class TestGlitchButtonGetGlitchColors:
    def test_returns_list(self):
        with patch("src.ui.glitch_button.config") as mock_config:
            with patch("src.ui.glitch_button.get_ui_colors") as mock_colors:
                mock_config.GLITCH_COLORS = {
                    "tv_accent": "#aaaaaa",
                    "text_primary": "#bbbbbb",
                    "text_secondary": "#cccccc",
                }
                mock_colors.return_value = {"primary": "#111111", "secondary": "#222222", "text_user": "#333333"}

                from src.ui.glitch_button import GlitchButton

                button = GlitchButton("Test")
                colors = button._get_glitch_colors()

                assert isinstance(colors, list)
                assert len(colors) == 3


class TestGlitchButtonRenderGlitched:
    def test_creates_text_object(self):
        with patch("src.ui.glitch_button.config") as mock_config:
            with patch("src.ui.glitch_button.get_ui_colors") as mock_colors:
                mock_config.GLITCH_COLORS = {
                    "tv_accent": "#bd93f9",
                    "text_primary": "#f8f8f2",
                    "text_secondary": "#6272a4",
                }
                mock_colors.return_value = {"primary": "#bd93f9", "secondary": "#6272a4", "text_user": "#f8f8f2"}

                from src.ui.glitch_button import GlitchButton

                button = GlitchButton("Test")
                button._render_glitched()

                assert button.label is not None

    def test_handles_short_label(self):
        with patch("src.ui.glitch_button.config") as mock_config:
            with patch("src.ui.glitch_button.get_ui_colors") as mock_colors:
                mock_config.GLITCH_COLORS = {
                    "tv_accent": "#bd93f9",
                    "text_primary": "#f8f8f2",
                    "text_secondary": "#6272a4",
                }
                mock_colors.return_value = {"primary": "#bd93f9", "secondary": "#6272a4", "text_user": "#f8f8f2"}

                from src.ui.glitch_button import GlitchButton

                button = GlitchButton("AB")
                button._render_glitched()

                assert button.label is not None


class TestGlitchButtonSetActive:
    def test_sets_active_true(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")

        button.set_active(True)

        assert button._is_active is True

    def test_sets_active_false(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._is_active = True

        button.set_active(False)

        assert button._is_active is False


class TestGlitchButtonGlitchTick:
    def test_decrements_click_remaining(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._click_glitch_remaining = 5
        button._in_glitch = False
        button._is_active = False

        button._glitch_tick()

        assert button._click_glitch_remaining == 4

    def test_stops_glitch_when_not_active(self):
        from src.ui.glitch_button import GlitchButton

        button = GlitchButton("Test")
        button._in_glitch = True
        button._is_active = False
        button._click_glitch_remaining = 0

        button._glitch_tick()

        assert button._in_glitch is False
