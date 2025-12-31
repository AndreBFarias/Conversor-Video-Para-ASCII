import threading
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSanitizeText:
    def test_removes_rich_tags(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("[b]Ola[/b] mundo")

        assert "[b]" not in result
        assert "[/b]" not in result
        assert "Ola" in result

    def test_removes_markdown(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("**texto** e *italico*")

        assert "**" not in result
        assert "*" not in result
        assert "texto" in result

    def test_replaces_urls(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("Veja https://example.com agora")

        assert "https://" not in result
        assert "link" in result

    def test_removes_inline_code(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("Use `print()` para debug")

        assert "`" not in result
        assert "print()" not in result

    def test_handles_empty_string(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("")

        assert result == ""

    def test_handles_none(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text(None)

        assert result == ""

    def test_removes_punctuation_words(self):
        from src.soul.boca import sanitize_text

        result = sanitize_text("Ponto final Virgula teste")

        assert "Ponto" not in result
        assert "Virgula" not in result


class TestTextSanitizerClass:
    def test_class_regex_patterns_exist(self):
        from src.soul.boca import TextSanitizer

        assert hasattr(TextSanitizer, "RE_RICH_TAGS_SIMPLE")
        assert hasattr(TextSanitizer, "RE_MARKDOWN_EMPHASIS")
        assert hasattr(TextSanitizer, "RE_URLS")

    def test_sanitize_classmethod(self):
        from src.soul.boca import TextSanitizer

        result = TextSanitizer.sanitize("[i]test[/i]")

        assert "[i]" not in result
        assert "test" in result


class TestCheckDaemon:
    def test_socket_not_exists(self):
        from src.soul.boca import Boca, check_daemon

        boca = Boca.__new__(Boca)
        boca.daemon_disponivel = False

        with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
            check_daemon(boca)

            assert boca.daemon_disponivel is False

    def test_socket_connection_success(self):
        from src.soul.boca import Boca, check_daemon

        boca = Boca.__new__(Boca)
        boca.daemon_disponivel = False

        with patch("src.soul.boca.engine_check.os.path.exists", return_value=True):
            with patch("src.soul.boca.engine_check.socket.socket") as mock_socket:
                mock_sock = MagicMock()
                mock_socket.return_value = mock_sock

                check_daemon(boca)

                assert boca.daemon_disponivel is True
                mock_sock.connect.assert_called_once()
                mock_sock.close.assert_called_once()

    def test_socket_connection_failure(self):
        from src.soul.boca import Boca, check_daemon

        boca = Boca.__new__(Boca)
        boca.daemon_disponivel = False

        with patch("src.soul.boca.engine_check.os.path.exists", return_value=True):
            with patch("src.soul.boca.engine_check.socket.socket") as mock_socket:
                mock_sock = MagicMock()
                mock_sock.connect.side_effect = Exception("Connection refused")
                mock_socket.return_value = mock_sock

                check_daemon(boca)

                assert boca.daemon_disponivel is False


class TestCheckElevenlabs:
    def test_no_api_key(self):
        from src.soul.boca import Boca, check_elevenlabs

        boca = Boca.__new__(Boca)
        boca.entity_voice_config = {}
        boca.elevenlabs_disponivel = False

        with patch("src.soul.boca.engine_check.config") as mock_config:
            mock_config.ELEVENLABS_API_KEY = None

            check_elevenlabs(boca)

            assert boca.elevenlabs_disponivel is False

    def test_valid_config(self):
        from src.soul.boca import Boca, check_elevenlabs

        boca = Boca.__new__(Boca)
        boca.active_entity_id = "luna"
        boca.entity_voice_config = {"elevenlabs": {"voice_id": "abc123def456"}}
        boca.elevenlabs_disponivel = False

        with patch("src.soul.boca.engine_check.config") as mock_config:
            mock_config.ELEVENLABS_API_KEY = "test_key"
            mock_config.ELEVENLABS_VOICE_ID = None

            check_elevenlabs(boca)

            assert boca.elevenlabs_disponivel is True
            assert boca.elevenlabs_voice_id == "abc123def456"


class TestCheckCoqui:
    def test_no_venv_tts(self):
        from src.soul.boca import Boca, check_coqui

        boca = Boca.__new__(Boca)
        boca.entity_voice_config = {}
        boca.coqui_disponivel = False

        with patch.object(Path, "exists", return_value=False):
            check_coqui(boca)

            assert boca.coqui_disponivel is False


class TestCheckChatterbox:
    def test_no_venv_tts(self):
        from src.soul.boca import Boca, check_chatterbox

        boca = Boca.__new__(Boca)
        boca.entity_voice_config = {}
        boca.chatterbox_disponivel = False

        with patch.object(Path, "exists", return_value=False):
            check_chatterbox(boca)

            assert boca.chatterbox_disponivel is False


class TestGetEffectiveEngine:
    def test_returns_configured_when_available(self):
        from src.soul.boca import Boca, get_effective_engine

        boca = Boca.__new__(Boca)
        boca.chatterbox_disponivel = True
        boca.coqui_disponivel = False
        boca.elevenlabs_disponivel = False

        with patch("src.soul.boca.engine_check.config") as mock_config:
            mock_config.TTS_ENGINE = "chatterbox"

            result = get_effective_engine(boca)

            assert result == "chatterbox"

    def test_fallback_to_available(self):
        from src.soul.boca import Boca, get_effective_engine

        boca = Boca.__new__(Boca)
        boca.chatterbox_disponivel = False
        boca.coqui_disponivel = True
        boca.elevenlabs_disponivel = False

        with patch("src.soul.boca.engine_check.config") as mock_config:
            mock_config.TTS_ENGINE = "chatterbox"

            result = get_effective_engine(boca)

            assert result == "coqui"

    def test_returns_none_when_all_unavailable(self):
        from src.soul.boca import Boca, get_effective_engine

        boca = Boca.__new__(Boca)
        boca.chatterbox_disponivel = False
        boca.coqui_disponivel = False
        boca.elevenlabs_disponivel = False

        with patch("src.soul.boca.engine_check.config") as mock_config:
            mock_config.TTS_ENGINE = "coqui"

            result = get_effective_engine(boca)

            assert result == "none"


class TestPlayAudioFile:
    def test_tries_players_in_order(self):
        from src.soul.boca import Boca, play_audio_file

        boca = Boca.__new__(Boca)
        boca.current_process = None

        with patch("src.soul.boca.playback.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc

            result = play_audio_file(boca, "/tmp/test.wav")

            assert result is True
            mock_popen.assert_called()

    def test_all_players_fail(self):
        from src.soul.boca import Boca, play_audio_file

        boca = Boca.__new__(Boca)
        boca.current_process = None

        with patch("src.soul.boca.playback.subprocess.Popen", side_effect=FileNotFoundError()):
            result = play_audio_file(boca, "/tmp/test.wav")

            assert result is False


class TestBocaInit:
    def test_speech_lock_created(self):
        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            with patch("src.soul.boca.core.get_active_entity", return_value="luna"):
                mock_loader.return_value.get_config.return_value = {}

                with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
                    with patch("src.soul.boca.engine_check.config") as mock_config:
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.TTS_ENGINE = "none"
                        with patch.object(Path, "exists", return_value=False):
                            from src.soul.boca import Boca

                            boca = Boca()

                            assert boca._speech_lock is not None

    def test_entity_loader_initialized(self):
        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            with patch("src.soul.boca.core.get_active_entity", return_value="eris"):
                mock_loader.return_value.get_config.return_value = {"voice": {}}

                with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
                    with patch("src.soul.boca.engine_check.config") as mock_config:
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.TTS_ENGINE = "none"
                        with patch.object(Path, "exists", return_value=False):
                            from src.soul.boca import Boca

                            boca = Boca()

                            assert boca.active_entity_id == "eris"


class TestLoadEntityVoiceConfig:
    def test_loads_voice_from_entity(self):
        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            with patch("src.soul.boca.core.get_active_entity", return_value="luna"):
                voice_config = {"coqui": {"reference_audio": "test.wav"}}
                mock_loader.return_value.get_config.return_value = {"voice": voice_config}

                with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
                    with patch("src.soul.boca.engine_check.config") as mock_config:
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.TTS_ENGINE = "none"
                        with patch.object(Path, "exists", return_value=False):
                            from src.soul.boca import Boca

                            boca = Boca()

                            assert boca.entity_voice_config == voice_config

    def test_returns_empty_on_error(self):
        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            with patch("src.soul.boca.core.get_active_entity", return_value="luna"):
                mock_loader.return_value.get_config.side_effect = Exception("Load error")

                with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
                    with patch("src.soul.boca.engine_check.config") as mock_config:
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.TTS_ENGINE = "none"
                        with patch.object(Path, "exists", return_value=False):
                            from src.soul.boca import Boca

                            boca = Boca()

                            assert boca.entity_voice_config == {}


class TestReloadForEntity:
    def test_reloads_with_new_entity(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca.active_entity_id = "luna"
        boca.entity_loader = MagicMock()
        boca.coqui_disponivel = True
        boca.chatterbox_disponivel = True
        boca.elevenlabs_disponivel = True

        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_config.return_value = {"voice": {}}

            with patch("src.soul.boca.engine_check.os.path.exists", return_value=False):
                with patch("src.soul.boca.engine_check.config") as mock_config:
                    mock_config.ELEVENLABS_API_KEY = None
                    mock_config.TTS_ENGINE = "none"
                    with patch.object(Path, "exists", return_value=False):
                        boca.reload_for_entity("eris")

                        assert boca.active_entity_id == "eris"
                        assert boca.coqui_disponivel is False
                        assert boca.chatterbox_disponivel is False
                        assert boca.elevenlabs_disponivel is False


class TestFalar:
    def test_empty_text_does_nothing(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca._speech_lock = MagicMock()
        boca._falar_interno = MagicMock()

        boca.falar("")

        boca._falar_interno.assert_not_called()

    def test_whitespace_only_does_nothing(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca._speech_lock = MagicMock()
        boca._falar_interno = MagicMock()

        boca.falar("   ")

        boca._falar_interno.assert_not_called()

    def test_calls_interno_with_text(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca._speech_lock = threading.Lock()
        boca._falar_interno = MagicMock()

        boca.falar("Ola mundo")

        boca._falar_interno.assert_called_once_with("Ola mundo", None)


class TestGerarAudio:
    def test_empty_text_returns_none(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)

        result = boca.gerar_audio("")

        assert result is None

    def test_calls_interno_and_logs_event(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca._speech_lock = threading.Lock()
        boca._gerar_audio_interno = MagicMock(return_value="/tmp/audio.wav")

        with patch("src.soul.boca.core.get_event_logger") as mock_logger:
            mock_evt = MagicMock()
            mock_logger.return_value = mock_evt

            with patch("src.soul.boca.core.config") as mock_config:
                mock_config.TTS_ENGINE = "coqui"

                result = boca.gerar_audio("Teste")

                assert result == "/tmp/audio.wav"
                mock_evt.tts.assert_called_once()


class TestParar:
    def test_terminates_current_process(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        boca.current_process = mock_process

        boca.parar()

        mock_process.terminate.assert_called_once()
        assert boca.current_process is None

    def test_handles_no_process(self):
        from src.soul.boca import Boca

        boca = Boca.__new__(Boca)
        boca.current_process = None

        boca.parar()

        assert boca.current_process is None
