import time

import numpy as np


class TestAudioVisualizerConstants:
    def test_gradient_colors_exist(self):
        from src.ui.audio_visualizer import AudioVisualizer

        assert len(AudioVisualizer.GRADIENT_COLORS) > 0

    def test_gradient_colors_are_tuples(self):
        from src.ui.audio_visualizer import AudioVisualizer

        for color in AudioVisualizer.GRADIENT_COLORS:
            assert isinstance(color, tuple)
            assert len(color) == 3

    def test_gradient_colors_valid_rgb(self):
        from src.ui.audio_visualizer import AudioVisualizer

        for r, g, b in AudioVisualizer.GRADIENT_COLORS:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_bg_color_exists(self):
        from src.ui.audio_visualizer import AudioVisualizer

        assert AudioVisualizer.BG_COLOR == "#282a36"


class TestAudioVisualizerInit:
    def test_creates_with_defaults(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()

        assert viz.num_bands == 8
        assert len(viz.smoothed_energies) == 8
        assert viz.smoothed_rms == 0.0
        assert viz.peak_rms == 0.0
        assert viz.time_offset == 0.0
        assert viz._busy is False

    def test_smoothed_energies_are_zero(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()

        assert all(e == 0.0 for e in viz.smoothed_energies)

    def test_last_update_is_recent(self):
        from src.ui.audio_visualizer import AudioVisualizer

        before = time.time()
        viz = AudioVisualizer()
        after = time.time()

        assert before <= viz.last_update <= after


class TestAudioVisualizerUpdateAudio:
    def test_skips_when_busy(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        viz._busy = True
        original_rms = viz.smoothed_rms

        viz.update_audio(np.array([1, 2, 3]), 44100)

        assert viz.smoothed_rms == original_rms

    def test_skips_none_audio(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        original_rms = viz.smoothed_rms

        viz.update_audio(None, 44100)

        assert viz._busy is False

    def test_skips_short_audio(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        original_rms = viz.smoothed_rms

        viz.update_audio(np.array([1, 2, 3]), 44100)

        assert viz._busy is False

    def test_processes_valid_audio(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        audio = np.random.randint(-32768, 32767, size=256, dtype=np.int16)

        viz.update_audio(audio, 44100)

        assert viz._busy is False

    def test_updates_peak_rms(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        audio = np.random.randint(-32768, 32767, size=256, dtype=np.int16)

        viz.update_audio(audio, 44100)

        assert viz.peak_rms >= 0

    def test_updates_smoothed_rms(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        audio = np.random.randint(-32768, 32767, size=1024, dtype=np.int16)

        viz.update_audio(audio, 44100)

        assert viz.smoothed_rms >= 0


class TestAudioVisualizerRateLimiting:
    def test_skips_rapid_updates(self):
        from src.ui.audio_visualizer import AudioVisualizer

        viz = AudioVisualizer()
        audio = np.random.randint(-32768, 32767, size=256, dtype=np.int16)

        viz.update_audio(audio, 44100)
        first_update_time = viz.last_update

        viz.update_audio(audio, 44100)

        assert viz.last_update == first_update_time

    def test_allows_update_after_interval(self):
        from src.ui.audio_visualizer import MIN_FRAME_INTERVAL, AudioVisualizer

        viz = AudioVisualizer()
        audio = np.random.randint(-32768, 32767, size=256, dtype=np.int16)

        viz.last_update = time.time() - MIN_FRAME_INTERVAL - 0.01

        viz.update_audio(audio, 44100)

        assert viz._busy is False

    def test_min_frame_interval_is_reasonable(self):
        from src.ui.audio_visualizer import MIN_FRAME_INTERVAL, TARGET_FPS

        assert MIN_FRAME_INTERVAL == 1.0 / TARGET_FPS
        assert 0.01 <= MIN_FRAME_INTERVAL <= 0.1

    def test_target_fps_from_config(self):
        import config

        from src.ui.audio_visualizer import TARGET_FPS

        expected_fps = config.UI_CONFIG.get("VIZ_FPS", 24)
        assert TARGET_FPS == expected_fps


class TestAudioVisualizerConfig:
    def test_viz_fps_in_config(self):
        import config

        assert "VIZ_FPS" in config.UI_CONFIG

    def test_viz_fps_is_int(self):
        import config

        assert isinstance(config.UI_CONFIG["VIZ_FPS"], int)

    def test_viz_fps_reasonable_range(self):
        import config

        fps = config.UI_CONFIG["VIZ_FPS"]
        assert 10 <= fps <= 60
