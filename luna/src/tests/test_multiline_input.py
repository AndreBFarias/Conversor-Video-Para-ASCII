from unittest.mock import MagicMock


class TestMultilineInputMessages:
    def test_submitted_message_stores_value(self):
        from src.ui.multiline_input import MultilineInput

        msg = MultilineInput.Submitted("test value")

        assert msg.value == "test value"

    def test_reaction_selected_stores_reaction(self):
        from src.ui.multiline_input import MultilineInput

        msg = MultilineInput.ReactionSelected("Luna_feliz")

        assert msg.reaction == "Luna_feliz"


class TestMultilineInputInit:
    def test_creates_with_defaults(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()

        assert widget._placeholder == ""
        assert widget._undo_stack == [""]
        assert widget._redo_stack == []
        assert widget._last_text == ""

    def test_creates_with_placeholder(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput(placeholder="Enter text")

        assert widget._placeholder == "Enter text"

    def test_creates_with_id(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput(id="test-input")

        assert widget.id == "test-input"


class TestMultilineInputPlaceholder:
    def test_placeholder_getter(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput(placeholder="Test")

        assert widget.placeholder == "Test"

    def test_placeholder_setter(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()
        widget._update_placeholder_display = MagicMock()

        widget.placeholder = "New placeholder"

        assert widget._placeholder == "New placeholder"
        widget._update_placeholder_display.assert_called_once()


class TestMultilineInputReactionPattern:
    def test_pattern_matches_react(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()
        match = widget._reaction_pattern.search("/react Luna_feliz")

        assert match is not None
        assert match.group(2) == "Luna_feliz"

    def test_pattern_matches_reacao(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()
        match = widget._reaction_pattern.search("/reacao Luna_triste")

        assert match is not None
        assert match.group(2) == "Luna_triste"

    def test_pattern_case_insensitive(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()
        match = widget._reaction_pattern.search("/REACT Luna_curiosa")

        assert match is not None

    def test_pattern_no_match(self):
        from src.ui.multiline_input import MultilineInput

        widget = MultilineInput()
        match = widget._reaction_pattern.search("hello world")

        assert match is None


class TestMultilineInputBindings:
    def test_has_enter_binding(self):
        from src.ui.multiline_input import MultilineInput

        bindings = [b.key for b in MultilineInput.BINDINGS]

        assert "enter" in bindings

    def test_has_paste_binding(self):
        from src.ui.multiline_input import MultilineInput

        bindings = [b.key for b in MultilineInput.BINDINGS]

        assert "ctrl+v" in bindings

    def test_has_undo_binding(self):
        from src.ui.multiline_input import MultilineInput

        bindings = [b.key for b in MultilineInput.BINDINGS]

        assert "ctrl+z" in bindings

    def test_has_redo_bindings(self):
        from src.ui.multiline_input import MultilineInput

        bindings = [b.key for b in MultilineInput.BINDINGS]

        assert "ctrl+y" in bindings
        assert "ctrl+shift+z" in bindings


class TestMultilineInputCSS:
    def test_has_default_css(self):
        from src.ui.multiline_input import MultilineInput

        assert len(MultilineInput.DEFAULT_CSS) > 0

    def test_css_contains_focus_style(self):
        from src.ui.multiline_input import MultilineInput

        assert ":focus" in MultilineInput.DEFAULT_CSS

    def test_css_contains_cursor_style(self):
        from src.ui.multiline_input import MultilineInput

        assert "cursor" in MultilineInput.DEFAULT_CSS
