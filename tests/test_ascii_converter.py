import pytest
import numpy as np
from src.core.utils.ascii_converter import (
    converter_frame_para_ascii,
    COLOR_SEPARATOR,
    LUMINANCE_RAMP_DEFAULT
)


class TestConverterFrameParaAscii:

    def test_output_is_string(
        self,
        sample_gray_frame,
        sample_color_frame,
        sample_mask,
        sample_magnitude_frame,
        sample_angle_frame
    ):
        result = converter_frame_para_ascii(
            sample_gray_frame,
            sample_color_frame,
            sample_mask,
            sample_magnitude_frame,
            sample_angle_frame,
            sobel_threshold=50,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT
        )
        assert isinstance(result, str)

    def test_output_has_correct_line_count(
        self,
        sample_gray_frame,
        sample_color_frame,
        sample_mask,
        sample_magnitude_frame,
        sample_angle_frame
    ):
        result = converter_frame_para_ascii(
            sample_gray_frame,
            sample_color_frame,
            sample_mask,
            sample_magnitude_frame,
            sample_angle_frame,
            sobel_threshold=50,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT
        )
        lines = result.split('\n')
        assert len(lines) == sample_gray_frame.shape[0]

    def test_masked_areas_are_spaces(self):
        gray = np.full((5, 5), 128, dtype=np.uint8)
        color = np.full((5, 5, 3), 128, dtype=np.uint8)
        mask = np.full((5, 5), 255, dtype=np.uint8)
        magnitude = np.zeros((5, 5), dtype=np.uint8)
        angle = np.zeros((5, 5), dtype=np.float32)
        result = converter_frame_para_ascii(
            gray, color, mask, magnitude, angle,
            sobel_threshold=50,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT
        )
        for line in result.split('\n'):
            parts = line.split(COLOR_SEPARATOR)
            chars = [parts[i] for i in range(0, len(parts)-1, 2) if parts[i]]
            for char in chars:
                assert char == ' '

    def test_terminal_format_has_ansi_codes(
        self,
        sample_gray_frame,
        sample_color_frame,
        sample_mask,
        sample_magnitude_frame,
        sample_angle_frame
    ):
        result = converter_frame_para_ascii(
            sample_gray_frame,
            sample_color_frame,
            sample_mask,
            sample_magnitude_frame,
            sample_angle_frame,
            sobel_threshold=50,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT,
            output_format="terminal"
        )
        assert '\033[38;5;' in result
        assert result.endswith('\033[0m')

    def test_file_format_has_color_separator(
        self,
        sample_gray_frame,
        sample_color_frame,
        sample_mask,
        sample_magnitude_frame,
        sample_angle_frame
    ):
        result = converter_frame_para_ascii(
            sample_gray_frame,
            sample_color_frame,
            sample_mask,
            sample_magnitude_frame,
            sample_angle_frame,
            sobel_threshold=50,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT,
            output_format="file"
        )
        assert COLOR_SEPARATOR in result

    def test_custom_luminance_ramp(
        self,
        sample_gray_frame,
        sample_color_frame,
        sample_mask,
        sample_magnitude_frame,
        sample_angle_frame
    ):
        custom_ramp = "@#$%"
        result = converter_frame_para_ascii(
            sample_gray_frame,
            sample_color_frame,
            sample_mask,
            sample_magnitude_frame,
            sample_angle_frame,
            sobel_threshold=50,
            luminance_ramp=custom_ramp
        )
        assert isinstance(result, str)

    def test_high_sobel_threshold_no_edges(self):
        gray = np.full((5, 5), 128, dtype=np.uint8)
        color = np.full((5, 5, 3), 128, dtype=np.uint8)
        mask = np.zeros((5, 5), dtype=np.uint8)
        magnitude = np.full((5, 5), 50, dtype=np.uint8)
        angle = np.zeros((5, 5), dtype=np.float32)
        result = converter_frame_para_ascii(
            gray, color, mask, magnitude, angle,
            sobel_threshold=100,
            luminance_ramp=LUMINANCE_RAMP_DEFAULT
        )
        assert '/' not in result
        assert '|' not in result
        assert '\\' not in result
        assert '-' not in result


class TestColorSeparator:

    def test_color_separator_is_defined(self):
        assert COLOR_SEPARATOR is not None
        assert len(COLOR_SEPARATOR) == 1


class TestLuminanceRamp:

    def test_default_ramp_has_characters(self):
        assert len(LUMINANCE_RAMP_DEFAULT) > 0

    def test_default_ramp_ends_with_space(self):
        assert LUMINANCE_RAMP_DEFAULT[-1] == ' '

    def test_default_ramp_starts_with_dense_char(self):
        assert LUMINANCE_RAMP_DEFAULT[0] == '$'
