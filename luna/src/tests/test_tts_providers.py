from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.soul.boca.providers.base import TTSParams, TTSProvider


class TestTTSParams:
    def test_default_values(self):
        params = TTSParams()
        assert params.speed == 1.0
        assert params.stability == 0.5
        assert params.style == 0.0
        assert params.extra == {}

    def test_custom_values(self):
        params = TTSParams(speed=1.5, stability=0.8, style=0.3, extra={"key": "value"})
        assert params.speed == 1.5
        assert params.stability == 0.8
        assert params.style == 0.3
        assert params.extra == {"key": "value"}

    def test_from_metatags_none(self):
        params = TTSParams.from_metatags(None)
        assert params.speed == 1.0
        assert params.stability == 0.5
        assert params.style == 0.0

    def test_from_metatags_empty(self):
        params = TTSParams.from_metatags({})
        assert params.speed == 1.0
        assert params.stability == 0.5
        assert params.style == 0.0

    def test_from_metatags_partial(self):
        params = TTSParams.from_metatags({"speed": 1.2})
        assert params.speed == 1.2
        assert params.stability == 0.5
        assert params.style == 0.0

    def test_from_metatags_full(self):
        metatags = {
            "speed": 0.8,
            "stability": 0.9,
            "style": 0.5,
            "extra": {"emotion": "happy"},
        }
        params = TTSParams.from_metatags(metatags)
        assert params.speed == 0.8
        assert params.stability == 0.9
        assert params.style == 0.5
        assert params.extra == {"emotion": "happy"}


class TestTTSProviderBase:
    def test_abstract_cannot_instantiate(self):
        mock_boca = MagicMock()
        with pytest.raises(TypeError):
            TTSProvider(mock_boca)

    def test_concrete_provider_structure(self):
        class ConcreteProvider(TTSProvider):
            name = "test"
            priority = 50

            def check_availability(self) -> bool:
                return True

            def generate(self, text: str, params: TTSParams) -> str | None:
                return "/tmp/test.wav"

            def speak(self, text: str, params: TTSParams) -> bool:
                return True

        mock_boca = MagicMock()
        provider = ConcreteProvider(mock_boca)

        assert provider.name == "test"
        assert provider.priority == 50
        assert provider.is_available is False
        assert provider.get_reference_audio() is None
        assert repr(provider) == "<ConcreteProvider [N/A]>"

    def test_repr_available(self):
        class ConcreteProvider(TTSProvider):
            name = "test"
            priority = 50

            def check_availability(self) -> bool:
                self._available = True
                return True

            def generate(self, text: str, params: TTSParams) -> str | None:
                return None

            def speak(self, text: str, params: TTSParams) -> bool:
                return False

        mock_boca = MagicMock()
        provider = ConcreteProvider(mock_boca)
        provider.check_availability()

        assert repr(provider) == "<ConcreteProvider [OK]>"


