import random

from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Button

import config
from src.ui.colors import get_ui_colors

GLITCH_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#@$%&*!?"


class GlitchButton(Button):
    can_focus = True

    def __init__(self, label: str, **kwargs):
        super().__init__(label, **kwargs)
        self._original_label = label
        self._glitch_timer: Timer | None = None
        self._in_glitch = False
        self._glitch_frames = 0
        self._is_active = False
        self._click_glitch_remaining = 0

    def on_mount(self) -> None:
        interval = config.GLITCH_CONFIG.get("EFFECT_INTERVAL", 0.15) * 0.8
        self._glitch_timer = self.set_interval(interval, self._glitch_tick)

    def on_button_pressed(self, event) -> None:
        self._click_glitch_remaining = 8
        self._in_glitch = True
        self._glitch_frames = 3

    def watch_has_focus(self, has_focus: bool) -> None:
        if has_focus:
            self._is_active = True
            self.add_class("focused")
        else:
            self._is_active = False
            self.remove_class("focused")
            if not self._click_glitch_remaining:
                self._render_normal()

    def _should_glitch(self) -> bool:
        if self._click_glitch_remaining > 0:
            return True
        if self.has_class("-active"):
            return True
        if self._is_active:
            return True
        return False

    def _glitch_tick(self) -> None:
        if self._click_glitch_remaining > 0:
            self._click_glitch_remaining -= 1

        if not self._should_glitch():
            if self._in_glitch:
                self._in_glitch = False
                self._render_normal()
            return

        if self._in_glitch:
            self._glitch_frames -= 1
            if self._glitch_frames <= 0:
                self._in_glitch = False
                self._render_normal()
            else:
                self._render_glitched()
            return

        if self._is_active:
            trigger = 0.6
        else:
            trigger = config.GLITCH_CONFIG.get("BUTTON_TRIGGER", 0.92)

        if random.random() > trigger:
            self._in_glitch = True
            self._glitch_frames = random.randint(2, 5) if self._is_active else random.randint(2, 4)
            self._render_glitched()

    def _render_normal(self) -> None:
        self.label = self._original_label

    def _get_glitch_colors(self) -> list:
        palette = config.GLITCH_COLORS
        colors = get_ui_colors()
        accent = palette.get("tv_accent", colors["primary"])
        primary = palette.get("text_primary", colors["secondary"])
        secondary = palette.get("text_secondary", colors["text_user"])
        return [accent, primary, secondary]

    def _render_glitched(self) -> None:
        text = Text()
        glitch_count = random.randint(1, min(2, len(self._original_label)))
        if len(self._original_label) > 0:
            positions = random.sample(range(len(self._original_label)), min(glitch_count, len(self._original_label)))
        else:
            positions = []

        colors = self._get_glitch_colors()
        for i, char in enumerate(self._original_label):
            if i in positions and char != " ":
                glitch_char = random.choice(GLITCH_CHARS)
                style = Style(color=random.choice(colors))
                text.append(glitch_char, style=style)
            else:
                text.append(char)

        self.label = text

    def set_active(self, active: bool) -> None:
        self._is_active = active
        if active:
            self.add_class("-active")
        else:
            self.remove_class("-active")
            self._render_normal()


# "A vontade de poder e a essencia da vida."
# — Friedrich Nietzsche
