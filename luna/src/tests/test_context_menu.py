from unittest.mock import MagicMock


class TestContextMenuItemInit:
    def test_creates_with_label(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("Test Label")

        assert item.label_text == "Test Label"
        assert item.shortcut == ""
        assert item.callback is None
        assert item.action == "test_label"

    def test_creates_with_shortcut(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("Copy", shortcut="Ctrl+C")

        assert item.label_text == "Copy"
        assert item.shortcut == "Ctrl+C"

    def test_creates_with_callback(self):
        from src.ui.context_menu import ContextMenuItem

        callback = MagicMock()
        item = ContextMenuItem("Action", callback=callback)

        assert item.callback is callback

    def test_creates_with_action(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("Some Action", action="custom_action")

        assert item.action == "custom_action"

    def test_separator_detected_dashes(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("---")

        assert item.is_separator is True

    def test_separator_detected_line(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("─────")

        assert item.is_separator is True

    def test_regular_item_not_separator(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("Regular Item")

        assert item.is_separator is False

    def test_action_from_label(self):
        from src.ui.context_menu import ContextMenuItem

        item = ContextMenuItem("New Conversation")

        assert item.action == "new_conversation"


class TestContextMenuInit:
    def test_creates_with_defaults(self):
        from src.ui.context_menu import ContextMenu

        menu = ContextMenu()

        assert menu.menu_x == 0
        assert menu.menu_y == 0
        assert menu.custom_items is None

    def test_creates_with_position(self):
        from src.ui.context_menu import ContextMenu

        menu = ContextMenu(x=100, y=50)

        assert menu.menu_x == 100
        assert menu.menu_y == 50

    def test_creates_with_items(self):
        from src.ui.context_menu import ContextMenu, ContextMenuItem

        items = [ContextMenuItem("Item 1"), ContextMenuItem("Item 2")]
        menu = ContextMenu(items=items)

        assert menu.custom_items == items
        assert len(menu.custom_items) == 2


class TestContextMenuBindings:
    def test_has_escape_binding(self):
        from src.ui.context_menu import ContextMenu

        bindings = [b.key for b in ContextMenu.BINDINGS]

        assert "escape" in bindings

    def test_has_enter_binding(self):
        from src.ui.context_menu import ContextMenu

        bindings = [b.key for b in ContextMenu.BINDINGS]

        assert "enter" in bindings


class TestContextMenuCSS:
    def test_has_css(self):
        from src.ui.context_menu import ContextMenu

        assert len(ContextMenu.CSS) > 0

    def test_css_contains_container_style(self):
        from src.ui.context_menu import ContextMenu

        assert "context-menu-container" in ContextMenu.CSS

    def test_css_contains_hover_style(self):
        from src.ui.context_menu import ContextMenu

        assert ":hover" in ContextMenu.CSS

    def test_css_contains_focus_style(self):
        from src.ui.context_menu import ContextMenu

        assert ":focus" in ContextMenu.CSS


class TestContextMenuActionDismiss:
    def test_action_dismiss_calls_dismiss(self):
        from src.ui.context_menu import ContextMenu

        menu = ContextMenu()
        menu.dismiss = MagicMock()

        menu.action_dismiss()

        menu.dismiss.assert_called_once()
