import logging
import queue

logger = logging.getLogger(__name__)


class AnimationThread:
    def __init__(self, threading_manager, animation_controller, app):
        self.manager = threading_manager
        self.animation_controller = animation_controller
        self.app = app
        self._app_mounted = True

        logger.info("AnimationThread configurado")

    def run(self):
        logger.info("Animation thread rodando...")

        while not self.manager.shutdown_event.is_set():
            try:
                animation_name = self.manager.animation_queue.get(timeout=0.3)

                if animation_name is None:
                    logger.debug("Sentinel recebido, finalizando AnimationThread")
                    break

                if self.manager.interrupt_event.is_set():
                    logger.debug("Animacao cancelada (interrupcao)")
                    animation_name = "observando"
                    self.manager.clear_interrupt()

                logger.debug(f"Executando animacao: {animation_name}")

                current = getattr(self.animation_controller, "current_animation", "observando")

                if animation_name != current:
                    logger.info(f"Transicao de animacao: {current} -> {animation_name}")
                    if self.manager.shutdown_event.is_set() or not self._app_mounted:
                        continue
                    try:
                        self.app.call_from_thread(self.app.run_animation, animation_name)
                    except Exception as e:
                        if "mount" in str(e).lower():
                            self._app_mounted = False
                        logger.debug(f"Erro ao executar animacao: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro em animation thread: {e}", exc_info=True)

        logger.info("Animation thread finalizado")
