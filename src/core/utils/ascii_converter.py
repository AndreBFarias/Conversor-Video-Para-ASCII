import numpy as np
from .color import rgb_to_ansi256

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
    lines = []

    for y in range(height):
        line_parts = []
        for x in range(width):
            if mask[y, x] == 255:
                char = " "
                ansi_code = 232
            else:
                pixel_brightness = gray_frame[y, x]
                if magnitude_frame[y, x] > sobel_threshold:
                    pixel_brightness = min(255, pixel_brightness + 100)
                char_index = int((pixel_brightness / 255) * (len(luminance_ramp) - 1))
                char = luminance_ramp[char_index]
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)

            if output_format == "file":
                line_parts.append(f"{char}{COLOR_SEPARATOR}{ansi_code}{COLOR_SEPARATOR}")
            else:
                line_parts.append(f"\033[38;5;{ansi_code}m{char}")

        lines.append("".join(line_parts))

    result = "\n".join(lines)
    if output_format == "terminal":
        result += "\033[0m"

    return result
