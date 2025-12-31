import random
from collections.abc import Callable

from rich.style import Style
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

from src.core.entity_loader import EntityLoader, get_active_entity
from src.ui.colors import get_ui_colors

from .constants import GLITCH_CHARS_HEAVY, GLITCH_CHARS_LIGHT, GLITCH_CHARS_MEDIUM
from .helpers import get_entity_status_text


class StatusDecryptWidget(Static):
    def __init__(self, initial_text: str = None, on_complete: Callable | None = None, **kwargs):
        super().__init__(**kwargs)
        if initial_text is None:
            initial_text = get_entity_status_text()
        self.original_text = initial_text

        entity_id = get_active_entity()
        entity_loader = EntityLoader(entity_id)
        theme = entity_loader.get_color_theme()
        self.color = theme.get("primary_color", "#bd93f9")
        self.glow_color = theme.get("glow_color", self.color)

        self.current_display: list[str] = list(initial_text)
        self.locked_positions: list[bool] = [c == " " for c in initial_text]
        self.decrypt_complete = True
        self.on_complete = on_complete
        self._first_animation = True

        self._chaos_timer: Timer | None = None
        self._lock_timer: Timer | None = None
        self._glitch_timer: Timer | None = None
        self._chaos_ticks = 0
        self._max_chaos_ticks = 15

        self._glitch_intensity = 0.0
        self._glitch_mask: list[bool] = []
        self._in_glitch_burst = False
        self._glitch_burst_frames = 0

    def on_mount(self) -> None:
        self.set_text(self.original_text, animate=True)
        self._glitch_timer = self.set_interval(0.12, self._glitch_tick)

    def set_text(self, new_text: str, sentiment: str = None, animate: bool = True) -> None:
        should_animate = animate and (new_text != self.original_text or self._first_animation)

        if should_animate:
            self._first_animation = False
            self._stop_timers()
            self.original_text = new_text
            self.current_display = [self._random_char(0.5) if c != " " else " " for c in new_text]
            self.locked_positions = [c == " " for c in new_text]
            self.decrypt_complete = False
            self._chaos_ticks = 0
            self._glitch_mask = [False] * len(new_text)

            self._chaos_timer = self.set_interval(0.05, self._tick_chaos)
        else:
            self.original_text = new_text
            self.current_display = list(new_text)
            self.locked_positions = [True] * len(new_text)
            self.decrypt_complete = True
            self._glitch_mask = [False] * len(new_text)

            self._render_current()

    def _stop_timers(self) -> None:
        if self._chaos_timer:
            self._chaos_timer.stop()
            self._chaos_timer = None
        if self._lock_timer:
            self._lock_timer.stop()
            self._lock_timer = None

    def _random_char(self, intensity: float = 0.5) -> str:
        if intensity > 0.7:
            pool = GLITCH_CHARS_HEAVY
        elif intensity > 0.4:
            pool = GLITCH_CHARS_MEDIUM + GLITCH_CHARS_LIGHT
        else:
            pool = GLITCH_CHARS_LIGHT
        return random.choice(pool)

    def _tick_chaos(self) -> None:
        for i, char in enumerate(self.original_text):
            if not self.locked_positions[i] and char != " ":
                self.current_display[i] = self._random_char(0.4)

        self._chaos_ticks += 1
        self._render_current()

        if self._chaos_ticks >= self._max_chaos_ticks:
            if self._chaos_timer:
                self._chaos_timer.stop()
                self._chaos_timer = None
            self._lock_timer = self.set_interval(0.08, self._lock_next_char)

    def _lock_next_char(self) -> None:
        for i, char in enumerate(self.original_text):
            if not self.locked_positions[i] and char != " ":
                self.current_display[i] = self.original_text[i]
                self.locked_positions[i] = True

                for j, c in enumerate(self.original_text):
                    if not self.locked_positions[j] and c != " ":
                        self.current_display[j] = self._random_char(0.4)

                self._render_current()
                return

        self.decrypt_complete = True
        self._stop_timers()
        self._render_final()

        if self.on_complete:
            self.on_complete()

    def _glitch_tick(self) -> None:
        if self._in_glitch_burst:
            self._glitch_burst_frames -= 1
            if self._glitch_burst_frames <= 0:
                self._in_glitch_burst = False
                self._glitch_mask = [False] * len(self.original_text)
                if self.decrypt_complete:
                    self._render_final()
                else:
                    self._render_current()
            else:
                self._render_glitched()
            return

        if random.random() > 0.92:
            num_glitches = random.randint(1, 3)
            text_len = len(self.original_text)
            if text_len > 0:
                valid_positions = [i for i, c in enumerate(self.original_text) if c != " "]
                if valid_positions:
                    positions = random.sample(valid_positions, min(num_glitches, len(valid_positions)))
                    self._glitch_mask = [i in positions for i in range(text_len)]
                    self._glitch_intensity = random.uniform(0.3, 0.7)
                    self._in_glitch_burst = True
                    self._glitch_burst_frames = random.randint(2, 5)
                    self._render_glitched()

    def _render_glitched(self) -> None:
        if not self.original_text.strip():
            self.update("")
            self._update_visibility(False)
            return

        self._update_visibility(True)
        colors = get_ui_colors()
        text = Text()
        text.append("[", style=Style(color=colors["text_secondary"]))

        base_chars = self.current_display if not self.decrypt_complete else list(self.original_text)

        for i, char in enumerate(base_chars):
            if self._glitch_mask[i] and char != " ":
                glitch_char = self._random_char(self._glitch_intensity)
                glitch_colors = [colors["text_secondary"], self.glow_color, self.color]
                style = Style(color=random.choice(glitch_colors), dim=random.random() > 0.5)
                text.append(glitch_char, style=style)
            else:
                if char == " ":
                    text.append(char)
                elif self.decrypt_complete or self.locked_positions[i]:
                    text.append(char, style=Style(color=self.color, bold=True))
                else:
                    text.append(char, style=Style(color=colors["text_secondary"], dim=True))

        text.append("]", style=Style(color=colors["text_secondary"]))
        self.update(text)

    def _render_current(self) -> None:
        if not self.original_text.strip():
            self.update("")
            self._update_visibility(False)
            return

        self._update_visibility(True)
        colors = get_ui_colors()
        text = Text()
        text.append("[", style=Style(color=colors["text_secondary"]))

        for i, char in enumerate(self.current_display):
            if self.locked_positions[i]:
                if char == " ":
                    text.append(char)
                else:
                    text.append(char, style=Style(color=self.color, bold=True))
            else:
                style = Style(color=colors["text_secondary"], dim=True)
                text.append(char, style=style)

        text.append("]", style=Style(color=colors["text_secondary"]))
        self.update(text)

    def _render_final(self) -> None:
        if not self.original_text.strip():
            self.update("")
            self._update_visibility(False)
            return

        self._update_visibility(True)
        colors = get_ui_colors()
        text = Text()
        text.append("[", style=Style(color=colors["text_secondary"]))

        for char in self.original_text:
            if char == " ":
                text.append(char)
            else:
                text.append(char, style=Style(color=self.color, bold=True))

        text.append("]", style=Style(color=colors["text_secondary"]))
        self.update(text)

    def _update_visibility(self, visible: bool) -> None:
        if visible:
            self.remove_class("status-hidden")
            self.add_class("status-visible")
        else:
            self.remove_class("status-visible")
            self.add_class("status-hidden")

    def force_complete(self) -> None:
        self._stop_timers()
        self.current_display = list(self.original_text)
        self.locked_positions = [True] * len(self.original_text)
        self.decrypt_complete = True
        self._render_final()

    def start_chaos_mode(self) -> None:
        self._stop_timers()
        self._in_continuous_chaos = True
        self.decrypt_complete = False
        self.locked_positions = [c == " " for c in self.original_text]
        self._chaos_timer = self.set_interval(0.06, self._tick_continuous_chaos)

    def stop_chaos_mode(self, new_sentiment: str = None) -> None:
        self._in_continuous_chaos = False
        if self._chaos_timer:
            self._chaos_timer.stop()
            self._chaos_timer = None

        if new_sentiment:
            new_text = get_entity_status_text(new_sentiment)
            self.set_text(new_text, sentiment=new_sentiment, animate=True)
        else:
            self.set_text(self.original_text, animate=True)

    def _tick_continuous_chaos(self) -> None:
        if not getattr(self, "_in_continuous_chaos", False):
            return

        for i, char in enumerate(self.original_text):
            if char != " ":
                self.current_display[i] = self._random_char(0.6)

        self._render_chaos()

    def _render_chaos(self) -> None:
        if not self.original_text.strip():
            self.update("")
            self._update_visibility(False)
            return

        self._update_visibility(True)
        colors = get_ui_colors()
        text = Text()
        text.append("[", style=Style(color=colors["text_secondary"]))

        chaos_colors = [colors["text_secondary"], colors["text_user"], colors["secondary"], colors["primary"]]

        for char in self.current_display:
            if char == " ":
                text.append(char)
            else:
                style = Style(color=random.choice(chaos_colors), dim=random.random() > 0.4)
                text.append(char, style=style)

        text.append("]", style=Style(color=colors["text_secondary"]))
        self.update(text)

    def is_in_chaos(self) -> bool:
        return getattr(self, "_in_continuous_chaos", False)
