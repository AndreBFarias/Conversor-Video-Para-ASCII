import logging
from collections.abc import Callable
from pathlib import Path
from threading import Thread

from PIL import Image

from src.core.entity_loader import get_active_entity, get_entity_name

logger = logging.getLogger(__name__)

PYSTRAY_AVAILABLE = False
try:
    import pystray

    PYSTRAY_AVAILABLE = True
except ImportError:
    logger.warning("pystray nao instalado. System tray desativado.")


class SystemTrayManager:
    def __init__(
        self,
        icon_path: Path,
        on_show: Callable,
        on_hide: Callable,
        on_quit: Callable,
        on_toggle_voice: Callable,
        on_canone: Callable = None,
        on_vision: Callable = None,
    ):
        self.icon_path = icon_path
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_quit = on_quit
        self.on_toggle_voice = on_toggle_voice
        self.on_canone = on_canone
        self.on_vision = on_vision

        self.icon = None
        self._thread: Thread | None = None
        self._voice_enabled = True
        self._running = False

    def _create_menu(self):
        if not PYSTRAY_AVAILABLE:
            return None

        menu_items = [
            pystray.MenuItem("Abrir Luna", self._action_show, default=True),
        ]

        if self.on_canone:
            menu_items.append(pystray.MenuItem("Canone", self._action_canone))

        menu_items.append(pystray.Menu.SEPARATOR)

        menu_items.append(
            pystray.MenuItem("Voz Ativa", self._action_toggle_voice, checked=lambda item: self._voice_enabled)
        )

        if self.on_vision:
            menu_items.append(pystray.MenuItem("Ver", self._action_vision))

        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Encerrar", self._action_quit))

        return pystray.Menu(*menu_items)

    def _action_show(self, icon=None, item=None):
        logger.info("[TRAY] Abrir Luna")
        try:
            self.on_show()
        except Exception as e:
            logger.error(f"[TRAY] Erro ao mostrar: {e}")

    def _action_canone(self, icon=None, item=None):
        logger.info("[TRAY] Abrir Canone")
        try:
            if self.on_canone:
                self.on_show()
                self.on_canone()
        except Exception as e:
            logger.error(f"[TRAY] Erro ao abrir Canone: {e}")

    def _action_vision(self, icon=None, item=None):
        logger.info("[TRAY] Capturar Visao")
        try:
            if self.on_vision:
                self.on_vision()
        except Exception as e:
            logger.error(f"[TRAY] Erro ao capturar visao: {e}")

    def _action_quit(self, icon=None, item=None):
        logger.info("[TRAY] Encerrar")
        try:
            self.on_quit()
        except Exception as e:
            logger.error(f"[TRAY] Erro ao sair: {e}")
        finally:
            self.stop()

    def _action_toggle_voice(self, icon=None, item=None):
        self._voice_enabled = not self._voice_enabled
        logger.info(f"[TRAY] Voz = {self._voice_enabled}")
        try:
            self.on_toggle_voice(self._voice_enabled)
        except Exception as e:
            logger.error(f"[TRAY] Erro ao toggle voz: {e}")

    def _load_icon(self) -> Image.Image | None:
        if self.icon_path and self.icon_path.exists():
            try:
                return Image.open(self.icon_path)
            except Exception as e:
                logger.warning(f"[TRAY] Erro ao carregar icone: {e}")

        try:
            icon = Image.new("RGBA", (64, 64), (189, 147, 249, 255))
            from PIL import ImageDraw

            draw = ImageDraw.Draw(icon)
            draw.ellipse([8, 8, 56, 56], fill=(40, 42, 54, 255))
            draw.text((20, 18), "L", fill=(189, 147, 249, 255))
            return icon
        except Exception as e:
            logger.error(f"[TRAY] Erro ao criar icone fallback: {e}")
            return Image.new("RGBA", (64, 64), (189, 147, 249, 255))

    def start(self) -> bool:
        if not PYSTRAY_AVAILABLE:
            logger.warning("[TRAY] pystray nao disponivel, tray desativado")
            return False

        if self._running:
            logger.warning("[TRAY] Ja esta rodando")
            return True

        try:
            image = self._load_icon()

            entity_name = get_entity_name(get_active_entity())
            self.icon = pystray.Icon(
                name=entity_name, icon=image, title=f"{entity_name} - Assistente IA", menu=self._create_menu()
            )

            self._thread = Thread(target=self._run_icon, daemon=True, name="TrayIconThread")
            self._running = True
            self._thread.start()

            logger.info("[TRAY] System tray iniciado")
            return True

        except Exception as e:
            logger.error(f"[TRAY] Erro ao iniciar: {e}")
            return False

    def _run_icon(self):
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"[TRAY] Erro no loop do icone: {e}")
        finally:
            self._running = False

    def stop(self):
        if self.icon and self._running:
            try:
                self.icon.stop()
                logger.info("[TRAY] System tray encerrado")
            except Exception as e:
                logger.error(f"[TRAY] Erro ao parar: {e}")
        self._running = False

    def notify(self, title: str, message: str):
        if self.icon and self._running:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                logger.debug(f"[TRAY] Erro ao notificar: {e}")

    def update_voice_state(self, enabled: bool):
        self._voice_enabled = enabled
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception as e:
                logger.debug(f"Erro ao atualizar menu do tray: {e}")

    @property
    def is_running(self) -> bool:
        return self._running
