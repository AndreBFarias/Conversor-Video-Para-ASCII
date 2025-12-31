from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.soul.onboarding.core import OnboardingProcess

logger = logging.getLogger(__name__)


async def falar_onboarding(
    process: OnboardingProcess, texto: str, stability: float = 0.3, style: float = 0.65, speed: float = 1.15
):
    if not texto:
        return
    role = process.selected_entity if process.selected_entity else "luna"
    process.app.add_chat_entry(role, texto)
    if hasattr(process.app, "boca") and process.app.boca:
        try:
            loop = asyncio.get_running_loop()

            if hasattr(process.app, "threading_manager") and process.app.threading_manager:
                process.app.threading_manager.luna_speaking_event.set()
                logger.debug("[ONBOARDING] Luna speaking event SET")

            try:
                if process.use_premium_tts and process.app.boca.elevenlabs_disponivel:
                    logger.debug(f"TTS ElevenLabs: speed={speed}, stability={stability}, style={style}")
                    await loop.run_in_executor(
                        None,
                        lambda: process.app.boca._falar_elevenlabs(
                            texto, speed=speed, stability=stability, style=style
                        ),
                    )
                else:
                    await loop.run_in_executor(None, process.app.boca.falar, texto)
            finally:
                if hasattr(process.app, "threading_manager") and process.app.threading_manager:
                    process.app.threading_manager.luna_speaking_event.clear()
                    logger.debug("[ONBOARDING] Luna speaking event CLEARED")

        except Exception as e:
            logger.error(f"Erro TTS onboarding: {e}")
            if hasattr(process.app, "threading_manager") and process.app.threading_manager:
                process.app.threading_manager.luna_speaking_event.clear()


def pause_listening(process: OnboardingProcess):
    if hasattr(process.app, "threading_manager") and process.app.threading_manager:
        process.app.threading_manager.listening_event.clear()
        logger.debug("[ONBOARDING] Escuta pausada (listening_event cleared)")


def resume_listening(process: OnboardingProcess):
    if hasattr(process.app, "threading_manager") and process.app.threading_manager:
        process.app.threading_manager.listening_event.set()
        logger.debug("[ONBOARDING] Escuta retomada (listening_event set)")


def activate_voice_mode(process: OnboardingProcess):
    if hasattr(process.app, "em_chamada"):
        process.app.em_chamada = True
        logger.info("[ONBOARDING] Modo de voz ativado (em_chamada=True)")
