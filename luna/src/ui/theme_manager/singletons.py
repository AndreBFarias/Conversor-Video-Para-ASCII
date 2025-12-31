from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ThemeManager

_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    from .core import ThemeManager as TM

    global _theme_manager
    if _theme_manager is None:
        _theme_manager = TM()
    return _theme_manager


def reload_theme_for_entity(entity_id: str) -> ThemeManager:
    from .core import ThemeManager as TM

    global _theme_manager
    if _theme_manager is None:
        _theme_manager = TM(entity_id)
    else:
        _theme_manager.reload_for_entity(entity_id)
    return _theme_manager
