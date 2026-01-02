import numpy as np


def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return 232 + int(((r - 8) / 247) * 23)
    ansi_r = int(r / 255 * 5)
    ansi_g = int(g / 255 * 5)
    ansi_b = int(b / 255 * 5)
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b


def rgb_to_ansi256_vectorized(color_frame: np.ndarray) -> np.ndarray:
    b = color_frame[:, :, 0].astype(np.int32)
    g = color_frame[:, :, 1].astype(np.int32)
    r = color_frame[:, :, 2].astype(np.int32)

    ansi_r = (r * 5) // 255
    ansi_g = (g * 5) // 255
    ansi_b = (b * 5) // 255

    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b
