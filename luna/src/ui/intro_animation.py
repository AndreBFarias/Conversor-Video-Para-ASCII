from src.ui.intro_animation import (
    GLITCH_CHARS_HEAVY,
    GLITCH_CHARS_LIGHT,
    GLITCH_CHARS_MEDIUM,
    STATIC_CHARS,
    BannerAnimation,
    PersonaIntro,
    _get_persona_configs,
    demo,
)

__all__ = [
    "PersonaIntro",
    "BannerAnimation",
    "demo",
    "_get_persona_configs",
    "GLITCH_CHARS_LIGHT",
    "GLITCH_CHARS_MEDIUM",
    "GLITCH_CHARS_HEAVY",
    "STATIC_CHARS",
]

if __name__ == "__main__":
    demo()
