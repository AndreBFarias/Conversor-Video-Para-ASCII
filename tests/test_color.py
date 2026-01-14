import pytest
import numpy as np
from src.core.utils.color import rgb_to_ansi256, rgb_to_ansi256_vectorized


class TestRgbToAnsi256:

    def test_black_returns_16(self):
        assert rgb_to_ansi256(0, 0, 0) == 16

    def test_white_returns_231(self):
        assert rgb_to_ansi256(255, 255, 255) == 231

    def test_gray_returns_grayscale_range(self):
        result = rgb_to_ansi256(128, 128, 128)
        assert 232 <= result <= 255

    def test_pure_red(self):
        result = rgb_to_ansi256(255, 0, 0)
        assert result == 16 + (36 * 5) + (6 * 0) + 0

    def test_pure_green(self):
        result = rgb_to_ansi256(0, 255, 0)
        assert result == 16 + (36 * 0) + (6 * 5) + 0

    def test_pure_blue(self):
        result = rgb_to_ansi256(0, 0, 255)
        assert result == 16 + (36 * 0) + (6 * 0) + 5

    def test_near_black_gray(self):
        result = rgb_to_ansi256(5, 5, 5)
        assert result == 16

    def test_near_white_gray(self):
        result = rgb_to_ansi256(250, 250, 250)
        assert result == 231


class TestRgbToAnsi256Vectorized:

    def test_output_shape_matches_input(self, sample_color_frame):
        result = rgb_to_ansi256_vectorized(sample_color_frame)
        assert result.shape == sample_color_frame.shape[:2]

    def test_black_frame_returns_16(self):
        frame = np.zeros((5, 5, 3), dtype=np.uint8)
        result = rgb_to_ansi256_vectorized(frame)
        assert np.all(result == 16)

    def test_white_frame_returns_231(self):
        frame = np.full((5, 5, 3), 255, dtype=np.uint8)
        result = rgb_to_ansi256_vectorized(frame)
        assert np.all(result == 231)

    def test_mixed_colors(self):
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        frame[0, 0] = [255, 0, 0]
        frame[0, 1] = [0, 255, 0]
        frame[1, 0] = [0, 0, 255]
        frame[1, 1] = [128, 128, 128]
        result = rgb_to_ansi256_vectorized(frame)
        assert result[0, 0] == 16 + 5
        assert result[0, 1] == 16 + 30
        assert result[1, 0] == 16 + 180

    def test_grayscale_detection(self):
        frame = np.zeros((3, 3, 3), dtype=np.uint8)
        frame[0, 0] = [100, 100, 100]
        frame[1, 1] = [200, 200, 200]
        frame[2, 2] = [50, 50, 50]
        result = rgb_to_ansi256_vectorized(frame)
        assert 232 <= result[0, 0] <= 255
        assert 232 <= result[1, 1] <= 255
        assert 232 <= result[2, 2] <= 255
