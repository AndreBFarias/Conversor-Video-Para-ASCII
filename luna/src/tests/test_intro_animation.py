from unittest.mock import MagicMock, patch


class TestGlitchCharsConstants:
    def test_light_chars_exist(self):
        from src.ui.intro_animation import GLITCH_CHARS_LIGHT

        assert len(GLITCH_CHARS_LIGHT) > 0

    def test_medium_chars_exist(self):
        from src.ui.intro_animation import GLITCH_CHARS_MEDIUM

        assert len(GLITCH_CHARS_MEDIUM) > 0

    def test_heavy_chars_exist(self):
        from src.ui.intro_animation import GLITCH_CHARS_HEAVY

        assert len(GLITCH_CHARS_HEAVY) > 0

    def test_static_chars_exist(self):
        from src.ui.intro_animation import STATIC_CHARS

        assert len(STATIC_CHARS) > 0


class TestGetPersonaConfigs:
    def test_returns_dict(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import _get_persona_configs

            result = _get_persona_configs()

            assert isinstance(result, dict)

    def test_contains_luna(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import _get_persona_configs

            result = _get_persona_configs()

            assert "LUNA" in result


class TestPersonaIntroInit:
    def test_creates_instance(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("TestName")

            assert intro.persona_name == "TESTNAME"

    def test_initializes_display(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")

            assert len(intro.current_display) == 4
            assert len(intro.locked_positions) == 4


class TestPersonaIntroRandomChar:
    def test_returns_string(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            char = intro._random_char()

            assert isinstance(char, str)
            assert len(char) == 1

    def test_high_intensity_uses_heavy(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import GLITCH_CHARS_HEAVY, PersonaIntro

            intro = PersonaIntro("Test")
            char = intro._random_char(0.8)

            assert char in GLITCH_CHARS_HEAVY


class TestPersonaIntroBuildNameDisplay:
    def test_returns_text(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from rich.text import Text

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            result = intro._build_name_display()

            assert isinstance(result, Text)


class TestPersonaIntroBuildScanline:
    def test_returns_text(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from rich.text import Text

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            result = intro._build_scanline(active=True)

            assert isinstance(result, Text)

    def test_inactive_returns_empty(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            result = intro._build_scanline(active=False)

            assert len(result) == 0


class TestPersonaIntroBuildStaticNoise:
    def test_returns_text(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
                "background": "#000000",
            }

            from rich.text import Text

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            result = intro._build_static_noise(0.5)

            assert isinstance(result, Text)


class TestPersonaIntroOnComplete:
    def test_stores_callback(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            callback = MagicMock()
            intro = PersonaIntro("Test")

            result = intro.on_complete(callback)

            assert intro._on_complete == callback
            assert result is intro


class TestPersonaIntroGetStaticDisplay:
    def test_returns_text(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from rich.text import Text

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            result = intro.get_static_display()

            assert isinstance(result, Text)

    def test_locks_all_positions(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import PersonaIntro

            intro = PersonaIntro("Test")
            intro.get_static_display()

            assert all(intro.locked_positions)


class TestBannerAnimationInit:
    def test_creates_instance(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
            }

            from src.ui.intro_animation import BannerAnimation

            banner = BannerAnimation("Test")

            assert banner.persona is not None
            assert banner._running is False


class TestBannerAnimationGetIdleFrame:
    def test_returns_frame(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
                "background": "#000000",
            }

            from src.ui.intro_animation import BannerAnimation

            banner = BannerAnimation("Test")
            result = banner.get_idle_frame()

            assert result is not None

    def test_handles_glitch_flag(self):
        with patch("src.ui.intro_animation.persona_intro.get_ui_colors") as mock_colors:
            mock_colors.return_value = {
                "primary": "#aaaaaa",
                "secondary": "#bbbbbb",
                "text_error": "#cccccc",
                "text_user": "#dddddd",
                "accent": "#eeeeee",
                "text_secondary": "#ffffff",
                "text_success": "#00ff00",
                "background": "#000000",
            }

            from src.ui.intro_animation import BannerAnimation

            banner = BannerAnimation("Test")
            result = banner.get_idle_frame(with_glitch=True)

            assert result is not None