class TestCoquiProvider:
    @pytest.fixture
    def mock_boca(self):
        boca = MagicMock()
        boca.venv_tts_python = "/path/to/venv/bin/python"
        boca.tts_wrapper_path = "/path/to/wrapper.py"
        boca.coqui_reference_audio = "/path/to/reference.wav"
        return boca

    def test_init(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        assert provider.name == "coqui"
        assert provider.priority == 20
        assert provider.is_available is False

    def test_check_availability_success(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)

        with patch("src.soul.boca.engine_check._check_coqui_internal", return_value=True):
            result = provider.check_availability()

        assert result is True
        assert provider.is_available is True
        assert provider._venv_python == "/path/to/venv/bin/python"

    def test_check_availability_failure(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)

        with patch("src.soul.boca.engine_check._check_coqui_internal", return_value=False):
            result = provider.check_availability()

        assert result is False
        assert provider.is_available is False

    def test_generate_not_available(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        result = provider.generate("test", TTSParams())
        assert result is None

    def test_generate_success(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        provider._available = True
        provider._venv_python = "/path/to/python"
        provider._wrapper_path = "/path/to/wrapper"
        provider._reference_audio = "/path/to/ref.wav"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "SUCCESS: audio generated"

        with patch("subprocess.run", return_value=mock_result):
            with patch(
                "src.soul.boca.providers.coqui.get_temp_audio_path",
                return_value="/tmp/test.wav",
            ):
                result = provider.generate("test text", TTSParams())

        assert result == "/tmp/test.wav"

    def test_generate_wrapper_fails(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        provider._available = True
        provider._venv_python = "/path/to/python"
        provider._wrapper_path = "/path/to/wrapper"
        provider._reference_audio = "/path/to/ref.wav"

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "error"

        with patch("subprocess.run", return_value=mock_result):
            with patch(
                "src.soul.boca.providers.coqui.get_temp_audio_path",
                return_value="/tmp/test.wav",
            ):
                result = provider.generate("test text", TTSParams())

        assert result is None

    def test_generate_timeout(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        provider._available = True
        provider._venv_python = "/path/to/python"
        provider._wrapper_path = "/path/to/wrapper"
        provider._reference_audio = "/path/to/ref.wav"

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)):
            with patch(
                "src.soul.boca.providers.coqui.get_temp_audio_path",
                return_value="/tmp/test.wav",
            ):
                result = provider.generate("test text", TTSParams())

        assert result is None

    def test_speak_not_available(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        result = provider.speak("test", TTSParams())
        assert result is False

    def test_speak_success(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        provider._available = True

        with patch.object(provider, "generate", return_value="/tmp/test.wav"):
            with patch("src.soul.boca.playback.play_audio_file", return_value=True):
                with patch("src.soul.boca.temp_audio.cleanup_temp_audio"):
                    result = provider.speak("test text", TTSParams())

        assert result is True

    def test_get_reference_audio(self, mock_boca):
        from src.soul.boca.providers.coqui import CoquiProvider

        provider = CoquiProvider(mock_boca)
        provider._reference_audio = "/path/to/ref.wav"
        assert provider.get_reference_audio() == "/path/to/ref.wav"


class TestChatterboxProvider:
    @pytest.fixture
    def mock_boca(self):
        boca = MagicMock()
        boca.venv_tts_python = "/path/to/venv/bin/python"
        boca.chatterbox_wrapper_path = "/path/to/wrapper.py"
        boca.chatterbox_reference_audio = "/path/to/reference.wav"
        return boca

    def test_init(self, mock_boca):
        from src.soul.boca.providers.chatterbox import ChatterboxProvider

        provider = ChatterboxProvider(mock_boca)
        assert provider.name == "chatterbox"
        assert provider.priority == 30
        assert provider.is_available is False

    def test_check_availability_success(self, mock_boca):
        from src.soul.boca.providers.chatterbox import ChatterboxProvider

        provider = ChatterboxProvider(mock_boca)

        with patch(
            "src.soul.boca.engine_check._check_chatterbox_internal",
            return_value=True,
        ):
            result = provider.check_availability()

        assert result is True
        assert provider.is_available is True

    def test_generate_success(self, mock_boca):
        from src.soul.boca.providers.chatterbox import ChatterboxProvider

        provider = ChatterboxProvider(mock_boca)
        provider._available = True
        provider._venv_python = "/path/to/python"
        provider._wrapper_path = "/path/to/wrapper"
        provider._reference_audio = "/path/to/ref.wav"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "SUCCESS: audio generated"

        with patch("subprocess.run", return_value=mock_result):
            with patch(
                "src.soul.boca.providers.chatterbox.get_temp_audio_path",
                return_value="/tmp/test.wav",
            ):
                result = provider.generate("test text", TTSParams())

        assert result == "/tmp/test.wav"

    def test_generate_no_success_marker(self, mock_boca):
        from src.soul.boca.providers.chatterbox import ChatterboxProvider

        provider = ChatterboxProvider(mock_boca)
        provider._available = True
        provider._venv_python = "/path/to/python"
        provider._wrapper_path = "/path/to/wrapper"
        provider._reference_audio = "/path/to/ref.wav"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Something else"

        with patch("subprocess.run", return_value=mock_result):
            with patch(
                "src.soul.boca.providers.chatterbox.get_temp_audio_path",
                return_value="/tmp/test.wav",
            ):
                result = provider.generate("test text", TTSParams())

        assert result is None


class TestElevenLabsProvider:
    @pytest.fixture
    def mock_boca(self):
        boca = MagicMock()
        boca.elevenlabs_voice_id = "voice123"
        return boca

    def test_init(self, mock_boca):
        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)
        assert provider.name == "elevenlabs"
        assert provider.priority == 10
        assert provider.is_available is False

    def test_check_availability_success(self, mock_boca):
        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)

        with patch(
            "src.soul.boca.engine_check._check_elevenlabs_internal",
            return_value=True,
        ):
            with patch("src.soul.boca.providers.elevenlabs.config") as mock_config:
                mock_config.ELEVENLABS_API_KEY = "test_key"
                result = provider.check_availability()

        assert result is True
        assert provider.is_available is True

    def test_generate_success(self, mock_boca):
        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)
        provider._available = True
        provider._voice_id = "voice123"
        provider._api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"

        with patch("requests.post", return_value=mock_response):
            with patch(
                "src.soul.boca.providers.elevenlabs.get_temp_audio_path",
                return_value="/tmp/test.mp3",
            ):
                with patch("builtins.open", MagicMock()):
                    result = provider.generate("test text", TTSParams())

        assert result == "/tmp/test.mp3"

    def test_generate_api_error(self, mock_boca):
        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)
        provider._available = True
        provider._voice_id = "voice123"
        provider._api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 401

        with patch("requests.post", return_value=mock_response):
            result = provider.generate("test text", TTSParams())

        assert result is None

    def test_generate_timeout(self, mock_boca):
        import requests

        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)
        provider._available = True
        provider._voice_id = "voice123"
        provider._api_key = "test_key"

        with patch("requests.post", side_effect=requests.exceptions.Timeout()):
            result = provider.generate("test text", TTSParams())

        assert result is None

    def test_speak_success(self, mock_boca):
        from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

        provider = ElevenLabsProvider(mock_boca)
        provider._available = True
        provider._voice_id = "voice123"
        provider._api_key = "test_key"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"

        with patch("requests.post", return_value=mock_response):
            with patch(
                "src.soul.boca.providers.elevenlabs.get_temp_audio_path",
                return_value="/tmp/test.mp3",
            ):
                with patch("builtins.open", MagicMock()):
                    with patch(
                        "src.soul.boca.playback.play_audio_file",
                        return_value=True,
                    ):
                        with patch("src.soul.boca.temp_audio.cleanup_temp_audio"):
                            result = provider.speak("test text", TTSParams())

        assert result is True


