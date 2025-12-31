from __future__ import annotations

import asyncio
import logging
import random
from enum import Enum, auto

from rich.style import Style
from rich.text import Text

import config
from src.ui.banner.helpers import (
    STATIC_CHARS,
    create_entity_banner,
    get_entity_palette,
    get_gradient_color,
)
from src.ui.colors import get_tv_static_colors

logger = logging.getLogger(__name__)


class TVTarget(Enum):
    BANNER = auto()
    ASCII = auto()
    STATUS = auto()
    EMOTION = auto()
    ALL = auto()


class TVStaticEngine:
    def __init__(self, app):
        self.app = app
        self._cache_banner_lines: list[str] | None = None

    def _get_colors(self) -> tuple:
        palette = config.GLITCH_COLORS
        tv_colors = get_tv_static_colors()
        base = palette.get("tv_base", tv_colors["base"])
        accent = palette.get("tv_accent", tv_colors["accent"])
        secondary = palette.get("tv_secondary", tv_colors["secondary"])
        return base, accent, secondary

    def _get_widget_dims(self, widget_id: str) -> tuple:
        try:
            widget = self.app.query_one(f"#{widget_id}")
            w = max(widget.size.width, 80) if widget.size.width else 80
            h = widget.size.height if widget.size.height > 0 else 20
            return w, h
        except Exception as e:
            logger.debug(f"Erro ao obter dimensoes do widget {widget_id}: {e}")
            return 80, 20

    def _get_banner_lines(self) -> list[str]:
        if self._cache_banner_lines is None:
            self._cache_banner_lines = str(create_entity_banner()).split("\n")
        return self._cache_banner_lines

    def generate_static_text(self, width: int, height: int, density: float = 1.0) -> Text:
        base_colors, accent_color, secondary_color = self._get_colors()
        static_text = Text()

        for row in range(height):
            line_text = Text()
            for col in range(width):
                if random.random() < density:
                    char = random.choice(STATIC_CHARS)
                    color = random.choice(base_colors)
                    rand_val = random.random()
                    if rand_val < 0.06:
                        color = accent_color
                    elif rand_val < 0.12:
                        color = secondary_color
                    line_text.append(char, Style(color=color))
                else:
                    line_text.append(" ")
            static_text.append(line_text)
            if row < height - 1:
                static_text.append("\n")

        return static_text

    def generate_banner_with_static(self, width: int, height: int, density: float) -> Text:
        base_colors, accent_color, secondary_color = self._get_colors()
        banner_lines = self._get_banner_lines()
        banner_static = Text()

        for line_idx in range(height):
            line_text = Text()
            original_line = banner_lines[line_idx] if line_idx < len(banner_lines) else ""

            for char_idx in range(width):
                original_char = original_line[char_idx] if char_idx < len(original_line) else " "

                if random.random() < density:
                    char = random.choice(STATIC_CHARS)
                    color = random.choice(base_colors)
                    rand_val = random.random()
                    if rand_val < 0.06:
                        color = accent_color
                    elif rand_val < 0.12:
                        color = secondary_color
                    line_text.append(char, Style(color=color))
                else:
                    if original_char in "█▄▀▐▌▓▒░" or original_char.strip():
                        grad_color = get_gradient_color(line_idx, height)
                        line_text.append(original_char, Style(color=grad_color, bold=True))
                    else:
                        line_text.append(" ")

            banner_static.append(line_text)
            if line_idx < height - 1:
                banner_static.append("\n")

        return banner_static

    async def run(
        self,
        targets: set[TVTarget] = None,
        duration: float = 0.8,
        steps: int = 15,
        pattern: str = "pulse",
        restore_after: bool = True,
    ):
        if targets is None:
            targets = {TVTarget.ALL}

        if TVTarget.ALL in targets:
            targets = {TVTarget.BANNER, TVTarget.ASCII, TVTarget.STATUS, TVTarget.EMOTION}

        try:
            welcome_pane = self.app.query_one("#welcome-pane") if TVTarget.BANNER in targets else None
            ascii_pane = self.app.query_one("#ascii-pane") if TVTarget.ASCII in targets else None
            status_label = self.app.query_one("#status-label") if TVTarget.STATUS in targets else None
            emotion_label = self.app.query_one("#emotion-label") if TVTarget.EMOTION in targets else None
        except Exception as e:
            logger.warning(f"Widgets nao encontrados: {e}")
            return

        from src.ui.banner.widgets import BannerGlitchWidget

        is_glitch_widget = welcome_pane and isinstance(welcome_pane, BannerGlitchWidget)

        w_ascii, h_ascii = self._get_widget_dims("ascii-pane")
        w_banner, h_banner = self._get_widget_dims("welcome-pane")

        status_was_visible = False
        if status_label:
            status_was_visible = "status-visible" in status_label.classes
            status_label.remove_class("status-hidden")
            status_label.add_class("status-visible")

        status_msgs = ["[Sintonizando...]", "[Ajustando...]", "[Conectando...]", "[Buscando sinal...]"]

        for i in range(steps):
            density = self._calculate_density(i, steps, pattern)
            flicker = random.uniform(-0.04, 0.04)
            density = max(0.0, min(1.0, density + flicker))

            if welcome_pane and TVTarget.BANNER in targets:
                if not is_glitch_widget:
                    welcome_pane.update(self.generate_banner_with_static(w_banner, h_banner, density))
                elif density > 0.5:
                    welcome_pane.force_glitch(2)

            if ascii_pane and TVTarget.ASCII in targets:
                ascii_pane.update(self.generate_static_text(w_ascii, h_ascii, density))

            if status_label and TVTarget.STATUS in targets and density > 0.3:
                status_label.update(random.choice(status_msgs))

            if emotion_label and TVTarget.EMOTION in targets and density > 0.3:
                if not hasattr(emotion_label, "set_text"):
                    static_len = max(3, int(12 * density))
                    emotion_label.update(f"[{''.join(random.choices(STATIC_CHARS[:8], k=static_len))}]")

            await asyncio.sleep(duration / steps)

        if restore_after:
            if welcome_pane and not is_glitch_widget:
                welcome_pane.update(create_entity_banner())

            if status_label:
                if not status_was_visible:
                    status_label.update("")
                    status_label.add_class("status-hidden")
                    status_label.remove_class("status-visible")

    def _calculate_density(self, step: int, total: int, pattern: str) -> float:
        progress = step / total

        if pattern == "pulse":
            if progress < 0.25:
                return (progress / 0.25) ** 1.8
            elif progress < 0.75:
                return 1.0
            else:
                return 1.0 - ((progress - 0.75) / 0.25) ** 2.2

        elif pattern == "fade_in":
            return progress**1.5

        elif pattern == "fade_out":
            return 1.0 - (progress**1.5)

        elif pattern == "constant":
            return 1.0

        elif pattern == "quick_pulse":
            if progress < 0.3:
                return progress / 0.3
            elif progress < 0.7:
                return 1.0
            else:
                return 1.0 - ((progress - 0.7) / 0.3)

        return progress


_tv_engine: TVStaticEngine | None = None


def get_tv_engine(app) -> TVStaticEngine:
    global _tv_engine
    if _tv_engine is None or _tv_engine.app != app:
        _tv_engine = TVStaticEngine(app)
    return _tv_engine
