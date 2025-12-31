import random
import time
from collections.abc import Callable

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.style import Style
from rich.text import Text

from src.ui.colors import get_ui_colors

from .constants import GLITCH_CHARS_HEAVY, GLITCH_CHARS_LIGHT, GLITCH_CHARS_MEDIUM, STATIC_CHARS


def _get_persona_configs() -> dict:
    colors = get_ui_colors()
    return {
        "LUNA": {"color": colors["primary"], "accent": colors["secondary"]},
        "ERIS": {"color": colors["primary"], "accent": colors["secondary"]},
        "JUNO": {"color": colors["primary"], "accent": colors["secondary"]},
        "ARES": {"color": colors["text_error"], "accent": colors["secondary"]},
        "ATHENA": {"color": colors["text_user"], "accent": colors["primary"]},
        "HERMES": {"color": colors["accent"], "accent": colors["text_user"]},
        "HADES": {"color": colors["text_secondary"], "accent": colors["primary"]},
        "APHRODITE": {"color": colors["secondary"], "accent": colors["primary"]},
        "HEPHAESTUS": {"color": colors["text_error"], "accent": colors["accent"]},
        "DIONYSUS": {"color": colors["accent"], "accent": colors["text_success"]},
    }


class PersonaIntro:
    def __init__(
        self,
        persona_name: str,
        primary_color: str | None = None,
        accent_color: str | None = None,
        console: Console | None = None,
        width: int = 40,
    ):
        self.persona_name = persona_name.upper()
        self.console = console or Console()
        self.width = width

        colors = get_ui_colors()
        persona_configs = _get_persona_configs()
        config = persona_configs.get(self.persona_name, {})
        self.primary_color = primary_color or config.get("color", colors["primary"])
        self.accent_color = accent_color or config.get("accent", colors["secondary"])
        self._colors = colors

        self.locked_positions: list[bool] = [False] * len(self.persona_name)
        self.current_display: list[str] = list(self.persona_name)

        self._on_complete: Callable | None = None
        self._is_idle = False
        self._glitch_intensity = 0.0

    def _random_char(self, intensity: float = 0.5) -> str:
        if intensity > 0.7:
            pool = GLITCH_CHARS_HEAVY
        elif intensity > 0.4:
            pool = GLITCH_CHARS_MEDIUM + GLITCH_CHARS_LIGHT
        else:
            pool = GLITCH_CHARS_LIGHT
        return random.choice(pool)

    def _build_name_display(self, glitch_mask: list[bool] = None) -> Text:
        text = Text()

        padding = (self.width - len(self.persona_name) - 8) // 2
        text.append(" " * max(0, padding))

        text.append("[ ", style=Style(color=self._colors["text_secondary"]))

        for i, char in enumerate(self.current_display):
            is_glitched = glitch_mask[i] if glitch_mask else False

            if is_glitched:
                glitch_char = self._random_char(self._glitch_intensity)
                glitch_colors = [self._colors["text_secondary"], self._colors["text_user"], self.accent_color]
                style = Style(color=random.choice(glitch_colors), dim=random.random() > 0.5)
                text.append(glitch_char, style=style)
            elif self.locked_positions[i]:
                style = Style(color=self.primary_color, bold=True)
                text.append(char, style=style)
            else:
                style = Style(color=self._colors["text_secondary"], dim=True)
                text.append(self._random_char(0.3), style=style)

        text.append(" ]", style=Style(color=self._colors["text_secondary"]))

        return text

    def _build_scanline(self, active: bool = False) -> Text:
        line = Text()
        if active:
            char = random.choice(["─", "━", "╌", "┄"])
            style = Style(color=self._colors["text_secondary"], dim=True)
            line.append(char * self.width, style=style)
        return line

    def _build_static_noise(self, density: float = 0.1) -> Text:
        line = Text()
        for _ in range(self.width):
            if random.random() < density:
                char = random.choice(STATIC_CHARS)
                noise_colors = [self._colors["text_secondary"], self._colors["background"], self.primary_color]
                style = Style(color=random.choice(noise_colors), dim=True)
                line.append(char, style=style)
            else:
                line.append(" ")
        return line

    def _build_frame(
        self, show_scanlines: bool = False, static_density: float = 0.0, glitch_mask: list[bool] = None
    ) -> Text:
        lines = []

        if show_scanlines and random.random() > 0.7:
            lines.append(self._build_scanline(True))
        else:
            lines.append(Text())

        if static_density > 0 and random.random() > 0.8:
            lines.append(self._build_static_noise(static_density))
        else:
            lines.append(Text())

        name_line = self._build_name_display(glitch_mask)
        lines.append(Align.center(name_line))

        if static_density > 0 and random.random() > 0.8:
            lines.append(self._build_static_noise(static_density * 0.5))
        else:
            lines.append(Text())

        if show_scanlines and random.random() > 0.7:
            lines.append(self._build_scanline(True))
        else:
            lines.append(Text())

        return Group(*lines)

    def _decrypt_animation(self, live: Live):
        total_chars = len(self.persona_name)

        self.current_display = [self._random_char(0.5) for _ in self.persona_name]
        self.locked_positions = [False] * total_chars

        for _ in range(25):
            for i in range(total_chars):
                self.current_display[i] = self._random_char(0.4)

            frame = self._build_frame(show_scanlines=True, static_density=0.05)
            live.update(Align.center(frame))
            time.sleep(0.06)

        for i in range(total_chars):
            for _ in range(random.randint(6, 12)):
                for j in range(total_chars):
                    if not self.locked_positions[j]:
                        self.current_display[j] = self._random_char(0.3)

                frame = self._build_frame(show_scanlines=True, static_density=0.02)
                live.update(Align.center(frame))
                time.sleep(0.04)

            self.current_display[i] = self.persona_name[i]
            self.locked_positions[i] = True

            frame = self._build_frame(show_scanlines=False, static_density=0.0)
            live.update(Align.center(frame))
            time.sleep(0.12)

        for _ in range(3):
            frame = self._build_frame(show_scanlines=False, static_density=0.0)
            live.update(Align.center(frame))
            time.sleep(0.08)

            glitch_mask = [random.random() > 0.85 for _ in self.persona_name]
            frame = self._build_frame(show_scanlines=True, static_density=0.03, glitch_mask=glitch_mask)
            live.update(Align.center(frame))
            time.sleep(0.04)

        frame = self._build_frame(show_scanlines=False, static_density=0.0)
        live.update(Align.center(frame))

    def _idle_loop(self, live: Live, duration: float = 10.0):
        self._is_idle = True
        start_time = time.time()

        while time.time() - start_time < duration:
            if random.random() > 0.92:
                num_glitches = random.randint(1, 3)
                glitch_positions = random.sample(
                    range(len(self.persona_name)), min(num_glitches, len(self.persona_name))
                )
                glitch_mask = [i in glitch_positions for i in range(len(self.persona_name))]
                self._glitch_intensity = random.uniform(0.3, 0.7)

                for _ in range(random.randint(2, 5)):
                    frame = self._build_frame(
                        show_scanlines=True, static_density=random.uniform(0.02, 0.08), glitch_mask=glitch_mask
                    )
                    live.update(Align.center(frame))
                    time.sleep(random.uniform(0.03, 0.06))

                frame = self._build_frame(show_scanlines=False, static_density=0.0)
                live.update(Align.center(frame))

            if random.random() > 0.97:
                frame = self._build_frame(show_scanlines=True, static_density=0.15)
                live.update(Align.center(frame))
                time.sleep(0.02)

                frame = self._build_frame(show_scanlines=False, static_density=0.0)
                live.update(Align.center(frame))

            time.sleep(0.1)

        self._is_idle = False

    def on_complete(self, callback: Callable) -> "PersonaIntro":
        self._on_complete = callback
        return self

    def play(self, idle_after: float = 0.0) -> None:
        self.locked_positions = [False] * len(self.persona_name)
        self.current_display = [self._random_char() for _ in self.persona_name]

        try:
            with Live(
                Align.center(self._build_frame()), console=self.console, refresh_per_second=30, screen=True
            ) as live:
                self._decrypt_animation(live)

                if idle_after > 0:
                    self._idle_loop(live, idle_after)

        except KeyboardInterrupt:
            pass

        if self._on_complete:
            self._on_complete()

    def play_inline(self, idle_after: float = 0.0) -> None:
        self.locked_positions = [False] * len(self.persona_name)
        self.current_display = [self._random_char() for _ in self.persona_name]

        try:
            with Live(
                Align.center(self._build_frame()), console=self.console, refresh_per_second=30, screen=False
            ) as live:
                self._decrypt_animation(live)

                if idle_after > 0:
                    self._idle_loop(live, idle_after)

        except KeyboardInterrupt:
            pass

        if self._on_complete:
            self._on_complete()

    def get_static_display(self) -> Text:
        self.current_display = list(self.persona_name)
        self.locked_positions = [True] * len(self.persona_name)
        return self._build_name_display()
