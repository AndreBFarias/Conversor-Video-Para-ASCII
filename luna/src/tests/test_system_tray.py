import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_singleton():
    from src.core import system_tray

    system_tray._tray_instance = None
    yield
    system_tray._tray_instance = None


@pytest.fixture
def mock_pystray():
    with patch.dict("sys.modules", {"pystray": MagicMock(), "PIL": MagicMock(), "PIL.Image": MagicMock()}):
        yield


class TestLunaTray:
    def test_init_without_pystray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            assert tray.icon is None

    def test_init_with_callback(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            callback = MagicMock()
            tray = LunaTray(app_callback=callback)
            assert tray.app_callback == callback

    def test_start_without_pystray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            tray.start()
            assert tray.icon is None

    def test_stop_without_icon(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            tray.stop()
            assert tray.icon is None

    def test_update_status(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            tray.update_status("listening")
            assert tray._status == "listening"

    def test_notify_without_tray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            result = tray.notify("Title", "Message")
            assert result is None

    def test_is_running_false_without_icon(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            assert tray.is_running is False

    def test_callback_new_conversation(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            callback = MagicMock()
            tray = LunaTray(app_callback=callback)
            tray._on_new_conversation()
            callback.assert_called_once_with("new_conversation")

    def test_callback_settings(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            callback = MagicMock()
            tray = LunaTray(app_callback=callback)
            tray._on_settings()
            callback.assert_called_once_with("settings")

    def test_callback_quit(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            callback = MagicMock()
            tray = LunaTray(app_callback=callback)
            tray._on_quit()
            callback.assert_called_once_with("quit")


class TestGetTray:
    def test_returns_none_without_pystray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import get_tray

            result = get_tray()
            assert result is None

    def test_reset_tray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import reset_tray

            reset_tray()
            from src.core import system_tray

            assert system_tray._tray_instance is None


class TestTrayWithMockedDeps:
    def test_create_default_icon_without_pystray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            result = tray._create_default_icon()
            assert result is None

    def test_create_menu_without_pystray(self):
        with patch("src.core.system_tray.TRAY_AVAILABLE", False):
            from src.core.system_tray import LunaTray

            tray = LunaTray()
            tray._create_menu()
            assert not hasattr(tray, "menu") or tray.menu is None
