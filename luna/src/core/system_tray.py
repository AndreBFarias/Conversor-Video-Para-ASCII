from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

try:
    import pystray
    from PIL import Image

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    pystray = None
    Image = None

import config
from src.core.logging_config import get_logger

logger = get_logger(__name__)

TrayCallback = Callable[[str], None]


class LunaTray:
    def __init__(self, app_callback: TrayCallback | None = None):
        self.app_callback = app_callback
        self.icon = None
        self._status = "idle"
        self._thread: threading.Thread | None = None

        if not TRAY_AVAILABLE:
            logger.warning("pystray/Pillow nao disponivel. Tray desabilitado.")
            return

        self._load_icon()
        self._create_menu()

    def _load_icon(self) -> None:
        if not TRAY_AVAILABLE:
            return

        icon_paths = [
            config.APP_DIR / "src" / "assets" / "icons" / "luna_tray.png",
            config.APP_DIR / "src" / "assets" / "icons" / "luna.png",
            config.APP_DIR / "src" / "assets" / "icons" / "icon.png",
        ]

        for path in icon_paths:
            if path.exists():
                try:
                    self.icon_image = Image.open(path)
                    self.icon_image = self.icon_image.resize((64, 64))
                    logger.debug(f"Icone carregado: {path}")
                    return
                except Exception as e:
                    logger.warning(f"Falha ao carregar icone {path}: {e}")

        self.icon_image = self._create_default_icon()

    def _create_default_icon(self) -> Image.Image:
        if not TRAY_AVAILABLE:
            return None

        img = Image.new("RGBA", (64, 64), (40, 42, 54, 255))

        try:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            draw.ellipse([16, 16, 48, 48], fill=(189, 147, 249, 255))
            draw.text((24, 22), "L", fill=(40, 42, 54, 255))
        except Exception:
            pass

        return img

    def _create_menu(self) -> None:
        if not TRAY_AVAILABLE:
            return

        self.menu = pystray.Menu(
            pystray.MenuItem("Nova Conversa", self._on_new_conversation),
            pystray.MenuItem("Configuracoes", self._on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Status",
                pystray.Menu(
                    pystray.MenuItem("Idle", lambda: self._set_status("idle")),
                    pystray.MenuItem("Listening", lambda: self._set_status("listening")),
                    pystray.MenuItem("Processing", lambda: self._set_status("processing")),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._on_quit),
        )

    def _on_new_conversation(self, icon=None, item=None) -> None:
        logger.info("Tray: Nova conversa solicitada")
        if self.app_callback:
            self.app_callback("new_conversation")

    def _on_settings(self, icon=None, item=None) -> None:
        logger.info("Tray: Configuracoes solicitadas")
        if self.app_callback:
            self.app_callback("settings")

    def _on_quit(self, icon=None, item=None) -> None:
        logger.info("Tray: Saida solicitada")
        if self.app_callback:
            self.app_callback("quit")
        self.stop()

    def _set_status(self, status: str) -> None:
        self._status = status
        logger.debug(f"Tray status: {status}")

    def start(self) -> None:
        if not TRAY_AVAILABLE:
            logger.info("Tray nao disponivel, pulando inicializacao")
            return

        if self.icon is not None:
            logger.warning("Tray ja iniciado")
            return

        try:
            self.icon = pystray.Icon(
                "Luna",
                self.icon_image,
                "Luna AI Assistant",
                self.menu,
            )

            self._thread = threading.Thread(target=self._run_icon, daemon=True)
            self._thread.start()
            logger.info("System tray iniciado")
        except Exception as e:
            logger.error(f"Falha ao iniciar tray: {e}")

    def _run_icon(self) -> None:
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Erro no tray loop: {e}")

    def stop(self) -> None:
        if self.icon:
            try:
                self.icon.stop()
                logger.info("System tray parado")
            except Exception as e:
                logger.error(f"Erro ao parar tray: {e}")
            finally:
                self.icon = None

    def update_status(self, status: str) -> None:
        self._status = status
        if self.icon:
            self.icon.title = f"Luna - {status.capitalize()}"

    def notify(self, title: str, message: str) -> None:
        if not TRAY_AVAILABLE or not self.icon:
            return

        try:
            self.icon.notify(message, title)
        except Exception as e:
            logger.debug(f"Notificacao nao suportada: {e}")

    @property
    def is_running(self) -> bool:
        return self.icon is not None and self._thread is not None and self._thread.is_alive()


_tray_instance: LunaTray | None = None


def get_tray(callback: TrayCallback | None = None) -> LunaTray | None:
    global _tray_instance

    if not TRAY_AVAILABLE:
        return None

    if _tray_instance is None:
        _tray_instance = LunaTray(callback)

    return _tray_instance


def reset_tray() -> None:
    global _tray_instance
    if _tray_instance:
        _tray_instance.stop()
    _tray_instance = None
