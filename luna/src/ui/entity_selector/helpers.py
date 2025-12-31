import logging

from src.core.entity_loader import EntityLoader, get_active_entity

logger = logging.getLogger(__name__)


def _get_current_theme_colors() -> dict:
    try:
        entity_id = get_active_entity()
        loader = EntityLoader(entity_id)
        return loader.get_color_theme()
    except Exception:
        return {
            "primary_color": "#bd93f9",
            "secondary_color": "#ff79c6",
            "accent_color": "#50fa7b",
            "background": "#282a36",
            "text_primary": "#f8f8f2",
            "text_secondary": "#6272a4",
        }


def _get_entity_theme_colors(entity_id: str) -> dict:
    try:
        loader = EntityLoader(entity_id)
        return loader.get_color_theme()
    except Exception:
        return _get_current_theme_colors()
