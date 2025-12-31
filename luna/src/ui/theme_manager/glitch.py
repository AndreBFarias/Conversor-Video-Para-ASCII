from __future__ import annotations

import logging

from src.core.entity_loader import EntityLoader

from .utils import hex_to_rgb, lighten, rgb_to_hex

logger = logging.getLogger(__name__)


def generate_glitch_palette_from_theme(theme: dict) -> dict:
    primary = theme.get("primary_color", "#bd93f9")
    secondary = theme.get("secondary_color", "#ff79c6")
    accent = theme.get("accent_color", "#50fa7b")
    background = theme.get("background", "#282a36")
    glow = theme.get("glow_color", primary)
    text_primary = theme.get("text_primary", "#f8f8f2")
    text_secondary = theme.get("text_secondary", "#6272a4")

    tv_static_config = theme.get("tv_static", {})

    if tv_static_config.get("base"):
        tv_base = tv_static_config["base"]
    else:
        tv_base = [lighten(background, 15), lighten(background, 25), lighten(background, 35), lighten(background, 45)]

    tv_accent = tv_static_config.get("accent", glow)
    tv_secondary = tv_static_config.get("secondary", text_secondary)

    return {
        "tv_base": tv_base,
        "tv_accent": tv_accent,
        "tv_secondary": tv_secondary,
        "text_primary": text_primary,
        "text_secondary": text_secondary,
        "glitch_primary": primary,
        "glitch_secondary": secondary,
        "glitch_accent": accent,
    }


def update_glitch_colors_for_entity(entity_id: str) -> None:
    import config

    try:
        loader = EntityLoader(entity_id)
        theme = loader.get_color_theme()

        if not theme:
            logger.warning(f"Tema nao encontrado para {entity_id}, mantendo GLITCH_COLORS atual")
            return

        glitch_palette = generate_glitch_palette_from_theme(theme)
        config.GLITCH_COLORS = glitch_palette

        logger.info(f"GLITCH_COLORS atualizado para entidade {entity_id}")
    except Exception as e:
        logger.error(f"Erro ao atualizar GLITCH_COLORS: {e}")
