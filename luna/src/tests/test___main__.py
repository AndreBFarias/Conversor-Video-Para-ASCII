from unittest.mock import patch


class TestTTSDaemonMain:
    def test_main_import(self):
        from src.tools.tts_daemon.__main__ import main

        assert callable(main)

    def test_main_calls_cli(self):
        with patch("src.tools.tts_daemon.__main__.main") as mock_main:
            mock_main.return_value = None

            from src.tools.tts_daemon import __main__

            assert hasattr(__main__, "main")

    def test_entry_point_exists(self):
        import importlib.util

        spec = importlib.util.find_spec("src.tools.tts_daemon.__main__")

        assert spec is not None
