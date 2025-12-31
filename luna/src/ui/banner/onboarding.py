from __future__ import annotations

import asyncio
import logging
import random

from src.ui.banner.helpers import create_entity_banner, create_entity_banner_glitched
from src.ui.banner.tv_static import get_tv_engine
from src.ui.elements import ONBOARDING_HIDEABLE

logger = logging.getLogger(__name__)


class OnboardingStaticOverlay:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.timer = None
        self._engine = get_tv_engine(app)
        self.revealed_elements: set = set()
        self.fullscreen_mode = True

    def start(self):
        if self.running:
            return
        self.running = True
        self.fullscreen_mode = True
        self.revealed_elements = set()
        self.timer = self.app.set_interval(0.12, self._update_overlay)

        for elem_id in ONBOARDING_HIDEABLE:
            try:
                elem = self.app.query_one(f"#{elem_id}")
                elem.add_class("onboarding-hidden")
                elem.remove_class("onboarding-revealed")
                elem.remove_class("glitch-reveal")
                elem.remove_class("revealed-stable")
            except Exception as e:
                logger.debug(f"Erro ao esconder elemento {elem_id} no onboarding: {e}")

        try:
            welcome = self.app.query_one("#welcome-pane")
            welcome.add_class("onboarding-hidden")

            status = self.app.query_one("#status-label")
            status.add_class("status-visible")
            status.remove_class("status-hidden")
        except Exception as e:
            logger.debug(f"Erro ao configurar widgets para onboarding: {e}")

    def reveal_element(self, element_id: str):
        self.revealed_elements.add(element_id)
        try:
            elem = self.app.query_one(f"#{element_id}")
            elem.remove_class("onboarding-hidden")
            elem.add_class("onboarding-revealed")

            self.app.run_worker(self._animate_reveal(element_id), exclusive=False)
        except Exception as e:
            logger.debug(f"Elemento {element_id} nao encontrado: {e}")

    async def _animate_reveal(self, element_id: str):
        try:
            elem = self.app.query_one(f"#{element_id}")

            for i in range(8):
                if i % 2 == 0:
                    elem.add_class("glitch-reveal")
                    elem.remove_class("onboarding-revealed")
                else:
                    elem.remove_class("glitch-reveal")
                    elem.add_class("onboarding-revealed")
                await asyncio.sleep(0.06)

            elem.remove_class("glitch-reveal")
            elem.remove_class("onboarding-revealed")
            elem.add_class("revealed-stable")

        except Exception as e:
            logger.debug(f"Erro na animacao de reveal do elemento {element_id}: {e}")

    def reveal_banner(self):
        self.fullscreen_mode = False
        try:
            welcome = self.app.query_one("#welcome-pane")
            welcome.remove_class("onboarding-hidden")
            welcome.remove_class("hidden")
            welcome.styles.display = "block"
            welcome.update(create_entity_banner())
            welcome.refresh()
            logger.info("[ONBOARDING] Banner LUNA revelado com sucesso")
        except Exception as e:
            logger.error(f"[ONBOARDING] Erro ao revelar banner: {e}")

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
            self.timer = None

        for elem_id in ONBOARDING_HIDEABLE:
            try:
                elem = self.app.query_one(f"#{elem_id}")
                elem.remove_class("onboarding-hidden")
                elem.remove_class("onboarding-revealed")
                elem.remove_class("glitch-reveal")
                elem.remove_class("revealed-stable")
            except Exception as e:
                logger.debug(f"Erro ao restaurar elemento {elem_id} apos onboarding: {e}")

        try:
            welcome = self.app.query_one("#welcome-pane")
            welcome.remove_class("onboarding-hidden")
            welcome.remove_class("onboarding-revealed")
            welcome.update(create_entity_banner())

            status = self.app.query_one("#status-label")
            status.add_class("status-hidden")
            status.remove_class("status-visible")
            status.update("")
        except Exception as e:
            logger.debug(f"Erro ao restaurar widgets apos stop onboarding: {e}")

    def _update_overlay(self):
        if not self.running:
            return

        try:
            ascii_pane = self.app.query_one("#ascii-pane")
            w, h = self._engine._get_widget_dims("ascii-pane")
            ascii_pane.update(self._engine.generate_static_text(w, h, density=0.7))

            if self.fullscreen_mode:
                welcome = self.app.query_one("#welcome-pane")
                w_b, h_b = self._engine._get_widget_dims("welcome-pane")
                welcome.update(self._engine.generate_static_text(w_b, h_b, density=0.65))
            else:
                welcome = self.app.query_one("#welcome-pane")
                welcome.update(create_entity_banner_glitched(glitch_intensity=0.06))

            status = self.app.query_one("#status-label")
            msgs = [
                "[Iniciando ritual...]",
                "[Sintonizando almas...]",
                "[Aguardando conexao...]",
                "[Preparando portal...]",
            ]
            if random.random() > 0.6:
                status.update(random.choice(msgs))

        except Exception as e:
            logger.debug(f"Erro ao atualizar overlay do onboarding: {e}")
