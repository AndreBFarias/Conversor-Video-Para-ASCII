import time
from threading import Event
from unittest.mock import MagicMock, patch


class TestWakeWordConfigDataclass:
    def test_fields(self):
        from src.soul.wake_word import WakeWordConfig

        config = WakeWordConfig(patterns=["luna", "ei luna"], cooldown=2.0, sample_rate=16000)

        assert config.patterns == ["luna", "ei luna"]
        assert config.cooldown == 2.0
        assert config.sample_rate == 16000


class TestWakeWordDetectorInit:
    def test_default_sample_rate(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                assert detector.sample_rate == 16000

    def test_custom_sample_rate(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector(sample_rate=48000)

                assert detector.sample_rate == 48000

    def test_initial_state(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                assert detector._loaded is False
                assert detector._whisper_model is None
                assert detector._audio_buffer == []


class TestWakeWordDetectorLoadModel:
    def test_loads_vad(self):
        import sys

        mock_vad = MagicMock()
        with patch.dict(sys.modules, {"webrtcvad": mock_vad}):
            with patch("src.soul.wake_word.detector.config") as mock_config:
                with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                    mock_config.WAKE_WORD_COOLDOWN = 2.0
                    mock_config.WAKE_WORD_PATTERNS = ["luna"]
                    mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])
                    mock_config.VAD_CONFIG = {"MODE": 2}

                    from src.soul.wake_word import WakeWordDetector

                    detector = WakeWordDetector()
                    detector.load_model(whisper_model=MagicMock())

                    mock_vad.Vad.assert_called_once()

    def test_returns_true_with_whisper_model(self):
        import sys

        mock_vad = MagicMock()
        with patch.dict(sys.modules, {"webrtcvad": mock_vad}):
            with patch("src.soul.wake_word.detector.config") as mock_config:
                with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                    mock_config.WAKE_WORD_COOLDOWN = 2.0
                    mock_config.WAKE_WORD_PATTERNS = ["luna"]
                    mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])
                    mock_config.VAD_CONFIG = {"MODE": 2}

                    from src.soul.wake_word import WakeWordDetector

                    detector = WakeWordDetector()

                    result = detector.load_model(whisper_model=MagicMock())

                    assert result is True
                    assert detector._loaded is True


class TestWakeWordDetectorIsLoaded:
    def test_returns_false_initially(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                assert detector.is_loaded is False

    def test_returns_true_after_load(self):
        import sys

        mock_vad = MagicMock()
        with patch.dict(sys.modules, {"webrtcvad": mock_vad}):
            with patch("src.soul.wake_word.detector.config") as mock_config:
                with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                    mock_config.WAKE_WORD_COOLDOWN = 2.0
                    mock_config.WAKE_WORD_PATTERNS = ["luna"]
                    mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])
                    mock_config.VAD_CONFIG = {"MODE": 2}

                    from src.soul.wake_word import WakeWordDetector

                    detector = WakeWordDetector()
                    detector.load_model(whisper_model=MagicMock())

                    assert detector.is_loaded is True


class TestWakeWordDetectorDetect:
    def test_returns_false_if_not_loaded(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                detected, text = detector.detect(b"\x00" * 1024)

                assert detected is False
                assert text is None

    def test_respects_cooldown(self):
        import sys

        mock_vad = MagicMock()
        with patch.dict(sys.modules, {"webrtcvad": mock_vad}):
            with patch("src.soul.wake_word.detector.config") as mock_config:
                with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                    mock_config.WAKE_WORD_COOLDOWN = 10.0
                    mock_config.WAKE_WORD_PATTERNS = ["luna"]
                    mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])
                    mock_config.VAD_CONFIG = {"MODE": 2}

                    from src.soul.wake_word import WakeWordDetector

                    detector = WakeWordDetector()
                    detector.load_model(whisper_model=MagicMock())
                    detector._last_detection_time = time.time()

                    detected, text = detector.detect(b"\x00" * 1024)

                    assert detected is False


class TestWakeWordDetectorNormalize:
    def test_removes_accents(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                result = detector._normalize("Olá Éris")

                assert "á" not in result
                assert "é" not in result

    def test_lowercases(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                result = detector._normalize("LUNA")

                assert result == "luna"


class TestWakeWordDetectorMatchesPattern:
    def test_matches_exact(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                result = detector._matches_pattern("luna")

                assert result is True

    def test_matches_with_context(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                result = detector._matches_pattern("ei luna voce esta ai")

                assert result is True

    def test_no_match(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                result = detector._matches_pattern("ola mundo")

                assert result is False


class TestWakeWordDetectorGetGreeting:
    def test_returns_greeting(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                greeting = detector.get_greeting()

                assert greeting in detector.GREETING_RESPONSES

    def test_cycles_through_greetings(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()

                g1 = detector.get_greeting()
                g2 = detector.get_greeting()

                assert g1 != g2 or len(detector.GREETING_RESPONSES) == 1


class TestWakeWordDetectorReset:
    def test_clears_buffer(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordDetector

                detector = WakeWordDetector()
                detector._audio_buffer = [1.0, 2.0, 3.0]

                detector.reset()

                assert detector._audio_buffer == []


class TestWakeWordThreadInit:
    def test_creates_instance(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordThread

                manager = MagicMock()
                shutdown_event = Event()

                thread = WakeWordThread(
                    threading_manager=manager, on_wake=MagicMock(), shutdown_event=shutdown_event, sample_rate=16000
                )

                assert thread.manager == manager
                assert thread.shutdown_event == shutdown_event
                assert thread._enabled is False


class TestWakeWordThreadEnableDisable:
    def test_enable(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordThread

                thread = WakeWordThread(
                    threading_manager=MagicMock(), on_wake=MagicMock(), shutdown_event=Event(), sample_rate=16000
                )

                thread.enable()

                assert thread._enabled is True
                assert thread._paused is False

    def test_disable(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordThread

                thread = WakeWordThread(
                    threading_manager=MagicMock(), on_wake=MagicMock(), shutdown_event=Event(), sample_rate=16000
                )
                thread._enabled = True

                thread.disable()

                assert thread._enabled is False
                assert thread._paused is True


class TestWakeWordThreadToggle:
    def test_toggles_on(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordThread

                thread = WakeWordThread(
                    threading_manager=MagicMock(), on_wake=MagicMock(), shutdown_event=Event(), sample_rate=16000
                )

                result = thread.toggle()

                assert result is True

    def test_toggles_off(self):
        with patch("src.soul.wake_word.detector.config") as mock_config:
            with patch("src.soul.wake_word.detector.get_active_entity", return_value="luna"):
                mock_config.WAKE_WORD_COOLDOWN = 2.0
                mock_config.WAKE_WORD_PATTERNS = ["luna"]
                mock_config.get_wake_word_patterns = MagicMock(return_value=["luna"])

                from src.soul.wake_word import WakeWordThread

                thread = WakeWordThread(
                    threading_manager=MagicMock(), on_wake=MagicMock(), shutdown_event=Event(), sample_rate=16000
                )
                thread._enabled = True

                result = thread.toggle()

                assert result is False
