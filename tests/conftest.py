import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_gray_frame():
    frame = np.zeros((10, 10), dtype=np.uint8)
    frame[0:5, :] = 255
    frame[5:10, :] = 128
    return frame


@pytest.fixture
def sample_color_frame():
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    frame[0:5, :] = [255, 0, 0]
    frame[5:10, :] = [0, 255, 0]
    return frame


@pytest.fixture
def sample_mask():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[0:3, 0:3] = 255
    return mask


@pytest.fixture
def sample_magnitude_frame():
    return np.random.randint(0, 255, (10, 10), dtype=np.uint8)


@pytest.fixture
def sample_angle_frame():
    return np.random.uniform(0, np.pi, (10, 10)).astype(np.float32)
