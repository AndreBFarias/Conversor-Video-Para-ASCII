import logging

logger = logging.getLogger(__name__)

_color_cache: dict | None = None
_tv_static_cache: dict | None = None


def get_ui_colors() -> dict:
    global _color_cache
    if _color_cache is not None:
        return _color_cache

    try:
        from src.core.entity_loader import get_active_loader

        loader = get_active_loader()
        theme = loader.get_full_color_theme()

        _color_cache = {
            "primary": theme.get("primary_color", "#bd93f9"),
            "secondary": theme.get("secondary_color", "#ff79c6"),
            "accent": theme.get("accent_color", "#50fa7b"),
            "background": theme.get("background", "#282a36"),
            "background_alt": theme.get("background_alt", "#1e1f29"),
            "background_input": theme.get("background_input", "#44475a"),
            "background_panel": theme.get("background_panel", "#2d2f3d"),
            "glow": theme.get("glow_color", "#bd93f9"),
            "text_primary": theme.get("text_primary", "#f8f8f2"),
            "text_secondary": theme.get("text_secondary", "#6272a4"),
            "text_user": theme.get("text_user", "#8be9fd"),
            "text_success": theme.get("text_success", "#50fa7b"),
            "text_error": theme.get("text_error", "#ff5555"),
        }

        logger.debug(f"Cache de cores UI carregado: {loader.entity_id}")
        return _color_cache

    except Exception as e:
        logger.warning(f"Erro ao carregar cores da entidade, usando fallback: {e}")
        return _get_fallback_colors()


def get_tv_static_colors() -> dict:
    global _tv_static_cache
    if _tv_static_cache is not None:
        return _tv_static_cache

    try:
        from src.core.entity_loader import get_active_loader

        loader = get_active_loader()
        theme = loader.get_full_color_theme()

        tv_static = theme.get("tv_static", {})
        _tv_static_cache = {
            "base": tv_static.get("base", ["#333333", "#444444", "#555555", "#666666"]),
            "accent": tv_static.get("accent", theme.get("glow_color", "#bd93f9")),
            "secondary": tv_static.get("secondary", theme.get("secondary_color", "#ff79c6")),
        }

        logger.debug(f"Cache de cores TV static carregado: {loader.entity_id}")
        return _tv_static_cache

    except Exception as e:
        logger.warning(f"Erro ao carregar cores TV static, usando fallback: {e}")
        return {
            "base": ["#333333", "#444444", "#555555", "#666666"],
            "accent": "#bd93f9",
            "secondary": "#ff79c6",
        }


def get_glitch_colors() -> dict:
    colors = get_ui_colors()
    tv = get_tv_static_colors()

    return {
        "tv_base": tv["base"],
        "tv_accent": tv["accent"],
        "tv_secondary": tv["secondary"],
        "text_primary": colors["text_primary"],
        "text_secondary": colors["text_secondary"],
        "glitch_primary": colors["primary"],
        "glitch_secondary": colors["secondary"],
        "glitch_accent": colors["accent"],
    }


def invalidate_color_cache() -> None:
    global _color_cache, _tv_static_cache
    _color_cache = None
    _tv_static_cache = None
    logger.info("Cache de cores invalidado")


def _get_fallback_colors() -> dict:
    return {
        "primary": "#bd93f9",
        "secondary": "#ff79c6",
        "accent": "#50fa7b",
        "background": "#282a36",
        "background_alt": "#1e1f29",
        "background_input": "#44475a",
        "background_panel": "#2d2f3d",
        "glow": "#bd93f9",
        "text_primary": "#f8f8f2",
        "text_secondary": "#6272a4",
        "text_user": "#8be9fd",
        "text_success": "#50fa7b",
        "text_error": "#ff5555",
    }


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}"


def lighten_color(hex_color: str, amount: int = 20) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r + amount, g + amount, b + amount)


def darken_color(hex_color: str, amount: int = 20) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r - amount, g - amount, b - amount)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"
