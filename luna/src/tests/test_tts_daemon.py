import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestTTSDaemonClient(unittest.TestCase):
    def test_socket_path_constant(self):
        from src.soul.boca.daemon import TTS_SOCKET_PATH

        assert TTS_SOCKET_PATH == "/tmp/luna_tts_daemon.sock"

    def test_gerar_via_daemon_returns_none_if_not_available(self):
        from src.soul.boca.daemon import gerar_via_daemon

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = False

        result = gerar_via_daemon(mock_boca, "Teste")
        assert result is None

    @patch("src.soul.boca.daemon.socket.socket")
    def test_gerar_via_daemon_handles_timeout(self, mock_socket_class):
        from src.soul.boca.daemon import gerar_via_daemon

        mock_socket = MagicMock()
        mock_socket.connect.side_effect = TimeoutError("Connection timed out")
        mock_socket_class.return_value = mock_socket

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = True

        result = gerar_via_daemon(mock_boca, "Teste")

        assert result is None
        assert mock_boca.daemon_disponivel is False

    @patch("src.soul.boca.daemon.socket.socket")
    def test_gerar_via_daemon_handles_connection_error(self, mock_socket_class):
        from src.soul.boca.daemon import gerar_via_daemon

        mock_socket = MagicMock()
        mock_socket.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_socket

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = True

        result = gerar_via_daemon(mock_boca, "Teste")

        assert result is None
        assert mock_boca.daemon_disponivel is False

    @patch("src.soul.boca.daemon.socket.socket")
    def test_gerar_via_daemon_success(self, mock_socket_class):
        from src.soul.boca.daemon import gerar_via_daemon

        mock_socket = MagicMock()
        response = {"status": "success", "path": "/tmp/test.wav", "duration": 0.5}
        mock_socket.recv.return_value = (json.dumps(response) + "\n").encode("utf-8")
        mock_socket_class.return_value = mock_socket

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = True

        result = gerar_via_daemon(mock_boca, "Teste")

        assert result == "/tmp/test.wav"

    @patch("src.soul.boca.daemon.socket.socket")
    def test_gerar_via_daemon_error_response(self, mock_socket_class):
        from src.soul.boca.daemon import gerar_via_daemon

        mock_socket = MagicMock()
        response = {"status": "error", "message": "Generation failed"}
        mock_socket.recv.return_value = (json.dumps(response) + "\n").encode("utf-8")
        mock_socket_class.return_value = mock_socket

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = True

        result = gerar_via_daemon(mock_boca, "Teste")

        assert result is None


class TestTTSDaemonConstants(unittest.TestCase):
    def test_socket_path(self):
        from src.tools.tts_daemon.constants import SOCKET_PATH

        assert SOCKET_PATH == "/tmp/luna_tts_daemon.sock"

    def test_pid_file(self):
        from src.tools.tts_daemon.constants import PID_FILE

        assert PID_FILE == "/tmp/luna_tts_daemon.pid"

    def test_script_dir_exists(self):
        from src.tools.tts_daemon.constants import SCRIPT_DIR

        assert SCRIPT_DIR.exists()


class TestTTSDaemonCLI(unittest.TestCase):
    def test_is_daemon_running_no_pid_file(self):
        from src.tools.tts_daemon.cli import is_daemon_running

        with patch("os.path.exists", return_value=False):
            assert is_daemon_running() is False

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("os.kill")
    def test_is_daemon_running_process_alive(self, mock_kill, mock_open, mock_exists):
        from src.tools.tts_daemon.cli import is_daemon_running

        mock_exists.return_value = True
        mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value="12345\n")))
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_kill.return_value = None

        with patch("src.tools.tts_daemon.cli.PID_FILE", "/tmp/test_pid"):
            result = is_daemon_running()

        assert result is True


class TestTTSDaemonClass(unittest.TestCase):
    def test_init_default_engine(self):
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            from src.tools.tts_daemon.daemon import TTSDaemon

            daemon = TTSDaemon()
            assert daemon.engine == "coqui"
            assert daemon.model is None
            assert daemon.running is False

    def test_init_chatterbox_engine(self):
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            from src.tools.tts_daemon.daemon import TTSDaemon

            daemon = TTSDaemon(engine="CHATTERBOX")
            assert daemon.engine == "chatterbox"

    def test_init_with_reference_audio(self):
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            from src.tools.tts_daemon.daemon import TTSDaemon

            daemon = TTSDaemon(reference_audio="/path/to/audio.wav")
            assert daemon.reference_audio == "/path/to/audio.wav"


class TestEngineCheck(unittest.TestCase):
    def test_check_daemon_no_socket(self):
        from src.soul.boca.engine_check import check_daemon

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = False

        with patch("os.path.exists", return_value=False):
            check_daemon(mock_boca)

        assert mock_boca.daemon_disponivel is False

    @patch("socket.socket")
    @patch("os.path.exists")
    def test_check_daemon_socket_exists_and_connects(self, mock_exists, mock_socket_class):
        from src.soul.boca.engine_check import check_daemon

        mock_exists.return_value = True
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        mock_boca = MagicMock()
        mock_boca.daemon_disponivel = False

        check_daemon(mock_boca)

        assert mock_boca.daemon_disponivel is True
        assert mock_socket.connect.called
        assert mock_socket.close.called


class TestBocaCoreDaemonIntegration(unittest.TestCase):
    def test_falar_interno_uses_daemon_first(self):
        from src.soul.boca.core import Boca

        with patch.object(Boca, "__init__", lambda x: None):
            boca = Boca()
            boca._speech_lock = MagicMock()
            boca._speech_lock.__enter__ = MagicMock()
            boca._speech_lock.__exit__ = MagicMock()
            boca.daemon_disponivel = True

            with patch("src.soul.boca.daemon.gerar_via_daemon") as mock_daemon:
                with patch("src.soul.boca.playback.play_audio_file") as mock_play:
                    with patch("src.soul.boca.sanitizer.sanitize_text", return_value="Teste"):
                        with patch("config.TTS_ENGINE", "coqui"):
                            mock_daemon.return_value = "/tmp/test.wav"
                            mock_play.return_value = True

                            with patch("os.remove"):
                                boca._falar_interno("Teste")

                            assert mock_daemon.called


if __name__ == "__main__":
    unittest.main()
