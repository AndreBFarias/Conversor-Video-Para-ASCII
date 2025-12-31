from __future__ import annotations

import logging

from rich.style import Style
from rich.text import Text

from src.core.entity_loader import EntityLoader, get_active_entity
from src.ui.colors import get_ui_colors

logger = logging.getLogger(__name__)

BLOCK_CHARS = "░▒▓█▄▀▐▌"
STATIC_CHARS = "░▒▓█▀▄▌▐│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌"
GLITCH_CHARS = "░▒▓█▀▄▐▌╔╗╚╝║═╬╣╠╩╦"


def get_entity_palette() -> dict:
    colors = get_ui_colors()
    return {
        "bg": colors["background"],
        "fg": colors["text_primary"],
        "comment": colors["text_secondary"],
        "primary": colors["primary"],
        "secondary": colors["secondary"],
        "accent": colors["accent"],
        "glow": colors["glow"],
    }


def get_default_banner() -> list[str]:
    return [
        " ▄█       ███    █▄  ███▄▄▄▄      ▄████████ ",
        "███       ███    ███ ███▀▀▀██▄   ███    ███ ",
        "███       ███    ███ ███   ███   ███    ███ ",
        "███       ███    ███ ███   ███   ███    ███ ",
        "███       ███    ███ ███   ███ ▀███████████ ",
        "███       ███    ███ ███   ███   ███    ███ ",
        "███▌    ▄ ███    ███ ███   ███   ███    ███ ",
        "█████▄▄██ ████████▀   ▀█   █▀    ███    █▀  ",
        "▀                                           ",
    ]


def get_default_gradient() -> list[str]:
    colors = get_ui_colors()
    try:
        entity_id = get_active_entity()
        loader = EntityLoader(entity_id)
        gradient = loader.get_gradient()
        if gradient:
            return gradient
    except Exception as e:
        logger.debug(f"Fallback para gradient default: {e}")
    return [
        colors["primary"],
        colors["secondary"],
        colors["text_secondary"],
    ]


def get_entity_banner_ascii() -> list[str]:
    try:
        entity_id = get_active_entity()
        loader = EntityLoader(entity_id)
        banner = loader.get_banner_ascii()
        if banner:
            return banner
    except Exception as e:
        logger.debug(f"Fallback para banner default: {e}")
    return get_default_banner()


def get_entity_gradient() -> list[str]:
    try:
        entity_id = get_active_entity()
        loader = EntityLoader(entity_id)
        gradient = loader.get_gradient()
        if gradient:
            return gradient
    except Exception as e:
        logger.debug(f"Fallback para gradient default: {e}")
    return get_default_gradient()


def get_gradient_color(line_index: int, total_lines: int, gradient: list[str] = None) -> str:
    if gradient is None:
        gradient = get_entity_gradient()
    if total_lines <= 1:
        return gradient[0] if gradient else get_default_gradient()[0]

    ratio = line_index / (total_lines - 1)
    idx = int(ratio * (len(gradient) - 1))
    return gradient[min(idx, len(gradient) - 1)]


def create_entity_banner() -> Text:
    banner_text = Text(justify="left")
    banner_lines = get_entity_banner_ascii()
    gradient = get_entity_gradient()
    total_lines = len(banner_lines)

    for i, line in enumerate(banner_lines):
        color = get_gradient_color(i, total_lines, gradient)

        for char in line:
            if char in "█▄▀▐▌▓▒░":
                banner_text.append(char, Style(color=color, bold=True))
            elif char.strip():
                banner_text.append(char, Style(color=color))
            else:
                banner_text.append(" ")

        if i < total_lines - 1:
            banner_text.append("\n")

    return banner_text


def create_entity_banner_glitched(glitch_intensity: float = 0.08) -> Text:
    import random

    banner_text = Text(justify="left")
    banner_lines = get_entity_banner_ascii()
    gradient = get_entity_gradient()
    total_lines = len(banner_lines)

    for i, line in enumerate(banner_lines):
        color = get_gradient_color(i, total_lines, gradient)

        for char in line:
            if random.random() < glitch_intensity and char.strip():
                glitch_char = random.choice(GLITCH_CHARS)
                glitch_color = random.choice(["#ff0055", "#00ff88", "#8855ff", color])
                banner_text.append(glitch_char, Style(color=glitch_color, bold=True))
            elif char in "█▄▀▐▌▓▒░":
                banner_text.append(char, Style(color=color, bold=True))
            elif char.strip():
                banner_text.append(char, Style(color=color))
            else:
                banner_text.append(" ")

        if i < total_lines - 1:
            banner_text.append("\n")

    return banner_text


def create_entity_banner_simple() -> Text:
    banner_text = Text(justify="left")
    luna_art = [
        "██╗     ██╗   ██╗███╗   ██╗ █████╗ ",
        "██║     ██║   ██║████╗  ██║██╔══██╗",
        "██║     ██║   ██║██╔██╗ ██║███████║",
        "██║  ██║██║   ██╗██║██╔═██║██║  ██║",
        "███████╗╚██████╔╝██║ █████║██║  ██║",
        "╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝",
    ]
    for line in luna_art:
        for char in line:
            if char != " ":
                banner_text.append(char, Style(color="#626ba5"))
            else:
                banner_text.append(" ")
        banner_text.append("\n")
    return banner_text
