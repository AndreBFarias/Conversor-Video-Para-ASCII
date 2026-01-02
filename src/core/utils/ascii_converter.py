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

    brightness = gray_frame.astype(np.int32)
    edge_boost = (magnitude_frame > sobel_threshold).astype(np.int32) * 100
    brightness = np.clip(brightness + edge_boost, 0, 255)

    char_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
    chars = ramp_array[char_indices]

    ansi_codes = rgb_to_ansi256_vectorized(color_frame)

    is_masked = mask == 255
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
