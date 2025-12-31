from pathlib import Path
from unittest.mock import MagicMock, patch


class TestOuvidoSussurranteInit:
    def test_creates_instance(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad") as mock_vad:
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.return_value = {
                        "index": 0,
                        "name": "Default",
                        "defaultSampleRate": 16000,
                    }

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()

                    assert ouvido.p is not None
                    assert ouvido.vad is not None

    def test_sample_rate_default(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.return_value = {
                        "index": 0,
                        "name": "Default",
                        "defaultSampleRate": 48000,
                    }

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()

                    assert ouvido.sample_rate == 48000


class TestOuvidoSussurranteFindBestDevice:
    def test_finds_pulse_device(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 2
                    mock_p.get_device_info_by_index.side_effect = [
                        {"index": 0, "name": "HDMI Output", "maxInputChannels": 0, "defaultSampleRate": 44100},
                        {"index": 1, "name": "pulse input", "maxInputChannels": 2, "defaultSampleRate": 48000},
                    ]

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()

                    assert ouvido.device_index == 1

    def test_skips_monitor_devices(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 2
                    mock_p.get_device_info_by_index.side_effect = [
                        {"index": 0, "name": "Monitor of Output", "maxInputChannels": 2, "defaultSampleRate": 44100},
                        {"index": 1, "name": "Microphone", "maxInputChannels": 1, "defaultSampleRate": 16000},
                    ]

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()

                    assert ouvido.device_index == 1


class TestOuvidoSussurranteInitWhisper:
    def test_returns_true_if_model_exists(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}
                    mock_config.WHISPER_CONFIG = {"MODEL_SIZE": "small", "COMPUTE_TYPE": "int8", "USE_GPU": False}
                    mock_config.WHISPER_MODELS_DIR = Path("/tmp")

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.return_value = {
                        "index": 0,
                        "name": "Default",
                        "defaultSampleRate": 16000,
                    }

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()
                    ouvido.model = MagicMock()

                    result = ouvido._init_whisper()

                    assert result is True


class TestOuvidoSussurranteOuvirETranscrever:
    def test_returns_none_without_whisper(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}
                    mock_config.WHISPER_CONFIG = {"MODEL_SIZE": "small", "COMPUTE_TYPE": "int8", "USE_GPU": False}
                    mock_config.WHISPER_MODELS_DIR = Path("/tmp")

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.return_value = {
                        "index": 0,
                        "name": "Default",
                        "defaultSampleRate": 16000,
                    }

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()
                    ouvido.model = None

                    with patch.object(ouvido, "_init_whisper", return_value=False):
                        result = ouvido.ouvir_e_transcrever()

                    assert result is None

    def test_returns_none_without_device(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}
                    mock_config.WHISPER_CONFIG = {"MODEL_SIZE": "small", "COMPUTE_TYPE": "int8", "USE_GPU": False}
                    mock_config.WHISPER_MODELS_DIR = Path("/tmp")

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.side_effect = Exception("No device")

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()
                    ouvido.model = MagicMock()

                    with patch.object(ouvido, "_init_whisper", return_value=True):
                        result = ouvido.ouvir_e_transcrever()

                    assert result is None


class TestOuvidoSussurranteClose:
    def test_terminates_pyaudio(self):
        with patch("src.soul.comunicacao.pyaudio") as mock_pyaudio:
            with patch("src.soul.comunicacao.webrtcvad"):
                with patch("src.soul.comunicacao.config") as mock_config:
                    mock_config.AUDIO_CONFIG = {"SAMPLE_RATE": 16000, "DEVICE_ID": None}
                    mock_config.VAD_CONFIG = {"MODE": 2, "FRAME_BUFFER_SIZE": 6}

                    mock_p = MagicMock()
                    mock_pyaudio.PyAudio.return_value = mock_p
                    mock_p.get_device_count.return_value = 0
                    mock_p.get_default_input_device_info.return_value = {
                        "index": 0,
                        "name": "Default",
                        "defaultSampleRate": 16000,
                    }

                    from src.soul.comunicacao import OuvidoSussurrante

                    ouvido = OuvidoSussurrante()

                    ouvido.close()

                    mock_p.terminate.assert_called_once()