class TestDaemonProvider:
    @pytest.fixture
    def mock_boca(self):
        return MagicMock()

    def test_init(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        assert provider.name == "daemon"
        assert provider.priority == 100
        assert provider.is_available is False

    def test_check_availability_no_socket(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)

        with patch("os.path.exists", return_value=False):
            result = provider.check_availability()

        assert result is False
        assert provider.is_available is False

    def test_check_availability_success(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b'{"status": "healthy"}\n'

        with patch("os.path.exists", return_value=True):
            with patch("socket.socket", return_value=mock_socket):
                result = provider.check_availability()

        assert result is True
        assert provider.is_available is True

    def test_check_availability_connection_error(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)

        with patch("os.path.exists", return_value=True):
            with patch(
                "socket.socket",
                side_effect=ConnectionRefusedError("Connection refused"),
            ):
                result = provider.check_availability()

        assert result is False
        assert provider.is_available is False

    def test_generate_not_available(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        result = provider.generate("test", TTSParams())
        assert result is None

    def test_generate_success(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        provider._available = True

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b'{"status": "success", "path": "/tmp/audio.wav", "duration": 1.5}\n'

        with patch("socket.socket", return_value=mock_socket):
            result = provider.generate("test text", TTSParams())

        assert result == "/tmp/audio.wav"

    def test_generate_timeout(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        provider._available = True

        mock_socket = MagicMock()
        mock_socket.connect.side_effect = TimeoutError("timeout")

        with patch("socket.socket", return_value=mock_socket):
            result = provider.generate("test text", TTSParams())

        assert result is None
        assert provider.is_available is False

    def test_generate_error_response(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        provider._available = True

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b'{"status": "error", "message": "TTS failed"}\n'

        with patch("socket.socket", return_value=mock_socket):
            result = provider.generate("test text", TTSParams())

        assert result is None

    def test_speak_success(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        provider._available = True

        with patch.object(provider, "generate", return_value="/tmp/test.wav"):
            with patch("src.soul.boca.playback.play_audio_file", return_value=True):
                with patch("os.remove"):
                    result = provider.speak("test text", TTSParams())

        assert result is True

    def test_speak_generate_fails(self, mock_boca):
        from src.soul.boca.providers.daemon import DaemonProvider

        provider = DaemonProvider(mock_boca)
        provider._available = True

        with patch.object(provider, "generate", return_value=None):
            result = provider.speak("test text", TTSParams())

        assert result is False


class TestBocaIntegration:
    @pytest.fixture
    def mock_dependencies(self):
        with patch("src.soul.boca.core.get_active_entity", return_value="luna"):
            with patch("src.soul.boca.core.EntityLoader") as mock_loader:
                mock_loader.return_value.get_config.return_value = {"voice": {}}
                with patch("src.soul.boca.engine_check.check_daemon"):
                    with patch("src.soul.boca.engine_check.check_elevenlabs"):
                        with patch("src.soul.boca.engine_check.check_coqui"):
                            with patch("src.soul.boca.engine_check.check_chatterbox"):
                                with patch(
                                    "src.soul.boca.engine_check.get_effective_engine",
                                    return_value="none",
                                ):
                                    yield

    def test_boca_init_providers(self, mock_dependencies):
        from src.soul.boca.core import Boca

        boca = Boca()
        providers = boca.get_providers()
        assert isinstance(providers, list)

    def test_boca_get_provider_by_name(self, mock_dependencies):
        from src.soul.boca.core import Boca

        boca = Boca()

        provider = boca.get_provider_by_name("nonexistent")
        assert provider is None

    def test_falar_empty_text(self, mock_dependencies):
        from src.soul.boca.core import Boca

        boca = Boca()
        result1 = boca.falar("")
        result2 = boca.falar("   ")
        assert result1 is None
        assert result2 is None

    def test_gerar_audio_empty_text(self, mock_dependencies):
        from src.soul.boca.core import Boca

        boca = Boca()
        result = boca.gerar_audio("")
        assert result is None

    def test_reload_for_entity(self, mock_dependencies):
        from src.soul.boca.core import Boca

        boca = Boca()

        with patch("src.soul.boca.core.EntityLoader") as mock_loader:
            mock_loader.return_value.get_config.return_value = {"voice": {}}
            with patch("src.soul.boca.engine_check.check_elevenlabs"):
                with patch("src.soul.boca.engine_check.check_coqui"):
                    with patch("src.soul.boca.engine_check.check_chatterbox"):
                        with patch(
                            "src.soul.boca.engine_check.get_effective_engine",
                            return_value="none",
                        ):
                            boca.reload_for_entity("eris")

        assert boca.active_entity_id == "eris"


class TestProviderOrdering:
    def test_provider_priority_sorting(self):
        from src.soul.boca.providers.base import TTSParams, TTSProvider

        class LowPriority(TTSProvider):
            name = "low"
            priority = 10

            def check_availability(self):
                return True

            def generate(self, text, params):
                return None

            def speak(self, text, params):
                return False

        class HighPriority(TTSProvider):
            name = "high"
            priority = 100

            def check_availability(self):
                return True

            def generate(self, text, params):
                return None

            def speak(self, text, params):
                return False

        mock_boca = MagicMock()
        providers = [LowPriority(mock_boca), HighPriority(mock_boca)]
        providers.sort(key=lambda p: -p.priority)

        assert providers[0].name == "high"
        assert providers[1].name == "low"
