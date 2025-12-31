from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Input, Label, Select, Static, Switch

from src.ui.glitch_button import GlitchButton
from src.ui.screens.canone.helpers import EnvHelper


def compose_entity_tab(entity_config: dict, primary_color: str, entity_name: str) -> ComposeResult:
    with VerticalScroll(id="entity-scroll"):
        yield Static("[#754f8f]Entidade Ativa[/]", classes="canone-section")
        yield Static("[dim]Escolha qual essencia manifestar[/dim]", classes="canone-hint")

        yield Static(
            f"[bold {primary_color}]{entity_name}[/]",
            id="current-entity-name",
            classes="canone-section",
        )

        persona = entity_config.get("persona", {})
        archetype_list = persona.get("archetype", [])
        archetype_str = ", ".join(archetype_list) if archetype_list else "Sem descricao"

        yield Static(f"[dim]{archetype_str}[/dim]", id="current-entity-description", classes="canone-hint")

        yield Static("[#754f8f]Trocar Entidade[/]", classes="canone-section")
        yield Static("[dim]Abre o selector de entidades[/dim]", classes="canone-hint")
        yield GlitchButton("Invocar Outra Essencia", id="btn-change-entity")


def compose_keys_tab(env: EnvHelper) -> ComposeResult:
    with VerticalScroll(id="keys-scroll"):
        yield Static("[#754f8f]Google API Key[/]", classes="canone-section")
        yield Static("[dim]Gemini - makersuite.google.com/app/apikey[/dim]", classes="canone-hint")
        yield Input(
            placeholder="AIza...",
            password=True,
            id="input-google-key",
            value=env.get("GOOGLE_API_KEY", ""),
        )

        yield Static("[#754f8f]ElevenLabs API Key[/]", classes="canone-section")
        yield Static("[dim]elevenlabs.io (TTS Cloud)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="Opcional",
            password=True,
            id="input-elevenlabs-key",
            value=env.get("ELEVENLABS_API_KEY", ""),
        )

        yield Static("[#754f8f]ElevenLabs Voice ID[/]", classes="canone-section")
        yield Input(
            placeholder="ID da voz",
            id="input-elevenlabs-voice",
            value=env.get("ELEVENLABS_VOICE_ID", ""),
        )

        yield Static("[#754f8f]OpenAI API Key[/]", classes="canone-section")
        yield Static("[dim]Whisper Cloud (STT alternativo)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="sk-...",
            password=True,
            id="input-openai-key",
            value=env.get("OPENAI_API_KEY", ""),
        )

        yield Static("[#754f8f]DeepSeek API Key[/]", classes="canone-section")
        yield Static("[dim]Codigo Cloud[/dim]", classes="canone-hint")
        yield Input(
            placeholder="Opcional",
            password=True,
            id="input-deepseek-key",
            value=env.get("DEEPSEEK_API_KEY", ""),
        )


def compose_advanced_tab(env: EnvHelper) -> ComposeResult:
    with VerticalScroll(id="advanced-scroll"):
        yield Static("[#754f8f]Ollama URL[/]", classes="canone-section")
        yield Input(
            placeholder="http://localhost:11434",
            id="input-ollama-url",
            value=env.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

        yield Static("[#754f8f]Gemini Timeout (segundos)[/]", classes="canone-section")
        yield Input(placeholder="15", id="input-gemini-timeout", value=env.get("GEMINI_TIMEOUT", "15"))

        yield Static("[#754f8f]Rate Limit (requests/min)[/]", classes="canone-section")
        yield Input(placeholder="15", id="input-rate-limit", value=env.get("RATE_MAX_RPM", "15"))

        yield Static("[#754f8f]Cache TTL (segundos)[/]", classes="canone-section")
        yield Input(
            placeholder="3600",
            id="input-cache-ttl",
            value=env.get("CACHE_TTL_SECONDS", "3600"),
        )

        yield Static("[#754f8f]GPU[/]", classes="canone-section")
        with Horizontal(classes="canone-switch-row"):
            yield Label("Usar GPU")
            yield Switch(id="switch-use-gpu", value=env.get("USE_GPU", "true").lower() == "true")

        yield Static("[#754f8f]Debug[/]", classes="canone-section")
        with Horizontal(classes="canone-switch-row"):
            yield Label("Modo Debug")
            yield Switch(id="switch-debug", value=env.get("DEBUG_MODE", "false").lower() == "true")

        yield Static("[#754f8f]Animacao FPS[/]", classes="canone-section")
        yield Input(placeholder="24", id="input-anim-fps", value=env.get("LUNA_ANIM_FPS", "24"))

        yield Static("[#754f8f]Limite Resposta (chars)[/]", classes="canone-section")
        yield Static("[dim]Maximo de caracteres por resposta (docs/codigo)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="3000",
            id="input-response-max-chars",
            value=env.get("RESPONSE_MAX_CHARS", "3000"),
        )


def compose_effects_tab(env: EnvHelper) -> ComposeResult:
    with VerticalScroll(id="effects-scroll"):
        yield Static("[#754f8f]FPS Animacao Piscando[/]", classes="canone-section")
        yield Static("[dim]Velocidade da animacao ao piscar[/dim]", classes="canone-hint")
        yield Input(
            placeholder="24.0",
            id="input-piscando-fps",
            value=env.get("GLITCH_PISCANDO_FPS", "24.0"),
        )

        yield Static("[#754f8f]Duracao Transicao TV (s)[/]", classes="canone-section")
        yield Static("[dim]Tempo do efeito de transicao static[/dim]", classes="canone-hint")
        yield Input(
            placeholder="1.2",
            id="input-tv-duration",
            value=env.get("GLITCH_TV_DURATION", "1.2"),
        )

        yield Static("[#754f8f]Duracao Media Glitch (s)[/]", classes="canone-section")
        yield Static("[dim]Tempo de cada efeito glitch[/dim]", classes="canone-hint")
        yield Input(
            placeholder="0.3",
            id="input-effect-duration",
            value=env.get("GLITCH_EFFECT_DURATION", "0.3"),
        )

        yield Static("[#754f8f]Intervalo entre Glitchs (s)[/]", classes="canone-section")
        yield Static("[dim]Frequencia de verificacao de glitch[/dim]", classes="canone-hint")
        yield Input(
            placeholder="0.15",
            id="input-effect-interval",
            value=env.get("GLITCH_EFFECT_INTERVAL", "0.15"),
        )

        yield Static("[#754f8f]Chance Glitch Banner (%)[/]", classes="canone-section")
        yield Static("[dim]Probabilidade de glitch no logo (6 = 6%)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="6",
            id="input-banner-trigger",
            value=str(int((1 - float(env.get("GLITCH_BANNER_TRIGGER", "0.94"))) * 100)),
        )

        yield Static("[#754f8f]Chance Glitch Botao (%)[/]", classes="canone-section")
        yield Static("[dim]Probabilidade de glitch nos botoes (8 = 8%)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="8",
            id="input-button-trigger",
            value=str(int((1 - float(env.get("GLITCH_BUTTON_TRIGGER", "0.92"))) * 100)),
        )

        yield Static("[#754f8f]Paleta de Cores[/]", classes="canone-section")
        yield Static("[dim]Tema de cores dos efeitos glitch[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Dracula (Roxo/Cyan)", "dracula"),
                ("Neon (Verde/Magenta)", "neon"),
                ("Monokai (Verde/Rosa)", "monokai"),
                ("Blood (Vermelho)", "blood"),
            ],
            id="select-glitch-palette",
            value=env.get("GLITCH_PALETTE", "dracula"),
        )
