class TestDashboardConstants:
    def test_dracula_palette_exists(self):
        from src.ui.dashboard import DRACULA

        assert len(DRACULA) > 0

    def test_dracula_has_bg(self):
        from src.ui.dashboard import DRACULA

        assert "bg" in DRACULA
        assert DRACULA["bg"].startswith("#")

    def test_dracula_has_fg(self):
        from src.ui.dashboard import DRACULA

        assert "fg" in DRACULA
        assert DRACULA["fg"].startswith("#")

    def test_dracula_has_purple(self):
        from src.ui.dashboard import DRACULA

        assert "purple" in DRACULA
        assert DRACULA["purple"] == "#bd93f9"

    def test_matrix_chars_exist(self):
        from src.ui.dashboard import MATRIX_CHARS

        assert len(MATRIX_CHARS) > 0

    def test_glitch_chars_exist(self):
        from src.ui.dashboard import GLITCH_CHARS

        assert len(GLITCH_CHARS) > 0

    def test_boot_messages_exist(self):
        from src.ui.dashboard import BOOT_MESSAGES

        assert len(BOOT_MESSAGES) > 0
        assert isinstance(BOOT_MESSAGES, list)

    def test_boot_messages_are_strings(self):
        from src.ui.dashboard import BOOT_MESSAGES

        for msg in BOOT_MESSAGES:
            assert isinstance(msg, str)

    def test_boot_messages_have_timestamps(self):
        from src.ui.dashboard import BOOT_MESSAGES

        for msg in BOOT_MESSAGES:
            assert "[" in msg


class TestPersonaBannerInit:
    def test_creates_with_defaults(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert banner.persona_name == "LUNA"
        assert banner.font == "slant"

    def test_creates_with_custom_name(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner(persona_name="ERIS")

        assert banner.persona_name == "ERIS"

    def test_creates_with_custom_font(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner(font="banner")

        assert banner.font == "banner"

    def test_name_uppercased(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner(persona_name="luna")

        assert banner.persona_name == "LUNA"

    def test_initializes_lists(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert isinstance(banner._ascii_lines, list)
        assert isinstance(banner._locked_chars, list)
        assert isinstance(banner._current_display, list)

    def test_timer_none_before_mount(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert banner._timer is None


class TestPersonaBannerReactives:
    def test_frame_count_starts_zero(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert banner.frame_count == 0

    def test_is_decrypting_starts_true(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert banner.is_decrypting is True


class TestPersonaBannerGenerateAscii:
    def test_generates_ascii_lines(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert len(banner._ascii_lines) > 0

    def test_generates_locked_chars_for_each_line(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert len(banner._locked_chars) == len(banner._ascii_lines)

    def test_generates_display_for_each_line(self):
        from src.ui.dashboard import PersonaBanner

        banner = PersonaBanner()

        assert len(banner._current_display) == len(banner._ascii_lines)
