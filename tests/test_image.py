import pytest
import numpy as np
import cv2
from src.core.utils.image import sharpen_frame, apply_morphological_refinement


class TestSharpenFrame:

    def test_zero_sharpen_returns_original(self):
        frame = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=0)
        assert np.array_equal(result, frame)

    def test_negative_sharpen_returns_original(self):
        frame = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=-1.0)
        assert np.array_equal(result, frame)

    def test_positive_sharpen_modifies_frame(self):
        frame = np.random.randint(50, 200, (50, 50, 3), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=0.5)
        assert not np.array_equal(result, frame)

    def test_output_shape_matches_input(self):
        frame = np.random.randint(0, 256, (100, 80, 3), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=1.0)
        assert result.shape == frame.shape

    def test_output_dtype_matches_input(self):
        frame = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=0.5)
        assert result.dtype == frame.dtype

    def test_grayscale_frame(self):
        frame = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
        result = sharpen_frame(frame, sharpen_amount=0.5)
        assert result.shape == frame.shape


class TestApplyMorphologicalRefinement:

    def test_no_erosion_no_dilation(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[20:30, 20:30] = 255
        result = apply_morphological_refinement(mask, erode_size=0, dilate_size=0)
        assert np.array_equal(result, mask)

    def test_erosion_shrinks_mask(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[10:40, 10:40] = 255
        original_white = np.sum(mask == 255)
        result = apply_morphological_refinement(mask, erode_size=3, dilate_size=0)
        result_white = np.sum(result == 255)
        assert result_white < original_white

    def test_dilation_expands_mask(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[20:30, 20:30] = 255
        original_white = np.sum(mask == 255)
        result = apply_morphological_refinement(mask, erode_size=0, dilate_size=3)
        result_white = np.sum(result == 255)
        assert result_white > original_white

    def test_output_shape_matches_input(self):
        mask = np.random.randint(0, 2, (100, 80), dtype=np.uint8) * 255
        result = apply_morphological_refinement(mask, erode_size=2, dilate_size=2)
        assert result.shape == mask.shape

    def test_output_is_binary(self):
        mask = np.random.randint(0, 2, (50, 50), dtype=np.uint8) * 255
        result = apply_morphological_refinement(mask, erode_size=2, dilate_size=2)
        unique_values = np.unique(result)
        assert all(v in [0, 255] for v in unique_values)

    def test_empty_mask_stays_empty(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        result = apply_morphological_refinement(mask, erode_size=2, dilate_size=2)
        assert np.sum(result) == 0
