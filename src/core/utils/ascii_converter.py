import numpy as np
from .color import rgb_to_ansi256, rgb_to_ansi256_vectorized

COLOR_SEPARATOR = "§"
LUMINANCE_RAMP_DEFAULT = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "


def converter_frame_para_ascii(
    gray_frame: np.ndarray,
    color_frame: np.ndarray,
    mask: np.ndarray,
    magnitude_frame: np.ndarray,
    angle_frame: np.ndarray,
    sobel_threshold: int,
    luminance_ramp: str,
    output_format: str = "file"
) -> str:
    height, width = gray_frame.shape
    ramp_len = len(luminance_ramp)
    ramp_array = np.array(list(luminance_ramp))

    lum_indices = ((gray_frame / 255) * (ramp_len - 1)).astype(np.int32)
    chars = ramp_array[lum_indices].copy()

    angle_degrees = angle_frame * (180 / np.pi)
    angle_degrees = (angle_degrees + 180) % 180

    is_edge = magnitude_frame > sobel_threshold

    slash_mask = is_edge & (((angle_degrees >= 22.5) & (angle_degrees < 67.5)) |
                            ((angle_degrees >= 157.5) & (angle_degrees < 202.5)))
    pipe_mask = is_edge & (((angle_degrees >= 67.5) & (angle_degrees < 112.5)) |
                           ((angle_degrees >= 247.5) & (angle_degrees < 292.5)))
    backslash_mask = is_edge & (((angle_degrees >= 112.5) & (angle_degrees < 157.5)) |
                                ((angle_degrees >= 292.5) & (angle_degrees < 337.5)))
    dash_mask = is_edge & ~(slash_mask | pipe_mask | backslash_mask)

    chars[slash_mask] = '/'
    chars[pipe_mask] = '|'
    chars[backslash_mask] = '\\'
    chars[dash_mask] = '-'

    ansi_codes = rgb_to_ansi256_vectorized(color_frame)

    is_masked = mask > 127
    chars[is_masked] = ' '
    ansi_codes[is_masked] = 232

    if output_format == "file":
        lines = []
        for y in range(height):
            row_chars = chars[y]
            row_codes = ansi_codes[y]
            line = COLOR_SEPARATOR.join(
                f"{c}{COLOR_SEPARATOR}{code}" for c, code in zip(row_chars, row_codes)
            ) + COLOR_SEPARATOR
            lines.append(line)
        return "\n".join(lines)
    else:
        lines = []
        for y in range(height):
            row_chars = chars[y]
            row_codes = ansi_codes[y]
            line = "".join(f"\033[38;5;{code}m{c}" for c, code in zip(row_chars, row_codes))
            lines.append(line)
        return "\n".join(lines) + "\033[0m"
