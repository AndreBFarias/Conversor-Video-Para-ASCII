from __future__ import annotations

import logging
import random

from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

import config
from src.ui.banner.helpers import (
    BLOCK_CHARS,
    STATIC_CHARS,
    create_entity_banner,
    get_entity_banner_ascii,
    get_entity_palette,
    get_gradient_color,
)
from src.ui.colors import get_ui_colors

logger = logging.getLogger(__name__)


class BannerGlitchWidget(Static):
    def __init__(self, ascii_lines: list[str] = None, primary_color: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.ascii_lines = ascii_lines or get_entity_banner_ascii()
        colors = get_ui_colors()
        self.primary_color = primary_color or get_entity_palette().get("primary", colors["primary"])
        self._glitch_timer: Timer | None = None
        self._is_glitching = False
        self._idle_timer: Timer | None = None
        self._glitch_count = 0
        self._max_glitch_frames = 5

    def on_mount(self) -> None:
        self._render_normal()
        interval = config.GLITCH_CONFIG.get("EFFECT_INTERVAL", 0.15)
        self._idle_timer = self.set_interval(interval, self._idle_tick)

    def _idle_tick(self) -> None:
        if "hidden" in self.classes:
            return
        trigger = config.GLITCH_CONFIG.get("BANNER_TRIGGER", 0.94)
        if not self._is_glitching and random.random() > trigger:
            self._trigger_glitch_burst()

    def _trigger_glitch_burst(self) -> None:
        if self._is_glitching:
            return

        self._is_glitching = True
        self._glitch_count = 0
        self._max_glitch_frames = random.randint(3, 7)
        effect_duration = config.GLITCH_CONFIG.get("EFFECT_DURATION_AVG", 0.3)
        frame_interval = effect_duration / self._max_glitch_frames
        self._glitch_timer = self.set_interval(max(0.03, frame_interval), self._glitch_frame)

    def _glitch_frame(self) -> None:
        if "hidden" in self.classes:
            if self._glitch_timer:
                self._glitch_timer.stop()
                self._glitch_timer = None
            self._is_glitching = False
            return

        self._glitch_count += 1
        intensity = random.uniform(0.2, 0.5)
        static_density = random.uniform(0.02, 0.06)
        self._render_glitched(intensity, static_density)

        if self._glitch_count >= self._max_glitch_frames:
            if self._glitch_timer:
                self._glitch_timer.stop()
                self._glitch_timer = None
            self._is_glitching = False
            self._render_normal()

    def _render_normal(self) -> None:
        text = Text()
        total_lines = len(self.ascii_lines)

        for i, line in enumerate(self.ascii_lines):
            color = get_gradient_color(i, total_lines)

            for char in line:
                if char in "█▄▀▐▌▓▒░":
                    text.append(char, style=Style(color=color, bold=True))
                elif char.strip():
                    text.append(char, style=Style(color=color))
                else:
                    text.append(char)

            if i < total_lines - 1:
                text.append("\n")

        self.update(text)

    def _get_glitch_colors(self) -> tuple:
        palette = config.GLITCH_COLORS
        entity_palette = get_entity_palette()
        colors = get_ui_colors()
        accent = palette.get("tv_accent", entity_palette.get("primary", colors["primary"]))
        primary = palette.get("text_primary", entity_palette.get("secondary", colors["secondary"]))
        secondary = palette.get("text_secondary", entity_palette.get("accent", colors["accent"]))
        return accent, primary, secondary

    def _render_glitched(self, intensity: float, static_density: float) -> None:
        text = Text()
        max_width = max(len(line) for line in self.ascii_lines)
        total_lines = len(self.ascii_lines)
        accent, primary, secondary = self._get_glitch_colors()

        if random.random() > 0.6:
            scanline_char = random.choice(["─", "━", "╌", "┄", "═"])
            text.append(scanline_char * max_width, style=Style(color=accent, dim=True))
            text.append("\n")

        if static_density > 0 and random.random() > 0.7:
            for _ in range(max_width):
                if random.random() < static_density:
                    char = random.choice(STATIC_CHARS[:4])
                    text.append(char, style=Style(color=accent, dim=True))
                else:
                    text.append(" ")
            text.append("\n")

        for i, line in enumerate(self.ascii_lines):
            base_color = get_gradient_color(i, total_lines)

            for char in line:
                if char in "█▄▀▐▌▓▒░" and random.random() < intensity:
                    glitch_char = random.choice(BLOCK_CHARS)
                    colors = [accent, secondary, primary]
                    style = Style(color=random.choice(colors), dim=random.random() > 0.5)
                    text.append(glitch_char, style=style)
                elif char.strip() and random.random() < intensity * 0.3:
                    colors = [secondary, primary, accent]
                    style = Style(color=random.choice(colors))
                    text.append(char, style=style)
                elif char in "█▄▀▐▌▓▒░":
                    text.append(char, style=Style(color=base_color, bold=True))
                elif char.strip():
                    text.append(char, style=Style(color=base_color))
                else:
                    text.append(char)

            if i < total_lines - 1:
                text.append("\n")

        self.update(text)

    def reload_for_entity(self, entity_id: str) -> None:
        from src.core.entity_loader import EntityLoader, reload_active_loader

        reload_active_loader()
        loader = EntityLoader(entity_id)
        self.ascii_lines = loader.get_banner_ascii()
        colors = get_ui_colors()
        self.primary_color = get_entity_palette().get("primary", colors["primary"])
        self._render_normal()
        logger.info(f"Banner recarregado para entidade: {entity_id}")

    def force_glitch(self, duration_frames: int = 5) -> None:
        self._is_glitching = True
        self._glitch_count = 0
        self._max_glitch_frames = duration_frames

        if self._glitch_timer:
            self._glitch_timer.stop()

        self._glitch_timer = self.set_interval(0.05, self._glitch_frame)


class Banner(Static):
    def on_mount(self) -> None:
        self.update(create_entity_banner())
