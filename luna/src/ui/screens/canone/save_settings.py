from __future__ import annotations

from pathlib import Path

from dotenv import set_key
from textual.widgets import Input, Select, Switch

import config


def save_all_settings(screen, env_path: Path, logger) -> None:
    try:
        env_file = str(env_path)
        mappings = [
            ("select-chat-provider", "CHAT_PROVIDER"),
            ("select-gemini-model", "GEMINI_MODEL"),
            ("select-gemini-live", "GEMINI_LIVE_ENABLED"),
            ("select-gemini-live-voice", "GEMINI_LIVE_VOICE"),
            ("select-chat-local-model", "CHAT_LOCAL_MODEL"),
            ("select-vision-provider", "VISION_PROVIDER"),
            ("select-vision-local-model", "VISION_LOCAL_MODEL"),
            ("select-code-provider", "CODE_PROVIDER"),
            ("select-code-local-model", "CODE_LOCAL_MODEL"),
            ("select-tts-engine", "TTS_ENGINE"),
            ("select-coqui-device", "COQUI_DEVICE"),
            ("select-whisper-model", "WHISPER_MODEL_SIZE"),
            ("select-whisper-compute", "WHISPER_COMPUTE_TYPE"),
            ("input-whisper-keywords", "WHISPER_KEYWORDS"),
            ("input-audio-device", "AUDIO_DEVICE_ID"),
            ("input-webcam-index", "WEBCAM_INDEX"),
            ("input-vad-silence", "VAD_SILENCE_DURATION"),
            ("input-vad-energy", "VAD_ENERGY_THRESHOLD"),
            ("select-vad-strategy", "VAD_STRATEGY"),
            ("switch-vad-auto", "VAD_AUTO_ADJUST"),
            ("input-vad-multiplier", "VAD_NOISE_MULTIPLIER"),
            ("input-vad-calibration", "VAD_CALIBRATION_SECONDS"),
            ("input-google-key", "GOOGLE_API_KEY"),
            ("input-elevenlabs-key", "ELEVENLABS_API_KEY"),
            ("input-elevenlabs-voice", "ELEVENLABS_VOICE_ID"),
            ("input-openai-key", "OPENAI_API_KEY"),
            ("input-deepseek-key", "DEEPSEEK_API_KEY"),
            ("input-ollama-url", "OLLAMA_BASE_URL"),
            ("input-gemini-timeout", "GEMINI_TIMEOUT"),
            ("input-rate-limit", "RATE_MAX_RPM"),
            ("input-cache-ttl", "CACHE_TTL_SECONDS"),
            ("input-anim-fps", "LUNA_ANIM_FPS"),
            ("input-response-max-chars", "RESPONSE_MAX_CHARS"),
            ("input-piscando-fps", "GLITCH_PISCANDO_FPS"),
            ("input-tv-duration", "GLITCH_TV_DURATION"),
            ("input-effect-duration", "GLITCH_EFFECT_DURATION"),
            ("input-effect-interval", "GLITCH_EFFECT_INTERVAL"),
            ("select-glitch-palette", "GLITCH_PALETTE"),
        ]

        for widget_id, env_key in mappings:
            try:
                widget = screen.query_one(f"#{widget_id}")
                if isinstance(widget, Select):
                    if widget.value and widget.value != Select.BLANK:
                        set_key(env_file, env_key, str(widget.value), quote_mode="never")
                elif isinstance(widget, Input):
                    if widget.value:
                        set_key(env_file, env_key, widget.value, quote_mode="never")
                elif isinstance(widget, Switch):
                    set_key(env_file, env_key, "true" if widget.value else "false", quote_mode="never")
            except Exception as e:
                logger.debug(f"Erro ao salvar {widget_id}: {e}")

        _save_voice_ref(screen, env_file, logger)
        _save_switches(screen, env_file, logger)
        _save_glitch_triggers(screen, env_file, logger)
        _reload_config(screen, logger)

        screen.notify("Fiat Lux!", severity="information", timeout=2)
        logger.info("Configuracoes salvas no .env e recarregadas")
        screen.app.pop_screen()

    except Exception as e:
        logger.error(f"Erro ao salvar configuracoes: {e}")
        screen.notify(f"Erro: {e}", severity="error", timeout=5)


def _save_voice_ref(screen, env_file: str, logger) -> None:
    try:
        voice_select = screen.query_one("#select-voice-ref", Select)
        if voice_select.value is not None:
            if voice_select.value == "":
                set_key(env_file, "COQUI_REFERENCE_AUDIO", "", quote_mode="never")
            elif voice_select.value != Select.BLANK:
                set_key(env_file, "COQUI_REFERENCE_AUDIO", str(voice_select.value), quote_mode="never")
    except Exception as e:
        logger.debug(f"Erro ao salvar voice ref: {e}")


def _save_switches(screen, env_file: str, logger) -> None:
    try:
        gpu_switch = screen.query_one("#switch-use-gpu", Switch)
        set_key(env_file, "USE_GPU", "true" if gpu_switch.value else "false", quote_mode="never")

        debug_switch = screen.query_one("#switch-debug", Switch)
        set_key(env_file, "DEBUG_MODE", "true" if debug_switch.value else "false", quote_mode="never")
    except Exception as e:
        logger.debug(f"Erro ao salvar switches GPU/Debug: {e}")


def _save_glitch_triggers(screen, env_file: str, logger) -> None:
    try:
        banner_input = screen.query_one("#input-banner-trigger", Input)
        if banner_input.value:
            pct = float(banner_input.value)
            trigger = 1.0 - (pct / 100.0)
            set_key(env_file, "GLITCH_BANNER_TRIGGER", f"{trigger:.2f}", quote_mode="never")

        button_input = screen.query_one("#input-button-trigger", Input)
        if button_input.value:
            pct = float(button_input.value)
            trigger = 1.0 - (pct / 100.0)
            set_key(env_file, "GLITCH_BUTTON_TRIGGER", f"{trigger:.2f}", quote_mode="never")
    except Exception as e:
        logger.debug(f"Erro ao salvar triggers de glitch: {e}")


def _reload_config(screen, logger) -> None:
    config.reload_config()

    if hasattr(screen.app, "animation_controller"):
        screen.app.animation_controller.load_all_animations()
        logger.info(f"Animacoes recarregadas com FPS={config.FRAME_RATE}")

    if hasattr(screen.app, "consciencia") and screen.app.consciencia:
        from src.core.entity_loader import get_active_entity

        entity_id = get_active_entity()
        screen.app.consciencia.reload_for_entity(entity_id)
        logger.info(f"Consciencia recarregada para {entity_id}")

    if hasattr(screen.app, "visao") and screen.app.visao:
        screen.app.visao.reload_config()
        logger.info("Visao recarregada")
