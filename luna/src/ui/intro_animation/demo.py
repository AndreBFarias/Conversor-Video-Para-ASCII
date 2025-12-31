import time

from rich.console import Console

from src.ui.colors import get_ui_colors

from .persona_intro import PersonaIntro


def demo():
    console = Console()
    colors = get_ui_colors()

    console.clear()
    console.print(f"\n[bold {colors['primary']}]PERSONA INTRO - Demo Suave[/]\n")
    console.print(f"[{colors['text_secondary']}]Ctrl+C para pular[/]\n")
    time.sleep(1)

    intro = PersonaIntro("Vitoria", width=120)
    intro.play(idle_after=8.0)

    console.clear()
    console.print(f"\n[bold {colors['accent']}]Demo concluida[/]\n")


if __name__ == "__main__":
    demo()
