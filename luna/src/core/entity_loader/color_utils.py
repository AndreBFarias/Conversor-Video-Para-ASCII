def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}"


def lighten_color(hex_color: str, amount: int) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r + amount, g + amount, b + amount)


def darken_color(hex_color: str, amount: int) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r - amount, g - amount, b - amount)


def generate_static_base(background: str) -> list:
    return [
        lighten_color(background, 20),
        lighten_color(background, 35),
        lighten_color(background, 50),
        lighten_color(background, 65),
    ]
