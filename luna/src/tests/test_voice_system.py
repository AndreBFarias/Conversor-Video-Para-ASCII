import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestVoiceProfileDataclass:
    def test_fields(self):
        with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
            with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                from src.soul.voice_system import VoiceProfile

                profile = VoiceProfile(
                    name="test_voice",
                    audio_path="/path/to/audio.wav",
                    exaggeration=0.5,
                    cfg_weight=0.5,
                    temperature=0.8,
                    description="Test voice",
                )

                assert profile.name == "test_voice"
                assert profile.audio_path == "/path/to/audio.wav"
                assert profile.exaggeration == 0.5


class TestLunaResponseDataclass:
    def test_fields(self):
        with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
            with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                from src.soul.voice_system import LunaResponse

                response = LunaResponse(
                    text="Hello",
                    audio_path="/tmp/audio.wav",
                    emotion="happy",
                    voice_profile="luna_neutral",
                    generation_time=1.5,
                    engine="coqui-tts",
                )

                assert response.text == "Hello"
                assert response.audio_path == "/tmp/audio.wav"
                assert response.engine == "coqui-tts"

    def test_optional_audio_path(self):
        with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
            with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                from src.soul.voice_system import LunaResponse

                response = LunaResponse(
                    text="Hello",
                    audio_path=None,
                    emotion="neutral",
                    voice_profile="default",
                    generation_time=0.5,
                    engine="none",
                )

                assert response.audio_path is None


class TestCoquiTTSEngineInit:
    def test_creates_directories(self):
        with patch("src.soul.voice_system.system.config") as mock_config:
            mock_config.APP_DIR = Path(tempfile.mkdtemp())

            from src.soul.voice_system import CoquiTTSEngine

            engine = CoquiTTSEngine()

            assert engine.output_dir.exists()


class TestCoquiTTSEngineIsAvailable:
    def test_returns_false_without_venv(self):
        with patch("src.soul.voice_system.engines.config") as mock_config:
            mock_config.APP_DIR = Path(tempfile.mkdtemp())

            from src.soul.voice_system import CoquiTTSEngine

            engine = CoquiTTSEngine()

            assert engine.is_available() is False


class TestCoquiTTSEngineGenerate:
    def test_returns_none_if_not_available(self):
        with patch("src.soul.voice_system.system.config") as mock_config:
            mock_config.APP_DIR = Path(tempfile.mkdtemp())

            from src.soul.voice_system import CoquiTTSEngine

            engine = CoquiTTSEngine()

            with patch.object(engine, "is_available", return_value=False):
                result = engine.generate("Test text")

            assert result is None


class TestChatterboxEngineInit:
    def test_sets_device_cpu(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                from src.soul.voice_system import ChatterboxEngine

                engine = ChatterboxEngine(device="cuda")

                assert engine.device == "cpu"

    def test_uses_cuda_when_available(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):
            with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                from src.soul.voice_system import ChatterboxEngine

                engine = ChatterboxEngine(device="cuda")

                assert engine.device == "cuda"


class TestChatterboxEngineGenerate:
    def test_returns_none_without_model(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                from src.soul.voice_system import ChatterboxEngine

                engine = ChatterboxEngine()

                result = engine.generate("Test text")

                assert result is None


class TestChatterboxEngineCleanup:
    def test_empties_cuda_cache(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):
            with patch.object(torch.cuda, "empty_cache") as mock_empty:
                with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                    from src.soul.voice_system import ChatterboxEngine

                    engine = ChatterboxEngine()

                    engine.cleanup()

                    mock_empty.assert_called()


class TestVoiceManagerInit:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.voice_system import VoiceManager

            manager = VoiceManager(voices_dir=Path(tmpdir) / "voices")

            assert manager.voices_dir.exists()

    def test_initializes_empty_profiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.voice_system import VoiceManager

            manager = VoiceManager(voices_dir=Path(tmpdir) / "voices")

            assert manager.profiles == {}


class TestVoiceManagerGetProfile:
    def test_returns_none_for_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.voice_system import VoiceManager

            manager = VoiceManager(voices_dir=Path(tmpdir))

            result = manager.get_profile("nonexistent")

            assert result is None

    def test_returns_profile_when_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.voice_system import VoiceManager

            manager = VoiceManager(voices_dir=Path(tmpdir))
            manager.add_profile("test", "/path/audio.wav", 0.5, 0.5, 0.8, "Test")

            result = manager.get_profile("test")

            assert result is not None
            assert result.name == "test"


class TestVoiceManagerAddProfile:
    def test_adds_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.voice_system import VoiceManager

            manager = VoiceManager(voices_dir=Path(tmpdir))

            manager.add_profile("new_voice", "/path/audio.wav", 0.6, 0.4, 0.9, "New voice")

            assert "new_voice" in manager.profiles
            assert manager.profiles["new_voice"].exaggeration == 0.6


class TestLunaVoiceSystemInit:
    def test_creates_instance(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        assert system.coqui_engine is not None
                        assert system.voice_manager is not None


class TestLunaVoiceSystemSelectVoiceForEmotion:
    def test_maps_feliz_to_happy(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system._select_voice_for_emotion("feliz")

                        assert result == "luna_playful"

    def test_maps_neutral_correctly(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system._select_voice_for_emotion("neutra")

                        assert result == "luna_neutral"


class TestLunaVoiceSystemSanitizeText:
    def test_removes_markdown_bold(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system._sanitize_text("**bold text**")

                        assert "**" not in result

    def test_removes_code_ticks(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system._sanitize_text("`code here`")

                        assert "`" not in result

    def test_handles_empty_text(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system._sanitize_text("")

                        assert result == ""


class TestLunaVoiceSystemSynthesize:
    def test_returns_response_for_empty_text(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()

                        result = system.synthesize("")

                        assert result.audio_path is None
                        assert result.engine == "none"


class TestLunaVoiceSystemCleanup:
    def test_calls_chatterbox_cleanup(self):
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("src.soul.voice_system.system.config") as mock_config:
                with patch("src.soul.voice_system.system.ELEVENLABS_AVAILABLE", False):
                    with patch("src.soul.voice_system.engines.CHATTERBOX_AVAILABLE", False):
                        mock_config.APP_DIR = Path(tempfile.mkdtemp())
                        mock_config.ELEVENLABS_API_KEY = None
                        mock_config.VOICE_SETTINGS = {}

                        from src.soul.voice_system import LunaVoiceSystem

                        system = LunaVoiceSystem()
                        system.chatterbox_engine.cleanup = MagicMock()

                        system.cleanup()

                        system.chatterbox_engine.cleanup.assert_called_once()
