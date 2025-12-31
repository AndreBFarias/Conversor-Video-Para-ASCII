ELEMENT_MAP: dict[str, str] = {
    "toggle_voice_call": "#toggle_voice_call",
    "olhar": "#olhar",
    "nova_conversa": "#nova_conversa",
    "ver_historico": "#ver_historico",
    "editar_alma": "#editar_alma",
    "canone": "#canone",
    "quit": "#quit",
    "attach_file": "#attach_file",
    "main_input": "#main_input",
    "menu-pane": "#menu-pane",
    "welcome-pane": "#welcome-pane",
    "chat-area": "#chat-area",
    "input-container": "#input-container",
    "ascii-pane": "#ascii-pane",
    "chat-list": "#chat-list",
    "status-label": "#status-label",
    "emotion-label": "#emotion-label",
}

ONBOARDING_HIDEABLE: list[str] = [
    "toggle_voice_call",
    "olhar",
    "nova_conversa",
    "ver_historico",
    "editar_alma",
    "canone",
    "quit",
    "attach_file",
    "main_input",
]


def get_selector(element_id: str) -> str:
    return ELEMENT_MAP.get(element_id, f"#{element_id}")
