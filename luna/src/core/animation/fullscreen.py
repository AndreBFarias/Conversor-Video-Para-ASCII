from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from .controller import AnimationController

logger = get_logger(__name__)


def run_fullscreen_animation(controller: AnimationController, sentiment: str):
    logger.info(f"Iniciando animacao FULLSCREEN: {sentiment}")
    controller.is_fullscreen = True

    def setup_fullscreen():
        try:
            controller.app.query_one("#welcome-pane").add_class("hidden")
            controller.app.query_one("#audio-visualizer").add_class("hidden")
            controller.app.query_one("#status-area").add_class("hidden")
            controller.app.query_one("#ascii-pane").add_class("fullscreen")
        except Exception as e:
            logger.error(f"Erro ao configurar fullscreen: {e}")

    controller._safe_ui_call(setup_fullscreen)
    controller.run_animation(sentiment)


def end_fullscreen(controller: AnimationController, with_transition: bool = True):
    if not controller.is_fullscreen:
        return
    logger.info("Encerrando modo FULLSCREEN.")
    controller.is_fullscreen = False

    voice_active = getattr(controller.app, "em_chamada", False)

    def teardown_fullscreen():
        try:
            controller.app.query_one("#ascii-pane").remove_class("fullscreen")
            controller.app.query_one("#status-area").remove_class("hidden")
            controller.app.query_one("#welcome-pane").remove_class("hidden")

            if voice_active:
                controller.app.query_one("#ascii-pane").add_class("hidden")
                controller.app.query_one("#audio-visualizer").remove_class("hidden")
                logger.debug("Fullscreen encerrado: visualizer ativo (voz)")
            else:
                controller.app.query_one("#audio-visualizer").add_class("hidden")
                logger.debug("Fullscreen encerrado: animacao continua")
        except Exception as e:
            logger.error(f"Erro ao restaurar de fullscreen: {e}")

    controller._safe_ui_call(teardown_fullscreen)

    if with_transition:

        async def transition_and_animate():
            from src.ui.banner import run_tv_static_transition

            await run_tv_static_transition(controller.app, 0.8, 15)
            controller.run_animation("observando")

        controller.app.run_worker(transition_and_animate(), exclusive=False, thread=False)
    else:
        controller.run_animation("observando")
