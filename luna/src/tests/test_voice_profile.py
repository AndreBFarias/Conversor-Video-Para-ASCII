import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np


class TestVoiceProfile:
    def test_dataclass_fields(self):
        from src.soul.voice_profile import VoiceProfile

        profile = VoiceProfile(
            name="test_user",
            embedding=np.array([0.1, 0.2, 0.3]),
            created_at="2024-01-01",
            sample_count=5,
        )

        assert profile.name == "test_user"
        assert profile.sample_count == 5
        assert profile.embedding is not None


class TestVoiceProfileManagerInit:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                assert manager.user_dir.exists()

    def test_initial_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                assert manager.encoder is None
                assert manager.user_embedding is None
                assert manager._loaded is False


class TestVoiceProfileManagerLoadEncoder:
    def test_returns_false_without_resemblyzer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                with patch.dict("sys.modules", {"resemblyzer": None}):
                    result = manager._load_encoder()

                    assert result is False

    def test_returns_true_if_already_loaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()
                manager.encoder = MagicMock()

                result = manager._load_encoder()

                assert result is True


class TestVoiceProfileManagerHasProfile:
    def test_returns_false_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                assert manager.has_voice_profile is False

    def test_returns_true_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                user_dir = Path(tmpdir) / "user"
                user_dir.mkdir(parents=True, exist_ok=True)
                mock_config.USER_DATA_DIR = user_dir
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                np.save(user_dir / "voice_embedding.npy", np.array([0.1, 0.2]))

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                assert manager.has_voice_profile is True


class TestVoiceProfileManagerGetProfile:
    def test_returns_empty_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                result = manager.get_profile()

                assert result == {}

    def test_returns_profile_when_exists(self):
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                user_dir = Path(tmpdir) / "user"
                user_dir.mkdir(parents=True, exist_ok=True)
                mock_config.USER_DATA_DIR = user_dir
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                with open(user_dir / "profile.json", "w") as f:
                    json.dump({"name": "test_user"}, f)

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                result = manager.get_profile()

                assert result["name"] == "test_user"


class TestVoiceProfileManagerIdentifySpeaker:
    def test_returns_false_without_embedding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import VoiceProfileManager

                manager = VoiceProfileManager()

                audio = np.zeros(16000, dtype=np.float32)
                is_user, similarity = manager.identify_speaker(audio)

                assert is_user is False
                assert similarity == 0.0


class TestAppearanceTracker:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()

                assert tracker.history == []

    def test_add_observation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()

                tracker.add_observation("Pessoa com oculos")

                assert len(tracker.history) == 1
                assert "oculos" in tracker.history[0]["description"]

    def test_normalize(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()

                result = tracker._normalize("Óculos")

                assert result == "oculos"

    def test_detect_change_no_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()

                changed, comment = tracker.detect_change("Pessoa com oculos")

                assert changed is False
                assert comment is None

    def test_detect_change_with_difference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()
                tracker.add_observation("Pessoa sorrindo")

                changed, comment = tracker.detect_change("Pessoa com oculos")

                assert changed is True
                assert comment is not None
                assert "oculos" in comment.lower()

    def test_detect_change_no_difference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()
                tracker.add_observation("Pessoa sorrindo")

                changed, comment = tracker.detect_change("Pessoa sorrindo")

                assert changed is False

    def test_get_recent_observations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()
                for i in range(10):
                    tracker.add_observation(f"Observation {i}")

                recent = tracker.get_recent_observations(3)

                assert len(recent) == 3
                assert "Observation 9" in recent[-1]["description"]

    def test_limits_history_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.appearance.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import AppearanceTracker

                tracker = AppearanceTracker()
                for i in range(60):
                    tracker.add_observation(f"Obs {i}")

                assert len(tracker.history) <= 50


class TestGlobalFunctions:
    def test_get_voice_manager_singleton(self):
        import src.soul.voice_profile as module

        module._voice_manager = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"
                mock_config.VOICE_SIMILARITY_THRESHOLD = 0.7

                from src.soul.voice_profile import get_voice_manager

                m1 = get_voice_manager()
                m2 = get_voice_manager()

                assert m1 is m2

    def test_get_appearance_tracker_singleton(self):
        import src.soul.voice_profile as module

        module._appearance_tracker = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.voice_profile.manager.config") as mock_config:
                mock_config.USER_DATA_DIR = Path(tmpdir) / "user"

                from src.soul.voice_profile import get_appearance_tracker

                t1 = get_appearance_tracker()
                t2 = get_appearance_tracker()

                assert t1 is t2
