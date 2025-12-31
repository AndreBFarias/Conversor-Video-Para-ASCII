import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.fixture(autouse=True)
def reset_singleton():
    from src.soul import voice_normalizer

    voice_normalizer._normalizer_instance = None
    yield
    voice_normalizer._normalizer_instance = None


@pytest.fixture
def mock_config():
    with patch("src.soul.voice_normalizer.config") as mock:
        mock.ENTITIES_DIR = Path("/tmp/test_entities")
        mock.get_current_entity_id.return_value = "luna"
        mock.get_coqui_reference_audio.return_value = "/tmp/reference.wav"
        mock.get_chatterbox_reference_audio.return_value = "/tmp/chatter.wav"
        mock.get_coqui_speaker_embedding.return_value = "/tmp/embedding.pt"
        yield mock


class TestNormalizedVoiceParams:
    def test_default_values(self):
        from src.soul.voice_normalizer import NormalizedVoiceParams

        params = NormalizedVoiceParams()
        assert params.stability == 0.5
        assert params.style == 0.5
        assert params.speed == 1.0
        assert params.similarity == 0.75

    def test_to_coqui_returns_dict(self):
        from src.soul.voice_normalizer import NormalizedVoiceParams

        params = NormalizedVoiceParams(stability=0.7, speed=1.2)
        result = params.to_coqui()
        assert isinstance(result, dict)
        assert "speed" in result
        assert "temperature" in result
        assert result["speed"] == 1.2
        assert result["temperature"] == pytest.approx(0.3)

    def test_to_chatterbox_returns_dict(self):
        from src.soul.voice_normalizer import NormalizedVoiceParams

        params = NormalizedVoiceParams(style=0.6, stability=0.8)
        result = params.to_chatterbox()
        assert isinstance(result, dict)
        assert "exaggeration" in result
        assert "cfg_weight" in result
        assert result["exaggeration"] == 0.6
        assert result["cfg_weight"] == 0.8

    def test_to_elevenlabs_returns_dict(self):
        from src.soul.voice_normalizer import NormalizedVoiceParams

        params = NormalizedVoiceParams(similarity=0.9)
        result = params.to_elevenlabs()
        assert isinstance(result, dict)
        assert "stability" in result
        assert "similarity_boost" in result
        assert "use_speaker_boost" in result
        assert result["use_speaker_boost"] is True

    def test_to_elevenlabs_low_similarity(self):
        from src.soul.voice_normalizer import NormalizedVoiceParams

        params = NormalizedVoiceParams(similarity=0.5)
        result = params.to_elevenlabs()
        assert result["use_speaker_boost"] is False


class TestVoiceNormalizer:
    def test_init_with_entity(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("eris")
            assert vn.entity_id == "eris"

    def test_init_default_entity(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer()
            assert vn.entity_id == "luna"

    def test_get_params_for_coqui(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            params = vn.get_params_for_engine("coqui", "neutral")
            assert isinstance(params, dict)
            assert "speed" in params
            assert "temperature" in params

    def test_get_params_for_chatterbox(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            params = vn.get_params_for_engine("chatterbox", "feliz")
            assert isinstance(params, dict)
            assert "exaggeration" in params

    def test_get_params_for_elevenlabs(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            params = vn.get_params_for_engine("elevenlabs", "triste")
            assert isinstance(params, dict)
            assert "stability" in params

    def test_emotion_mapping_pt_br(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            emotions = ["feliz", "triste", "irritada", "curiosa", "sarcastica", "flertando"]
            for emotion in emotions:
                params = vn.get_params_for_engine("coqui", emotion)
                assert isinstance(params, dict)

    def test_unknown_emotion_uses_default(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            params = vn.get_params_for_engine("coqui", "unknown_emotion")
            default = vn.get_params_for_engine("coqui", "neutral")
            assert params["speed"] == default["speed"]

    def test_get_reference_audio_coqui(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            ref = vn.get_reference_audio("coqui")
            assert ref == "/tmp/reference.wav"

    def test_get_reference_audio_chatterbox(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            ref = vn.get_reference_audio("chatterbox")
            assert ref == "/tmp/chatter.wav"

    def test_get_speaker_embedding(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            emb = vn.get_speaker_embedding("coqui")
            assert emb == "/tmp/embedding.pt"

    def test_reload_for_entity(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import VoiceNormalizer

            vn = VoiceNormalizer("luna")
            vn.reload_for_entity("eris")
            assert vn.entity_id == "eris"

    def test_config_overrides(self, mock_config):
        voice_config = {"voice": {"coqui": {"stability": 0.9, "speed": 0.8}}}
        with patch("src.soul.voice_normalizer.read_json_safe", return_value=voice_config):
            from src.soul.voice_normalizer import VoiceNormalizer

            mock_config.ENTITIES_DIR = Path("/tmp")
            with patch.object(Path, "exists", return_value=True):
                vn = VoiceNormalizer("luna")
                params = vn.get_params_for_engine("coqui", "neutral")
                assert params["speed"] == 0.8


class TestGetVoiceNormalizer:
    def test_singleton_pattern(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import get_voice_normalizer, reset_voice_normalizer

            reset_voice_normalizer()
            vn1 = get_voice_normalizer("luna")
            vn2 = get_voice_normalizer()
            assert vn1 is vn2

    def test_reload_on_different_entity(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import get_voice_normalizer, reset_voice_normalizer

            reset_voice_normalizer()
            vn1 = get_voice_normalizer("luna")
            vn2 = get_voice_normalizer("eris")
            assert vn2.entity_id == "eris"

    def test_reset_clears_instance(self, mock_config):
        with patch("src.soul.voice_normalizer.read_json_safe", return_value={}):
            from src.soul.voice_normalizer import get_voice_normalizer, reset_voice_normalizer

            vn1 = get_voice_normalizer("luna")
            reset_voice_normalizer()
            from src.soul import voice_normalizer

            assert voice_normalizer._normalizer_instance is None
