import random
from collections.abc import Callable

from rich.console import Console
from rich.text import Text

from .persona_intro import PersonaIntro


class BannerAnimation:
    def __init__(self, persona_name: str, console: Console | None = None, width: int = 50):
        self.persona = PersonaIntro(persona_name, console=console, width=width)
        self.console = console or Console()
        self._running = False

    def start_decrypt(self, callback: Callable | None = None):
        if callback:
            self.persona.on_complete(callback)
        self.persona.play_inline(idle_after=0)

    def get_idle_frame(self, with_glitch: bool = False) -> Text:
        if with_glitch and random.random() > 0.9:
            num_glitches = random.randint(1, 2)
            positions = random.sample(
                range(len(self.persona.persona_name)), min(num_glitches, len(self.persona.persona_name))
            )
            glitch_mask = [i in positions for i in range(len(self.persona.persona_name))]
            self.persona._glitch_intensity = 0.4
            return self.persona._build_frame(
                show_scanlines=random.random() > 0.7,
                static_density=0.02 if random.random() > 0.8 else 0.0,
                glitch_mask=glitch_mask,
            )

        self.persona.current_display = list(self.persona.persona_name)
        self.persona.locked_positions = [True] * len(self.persona.persona_name)
        return self.persona._build_frame(show_scanlines=False, static_density=0.0)
