from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import config
from src.core.entity_loader import EntityLoader, set_active_entity
from src.soul.onboarding.acts import finish_onboarding, run_act_one, run_act_two
from src.soul.onboarding.dialogues import OnboardingDialogues
from src.soul.onboarding.input_handlers import handle_button_click as _handle_button_click
from src.soul.onboarding.input_handlers import handle_text_input as _handle_text_input
from src.soul.onboarding.profile import ensure_directories, reset_profile, verify_first_run
from src.soul.onboarding.tts_helpers import pause_listening, resume_listening
from src.soul.onboarding.ui_helpers import hide_all_for_onboarding, reload_ui_for_entity, reveal_all
from src.soul.personalidade import get_personalidade
from src.ui.banner import OnboardingStaticOverlay
from src.ui.entity_selector import EntitySelectorScreen

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class OnboardingProcess:
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.input_future = None
        self.button_future = None
        self.waiting_for_button = None
        self.personalidade = get_personalidade()
        self.dialogues = OnboardingDialogues()
        self.user_name = "Viajante"
        self.revealed_elements = set()
        self.static_overlay = None
        self.use_premium_tts = False
        self.use_premium_vision = False
        self.selected_entity = "luna"
        self.entity_loader = None

        self._detect_premium_providers()
        ensure_directories()

    def _detect_premium_providers(self):
        self.use_premium_tts = config.has_premium_tts()
        self.use_premium_vision = config.has_premium_vision()

        if self.use_premium_tts:
            logger.info("ElevenLabs detectado - usando TTS premium no onboarding")
        if self.use_premium_vision:
            logger.info("Gemini detectado - usando Vision premium no onboarding")

    def should_show_entity_selector(self) -> bool:
        try:
            loader = EntityLoader("luna")
            available = loader.list_available_entities()
            return len(available) > 1
        except Exception as e:
            logger.error(f"Erro ao verificar entidades disponiveis: {e}")
            return False

    def verify_first_run(self):
        return verify_first_run()

    def reset_profile(self):
        reset_profile(self.personalidade)

    async def _show_entity_selector(self) -> str:
        try:
            result = await self.app.push_screen_wait(EntitySelectorScreen())
            if result:
                return result
            return "luna"
        except Exception as e:
            logger.error(f"Erro ao mostrar seletor de entidades: {e}")
            return "luna"

    async def start_sequence(self):
        self.is_running = True
        logger.info("Onboarding Sequence Started (Ritual Mode)")

        if self.use_premium_tts:
            logger.info("Usando ElevenLabs para TTS durante onboarding")
        if self.use_premium_vision:
            logger.info("Usando Gemini para Vision durante onboarding")

        self.reset_profile()

        original_state = self.app.app_state
        self.app.app_state = "BUSY"

        pause_listening(self)

        try:
            if self.should_show_entity_selector():
                logger.info("Multiplas entidades disponiveis - mostrando seletor")
                self.selected_entity = await self._show_entity_selector()
                logger.info(f"Entidade selecionada: {self.selected_entity}")
                set_active_entity(self.selected_entity)
                self.entity_loader = EntityLoader(self.selected_entity)
                reload_ui_for_entity(self, self.selected_entity)
            else:
                logger.info("Apenas Luna disponivel - pulando seletor de entidades")
                self.selected_entity = "luna"
                self.entity_loader = EntityLoader("luna")

            self.dialogues.reload_for_entity(self.selected_entity)
            logger.info(f"Dialogos carregados para {self.selected_entity}")

            self.static_overlay = OnboardingStaticOverlay(self.app)
            self.static_overlay.start()

            hide_all_for_onboarding(self)

            await run_act_one(self)
            await run_act_two(self)
            await finish_onboarding(self)

        except asyncio.CancelledError:
            logger.info("Onboarding cancelled.")
        except Exception as e:
            logger.error(f"Error in onboarding: {e}", exc_info=True)
            self.app.add_chat_entry("kernel", f"Erro fatal no onboarding: {e}")
        finally:
            self.is_running = False
            self.app.app_state = "IDLE"
            if self.static_overlay:
                self.static_overlay.stop()
            reveal_all(self)
            resume_listening(self)

    def handle_text_input(self, text):
        return _handle_text_input(self, text)

    def handle_button_click(self, button_id):
        return _handle_button_click(self, button_id)


OnboardingFlow = OnboardingProcess
