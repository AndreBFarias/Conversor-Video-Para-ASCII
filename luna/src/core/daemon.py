import logging
from threading import Event
from typing import TYPE_CHECKING

import config
from src.core.entity_loader import get_active_entity, get_entity_name

if TYPE_CHECKING:
    from main import LunaApp

logger = logging.getLogger(__name__)


class DaemonController:
    def __init__(self, app: "LunaApp"):
        self.app = app
        self.tray = None
        self._hidden = False
        self._wake_event = Event()
        self._initialized = False

    def setup(self) -> bool:
        if not config.DAEMON_MODE:
            logger.info("[DAEMON] Modo daemon desativado")
            return False

        try:
            from src.core.tray import PYSTRAY_AVAILABLE, SystemTrayManager

            if not PYSTRAY_AVAILABLE:
                logger.warning("[DAEMON] pystray nao disponivel")
                return False

            self.tray = SystemTrayManager(
                icon_path=config.TRAY_ICON_PATH,
                on_show=self._show_app,
                on_hide=self._hide_app,
                on_quit=self._quit_app,
                on_toggle_voice=self._toggle_voice,
                on_canone=self._open_canone,
                on_vision=self._capture_vision,
            )

            if self.tray.start():
                self._initialized = True
                logger.info("[DAEMON] Controller inicializado com system tray")

                initial_voice_state = self.app.em_chamada
                self.tray.update_voice_state(initial_voice_state)
                logger.info(f"[DAEMON] Estado inicial de voz sincronizado: {initial_voice_state}")

                if config.START_MINIMIZED:
                    self._hide_app()

                return True

        except Exception as e:
            logger.error(f"[DAEMON] Erro ao configurar: {e}")

        return False

    def _show_app(self):
        self._hidden = False
        logger.info("[DAEMON] Restaurando janela")

        try:
            self.app.call_from_thread(self._restore_window_sync)
        except Exception as e:
            logger.error(f"[DAEMON] Erro ao restaurar: {e}")

    def _hide_app(self):
        self._hidden = True
        logger.info("[DAEMON] Ocultando janela")

        try:
            self.app.call_from_thread(self._minimize_window_sync)
        except Exception as e:
            logger.error(f"[DAEMON] Erro ao ocultar: {e}")

    def _restore_window_sync(self):
        try:
            main_container = self.app.query_one("#main-container")
            main_container.display = True
            self.app.refresh()
        except Exception as e:
            logger.debug(f"[DAEMON] Erro ao restaurar sync: {e}")

    def _minimize_window_sync(self):
        try:
            main_container = self.app.query_one("#main-container")
            main_container.display = False
        except Exception as e:
            logger.debug(f"[DAEMON] Erro ao minimizar sync: {e}")

    def _quit_app(self):
        logger.info("[DAEMON] Encerrando aplicacao via tray (force quit)")
        try:
            import asyncio

            self.app.call_from_thread(lambda: asyncio.create_task(self.app.action_force_quit()))
        except Exception as e:
            logger.error(f"[DAEMON] Erro ao encerrar: {e}")

    def _toggle_voice(self, enabled: bool):
        logger.info(f"[DAEMON] Toggle voz: {enabled}")
        try:
            if enabled:
                self.app.threading_manager.listening_event.set()
                self.app.em_chamada = True
            else:
                self.app.threading_manager.listening_event.clear()
                self.app.em_chamada = False

            if self.tray:
                self.tray.update_voice_state(enabled)

        except Exception as e:
            logger.error(f"[DAEMON] Erro ao toggle voz: {e}")

    def _open_canone(self):
        logger.info("[DAEMON] Abrindo Canone via tray")
        try:
            self.app.call_from_thread(self._open_canone_sync)
        except Exception as e:
            logger.error(f"[DAEMON] Erro ao abrir Canone: {e}")

    def _open_canone_sync(self):
        try:
            self.app.push_screen("canone")
        except Exception as e:
            logger.debug(f"[DAEMON] Erro ao abrir Canone sync: {e}")

    def _capture_vision(self):
        logger.info("[DAEMON] Capturando visao via tray")
        try:
            import asyncio

            self.app.call_from_thread(lambda: asyncio.create_task(self._capture_vision_async()))
        except Exception as e:
            logger.error(f"[DAEMON] Erro ao capturar visao: {e}")

    async def _capture_vision_async(self):
        try:
            if hasattr(self.app, "visao") and self.app.visao:
                result = await self.app.visao.olhar_agora()
                if result:
                    logger.info(f"[DAEMON] Visao capturada: {result[:100]}...")
                    if self.tray:
                        entity_name = get_entity_name(get_active_entity())
                        self.tray.notify(entity_name, "Captura realizada")
        except Exception as e:
            logger.error(f"[DAEMON] Erro na captura: {e}")

    def on_wake_word(self, greeting: str):
        logger.info(f"[DAEMON] Wake word callback: {greeting}")

        if self._hidden:
            self._show_app()

            if self.tray:
                entity_name = get_entity_name(get_active_entity())
                self.tray.notify(entity_name, greeting)

        try:
            self.app.call_from_thread(self.app._handle_wake_word, greeting)
        except Exception as e:
            logger.error(f"[DAEMON] Erro no wake word callback: {e}")

    def notify(self, title: str, message: str):
        if self.tray and self._initialized:
            self.tray.notify(title, message)

    def shutdown(self):
        if self.tray:
            self.tray.stop()
            logger.info("[DAEMON] Controller encerrado")

    @property
    def is_hidden(self) -> bool:
        return self._hidden

    @property
    def is_initialized(self) -> bool:
        return self._initialized
