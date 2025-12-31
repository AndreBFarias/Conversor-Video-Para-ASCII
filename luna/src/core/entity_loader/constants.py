from config import APP_DIR

PANTEAO_DIR = APP_DIR / "src" / "assets" / "panteao"
REGISTRY_PATH = PANTEAO_DIR / "registry.json"
ENTITIES_DIR = PANTEAO_DIR / "entities"
PROFILE_PATH = APP_DIR / "src" / "data_memory" / "user" / "profile.json"

DEFAULT_COLORS = {
    "primary_color": "#bd93f9",
    "secondary_color": "#ff79c6",
    "accent_color": "#50fa7b",
    "background": "#282a36",
    "glow_color": "#bd93f9",
    "text_primary": "#f8f8f2",
    "text_secondary": "#6272a4",
}

DEFAULT_GRADIENT = [
    "#bd93f9",
    "#a78bfa",
    "#9580f5",
    "#8b7cf0",
    "#7c6fe8",
    "#6d62e0",
    "#5e55d8",
    "#4f48d0",
    "#6272a4",
]

DEFAULT_BANNER = [
    " ▄█       ███    █▄  ███▄▄▄▄      ▄████████ ",
    "███       ███    ███ ███▀▀▀██▄   ███    ███ ",
    "███       ███    ███ ███   ███   ███    ███ ",
    "███       ███    ███ ███   ███   ███    ███ ",
    "███       ███    ███ ███   ███ ▀███████████ ",
    "███       ███    ███ ███   ███   ███    ███ ",
    "███▌    ▄ ███    ███ ███   ███   ███    ███ ",
    "█████▄▄██ ████████▀   ▀█   █▀    ███    █▀  ",
    "▀                                           ",
]
