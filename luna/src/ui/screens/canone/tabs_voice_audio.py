from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Select, Static, Switch

from src.ui.screens.canone.helpers import EnvHelper


def compose_voice_tab(env: EnvHelper) -> ComposeResult:
    with VerticalScroll(id="voice-scroll"):
        yield Static("[#754f8f]Motor TTS[/]", classes="canone-section")
        yield Select(
            [
                ("Coqui XTTS (Local, Alta Qualidade)", "coqui"),
                ("Chatterbox (Local, Expressivo)", "chatterbox"),
                ("ElevenLabs (Cloud, Premium)", "elevenlabs"),
            ],
            id="select-tts-engine",
            value=env.get("TTS_ENGINE", "coqui"),
        )

        yield Static("[#754f8f]Voz de Referencia (Coqui)[/]", classes="canone-section")
        yield Select(env.get_voice_options(), id="select-voice-ref", value=env.get_current_voice())

        yield Static("[#754f8f]Dispositivo Coqui[/]", classes="canone-section")
        yield Select(
            [
                ("GPU (CUDA)", "cuda"),
                ("CPU", "cpu"),
            ],
            id="select-coqui-device",
            value=env.get("COQUI_DEVICE", "cuda"),
        )

        yield Static("[#754f8f]Modelo Whisper (STT)[/]", classes="canone-section")
        yield Static("[dim]Small recomendado para RTX 3050[/dim]", classes="canone-hint")
        yield Select(
            [
                ("Tiny (~75MB, Ultra Rapido)", "tiny"),
                ("Base (~150MB)", "base"),
                ("Small (~500MB, Recomendado)", "small"),
                ("Medium (~1.5GB)", "medium"),
            ],
            id="select-whisper-model",
            value=env.get("WHISPER_MODEL_SIZE", "small"),
        )

        yield Static("[#754f8f]Tipo de Computacao[/]", classes="canone-section")
        yield Select(
            [
                ("Float16 (GPU)", "float16"),
                ("Int8 (CPU)", "int8"),
                ("Float32 (Compativel)", "float32"),
            ],
            id="select-whisper-compute",
            value=env.get("WHISPER_COMPUTE_TYPE", "float16"),
        )

        yield Static("[#754f8f]Palavras-chave para Transcricao[/]", classes="canone-section")
        yield Static(
            "[dim]Palavras que voce usa frequentemente (separadas por virgula)[/dim]",
            classes="canone-hint",
        )
        yield Input(
            placeholder="Luna,oi Luna,tudo bem",
            id="input-whisper-keywords",
            value=env.get("WHISPER_KEYWORDS", "Luna,oi Luna,ei Luna"),
        )


def compose_audio_tab(env: EnvHelper) -> ComposeResult:
    with VerticalScroll(id="audio-scroll"):
        yield Static("[#754f8f]Dispositivo de Audio[/]", classes="canone-section")
        yield Static("[dim]0 = microfone padrao do sistema[/dim]", classes="canone-hint")
        yield Input(
            placeholder="0 = padrao, ou ID especifico (1, 2...)",
            id="input-audio-device",
            value=env.get("AUDIO_DEVICE_ID", "0"),
        )

        yield Static("[#754f8f]Indice da Webcam[/]", classes="canone-section")
        yield Input(
            placeholder="0 = primeira webcam",
            id="input-webcam-index",
            value=env.get("WEBCAM_INDEX", "0"),
        )

        yield Static("[#754f8f]VAD - Silencio para Parar (segundos)[/]", classes="canone-section")
        yield Input(
            placeholder="2.0",
            id="input-vad-silence",
            value=env.get("VAD_SILENCE_DURATION", "2.0"),
        )

        yield Static("[#754f8f]VAD - Limiar de Energia[/]", classes="canone-section")
        yield Static("[dim]Aumente se ruido ambiente dispara o VAD (3000-8000)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="6000",
            id="input-vad-energy",
            value=env.get("VAD_ENERGY_THRESHOLD", "6000"),
        )

        yield Static("[#754f8f]Estrategia VAD[/]", classes="canone-section")
        yield Select(
            [
                ("Energy (Simples)", "energy"),
                ("WebRTC (Avancado)", "webrtc"),
            ],
            id="select-vad-strategy",
            value=env.get("VAD_STRATEGY", "energy"),
        )

        yield Static("[#754f8f]VAD Auto-Ajuste[/]", classes="canone-section")
        yield Static("[dim]Calibra threshold baseado no ruido ambiente[/dim]", classes="canone-hint")
        yield Switch(value=env.get("VAD_AUTO_ADJUST", "true").lower() == "true", id="switch-vad-auto")

        yield Static("[#754f8f]Multiplicador de Ruido[/]", classes="canone-section")
        yield Static("[dim]Threshold = ruido ambiente x multiplicador (1.5-3.0)[/dim]", classes="canone-hint")
        yield Input(
            placeholder="2.0",
            id="input-vad-multiplier",
            value=env.get("VAD_NOISE_MULTIPLIER", "2.0"),
        )

        yield Static("[#754f8f]Tempo de Calibracao (segundos)[/]", classes="canone-section")
        yield Input(
            placeholder="3.0",
            id="input-vad-calibration",
            value=env.get("VAD_CALIBRATION_SECONDS", "3.0"),
        )
