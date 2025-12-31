from __future__ import annotations

import asyncio
import logging
import random

import config
from src.core.entity_loader import get_active_entity
from src.ui.banner.helpers import STATIC_CHARS, create_entity_banner
from src.ui.banner.tv_static import TVTarget, get_tv_engine
from src.ui.elements import ONBOARDING_HIDEABLE
from src.ui.status_decrypt import get_entity_status_text

logger = logging.getLogger(__name__)


class ProgressiveStaticBackground:
    STAGE_ALL = 0
    STAGE_NO_BANNER = 1
    STAGE_NO_STATUS = 2
    STAGE_CLEAR = 3

    def __init__(self, app):
        self.app = app
        self.running = False
        self.timer = None
        self.stage = self.STAGE_ALL
        self._engine = get_tv_engine(app)

    def start(self):
        if self.running:
            return
        self.running = True
        self.stage = self.STAGE_ALL
        self.timer = self.app.set_interval(0.08, self._update_static)

    def advance_stage(self):
        self.stage += 1

        if self.stage == self.STAGE_NO_BANNER:
            self.app.query_one("#welcome-pane").update(create_entity_banner())
        elif self.stage == self.STAGE_NO_STATUS:
            status = self.app.query_one("#status-label")
            emotion = self.app.query_one("#emotion-label")
            if hasattr(status, "set_text"):
                status.set_text("", animate=False)
            else:
                status.update("")
            status.add_class("status-hidden")
            entity_text = get_entity_status_text("observando")
            if hasattr(emotion, "set_text"):
                emotion.set_text(entity_text, sentiment="observando", animate=True)
            else:
                emotion.update(f"[{entity_text}]")
        elif self.stage >= self.STAGE_CLEAR:
            self.stop()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.stage = self.STAGE_CLEAR

        try:
            self.app.query_one("#welcome-pane").update(create_entity_banner())
            status = self.app.query_one("#status-label")
            if hasattr(status, "set_text"):
                status.set_text("", animate=False)
            else:
                status.update("")
            status.add_class("status-hidden")
        except Exception as e:
            logger.debug(f"Erro ao restaurar widgets apos stop: {e}")

    def _update_static(self):
        if not self.running:
            return

        try:
            if self.stage == self.STAGE_ALL:
                self._update_all_static()
            elif self.stage == self.STAGE_NO_BANNER:
                self._update_status_and_ascii_static()
            elif self.stage == self.STAGE_NO_STATUS:
                self._update_ascii_static_only()
        except Exception as e:
            logger.debug(f"Erro ao atualizar static background: {e}")

    def _update_all_static(self):
        welcome = self.app.query_one("#welcome-pane")
        ascii_pane = self.app.query_one("#ascii-pane")
        status = self.app.query_one("#status-label")
        emotion = self.app.query_one("#emotion-label")

        w_banner, h_banner = self._engine._get_widget_dims("welcome-pane")
        w_ascii, h_ascii = self._engine._get_widget_dims("ascii-pane")

        welcome.update(self._engine.generate_static_text(w_banner, h_banner))
        ascii_pane.update(self._engine.generate_static_text(w_ascii, h_ascii))

        status.remove_class("status-hidden")
        status.add_class("status-visible")
        status.update(random.choice(["[Sintonizando...]", "[Ajustando...]", "[Conectando...]"]))

        if not hasattr(emotion, "set_text"):
            emotion.update(f"[{''.join(random.choices(STATIC_CHARS[:8], k=12))}]")

    def _update_status_and_ascii_static(self):
        ascii_pane = self.app.query_one("#ascii-pane")
        status = self.app.query_one("#status-label")
        emotion = self.app.query_one("#emotion-label")

        w, h = self._engine._get_widget_dims("ascii-pane")
        ascii_pane.update(self._engine.generate_static_text(w, h))

        status.remove_class("status-hidden")
        status.add_class("status-visible")
        status.update(random.choice(["[Sintonizando...]", "[Ajustando...]", "[Conectando...]"]))

        if not hasattr(emotion, "set_text"):
            emotion.update(f"[{''.join(random.choices(STATIC_CHARS[:8], k=12))}]")

    def _update_ascii_static_only(self):
        ascii_pane = self.app.query_one("#ascii-pane")
        w, h = self._engine._get_widget_dims("ascii-pane")
        ascii_pane.update(self._engine.generate_static_text(w, h))


ContinuousStaticBackground = ProgressiveStaticBackground


async def run_processing_static(app, on: bool = True):
    if on:
        if not hasattr(app, "_processing_static_bg") or app._processing_static_bg is None:
            app._processing_static_bg = ProgressiveStaticBackground(app)
        app._processing_static_bg.start()

        try:
            status_label = app.query_one("#status-label")
            status_label.remove_class("status-hidden")
            status_label.add_class("status-visible")
        except Exception as e:
            logger.debug(f"Erro ao mostrar status label durante processing: {e}")
    else:
        if hasattr(app, "_processing_static_bg") and app._processing_static_bg:
            app._processing_static_bg.stop()
            app._processing_static_bg = None

        engine = get_tv_engine(app)
        await engine.run(targets={TVTarget.BANNER, TVTarget.ASCII}, duration=0.3, steps=8, pattern="fade_out")
