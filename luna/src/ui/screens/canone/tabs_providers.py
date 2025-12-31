from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Select, Static

from src.ui.screens.canone.helpers import EnvHelper, OllamaModelHelper


def compose_providers_tab(env: EnvHelper) -> ComposeResult:
    chat_options, chat_selected = OllamaModelHelper.get_chat_models(env)
    vision_options, vision_selected = OllamaModelHelper.get_vision_models(env)
    code_options, code_selected = OllamaModelHelper.get_code_models(env)

    with VerticalScroll(id="providers-scroll"):
        yield Static("[#754f8f]Chat Principal[/]", classes="canone-section")
        yield Static("[dim]Provider que controla a mente[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Gemini (Cloud)", "gemini"),
                ("Ollama (Local)", "local"),
            ],
            id="select-chat-provider",
            value=env.get("CHAT_PROVIDER", "gemini"),
        )

        yield Static("[#754f8f]Modelo Gemini[/]", classes="canone-section")
        yield Select(
            [
                ("Gemini 2.0 Flash (Estavel)", "gemini-2.0-flash"),
                ("Gemini 2.0 Flash Exp (Live)", "gemini-2.0-flash-exp"),
                ("Gemini 2.5 Flash (Novo)", "gemini-2.5-flash-preview-05-20"),
                ("Gemini 2.5 Pro (Preciso)", "gemini-2.5-pro-preview-05-06"),
            ],
            id="select-gemini-model",
            value=env.get("GEMINI_MODEL", "gemini-2.0-flash"),
        )

        yield Static("[#754f8f]Gemini Live (Streaming)[/]", classes="canone-section")
        yield Static("[dim]Audio bidirecional em tempo real[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Desativado (TTS Local)", "false"),
                ("Ativado (Voz Gemini)", "true"),
            ],
            id="select-gemini-live",
            value=env.get("GEMINI_LIVE_ENABLED", "false"),
        )

        yield Static("[#754f8f]Voz Gemini Live[/]", classes="canone-section")
        yield Select(
            [
                ("Aoede (Feminina, Suave)", "Aoede"),
                ("Charon (Masculina, Grave)", "Charon"),
                ("Fenrir (Masculina, Energica)", "Fenrir"),
                ("Kore (Feminina, Jovem)", "Kore"),
                ("Puck (Neutra, Leve)", "Puck"),
            ],
            id="select-gemini-live-voice",
            value=env.get("GEMINI_LIVE_VOICE", "Aoede"),
        )

        yield Static("[#754f8f]Modelo Local (Ollama)[/]", classes="canone-section")
        yield Static("[dim]Modelos detectados no Ollama local[/dim]", classes="canone-hint")
        yield Select(chat_options, id="select-chat-local-model", value=chat_selected)

        yield Static("[#754f8f]Visao[/]", classes="canone-section")
        yield Static("[dim]Moondream recomendado para RTX 3050[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Gemini Vision (Cloud)", "gemini"),
                ("Moondream (Local)", "local"),
            ],
            id="select-vision-provider",
            value=env.get("VISION_PROVIDER", "gemini"),
        )

        yield Static("[#754f8f]Modelo de Visao (Ollama)[/]", classes="canone-section")
        yield Select(vision_options, id="select-vision-local-model", value=vision_selected)

        yield Static("[#754f8f]Codigo/Programacao[/]", classes="canone-section")
        yield Static("[dim]Provider para analise e geracao de codigo[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Gemini (Cloud)", "gemini"),
                ("DeepSeek (Cloud)", "deepseek"),
                ("Ollama (Local)", "local"),
            ],
            id="select-code-provider",
            value=env.get("CODE_PROVIDER", "local"),
        )

        yield Static("[#754f8f]Modelo de Codigo (Local)[/]", classes="canone-section")
        yield Static("[dim]Modelos especializados em programacao[/dim]", classes="canone-hint")
        yield Select(code_options, id="select-code-local-model", value=code_selected)
