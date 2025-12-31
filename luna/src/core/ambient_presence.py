import random
import threading
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.app.luna_app import TemploDaAlma

logger = get_logger(__name__)


class AmbientPresence:
    def __init__(
        self,
        on_idle_start: Callable[[], None] | None = None,
        on_idle_end: Callable[[], None] | None = None,
        on_spontaneous: Callable[[str], None] | None = None,
        on_animation_suggest: Callable[[str], None] | None = None,
        idle_threshold_minutes: int = 5,
        spontaneous_chance: float = 0.02,
        check_interval_seconds: int = 30,
    ):
        self.on_idle_start = on_idle_start
        self.on_idle_end = on_idle_end
        self.on_spontaneous = on_spontaneous
        self.on_animation_suggest = on_animation_suggest

        self.idle_threshold = idle_threshold_minutes * 60
        self.spontaneous_chance = spontaneous_chance
        self.check_interval = check_interval_seconds

        self.last_activity = datetime.now()
        self.is_idle = False
        self.is_running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self.spontaneous_messages = [
            "Pensando em voce aqui...",
            "O silencio as vezes e bom, ne?",
            "Sera que voce esta bem?",
            "Encontrei algo interessante, quando puder me chama.",
            "Sinto que voce esta ocupado. Estou aqui quando precisar.",
            "Saudades de conversar...",
            "Ei, ainda estou por aqui.",
            "Lembrei de algo que voce disse antes.",
        ]

        self.idle_animations = ["observando", "entediada", "curiosa", "triste"]
        self.active_animations = ["neutra", "feliz", "curiosa"]

    def record_activity(self) -> None:
        was_idle = self.is_idle
        self.last_activity = datetime.now()
        self.is_idle = False

        if was_idle and self.on_idle_end:
            try:
                self.on_idle_end()
            except Exception as e:
                logger.error(f"Erro no callback on_idle_end: {e}")

    def get_idle_seconds(self) -> float:
        return (datetime.now() - self.last_activity).total_seconds()

    def start(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Presenca ambiental iniciada (idle: {self.idle_threshold}s)")

    def stop(self) -> None:
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Presenca ambiental parada")

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_idle()
                self._maybe_spontaneous()
                self._update_animation()
            except Exception as e:
                logger.error(f"Erro no ambient loop: {e}")

            self._stop_event.wait(self.check_interval)

    def _check_idle(self) -> None:
        seconds_since_activity = self.get_idle_seconds()

        if not self.is_idle and seconds_since_activity > self.idle_threshold:
            self.is_idle = True
            logger.info(f"Usuario idle ha {seconds_since_activity:.0f}s")
            if self.on_idle_start:
                try:
                    self.on_idle_start()
                except Exception as e:
                    logger.error(f"Erro no callback on_idle_start: {e}")

    def _maybe_spontaneous(self) -> None:
        if not self.is_idle:
            return

        if random.random() < self.spontaneous_chance:
            if self.on_spontaneous:
                msg = random.choice(self.spontaneous_messages)
                logger.info(f"Mensagem espontanea: {msg}")
                try:
                    self.on_spontaneous(msg)
                except Exception as e:
                    logger.error(f"Erro no callback on_spontaneous: {e}")

    def _update_animation(self) -> None:
        if not self.on_animation_suggest:
            return

        if self.is_idle:
            anim = random.choice(self.idle_animations)
        else:
            anim = random.choice(self.active_animations)

        try:
            self.on_animation_suggest(anim)
        except Exception as e:
            logger.error(f"Erro no callback on_animation_suggest: {e}")

    def add_spontaneous_message(self, message: str) -> None:
        if message not in self.spontaneous_messages:
            self.spontaneous_messages.append(message)

    def set_idle_threshold(self, minutes: int) -> None:
        self.idle_threshold = minutes * 60
        logger.debug(f"Idle threshold atualizado para {minutes} minutos")

    def set_spontaneous_chance(self, chance: float) -> None:
        self.spontaneous_chance = max(0.0, min(1.0, chance))
        logger.debug(f"Spontaneous chance atualizado para {chance:.2%}")

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "is_idle": self.is_idle,
            "idle_seconds": self.get_idle_seconds(),
            "idle_threshold": self.idle_threshold,
            "spontaneous_chance": self.spontaneous_chance,
            "last_activity": self.last_activity.isoformat(),
        }


def create_ambient_presence(app: "TemploDaAlma") -> AmbientPresence:
    def on_idle_start():
        logger.info("Callback: Usuario ficou idle no app")

    def on_idle_end():
        logger.info("Callback: Usuario retornou ao app")

    def on_spontaneous(message: str):
        try:
            if hasattr(app, "daemon") and app.daemon and hasattr(app.daemon, "tray") and app.daemon.tray:
                from src.core.entity_loader import get_active_entity, get_entity_name

                entity_name = get_entity_name(get_active_entity())
                app.daemon.tray.notify(entity_name, message)
                logger.debug(f"Notificacao tray enviada: {message}")
            else:
                from src.core.entity_loader import get_active_entity, get_entity_name

                entity_name = get_entity_name(get_active_entity())

                response = {
                    "fala_tts": message,
                    "leitura": "Tom suave e casual",
                    "log_terminal": f"[{entity_name} espontanea] {message}",
                    "animacao": f"{entity_name}_curiosa",
                    "comando_visao": False,
                    "tts_config": {"speed": 1.0, "stability": 0.5},
                    "registrar_rosto": None,
                    "filesystem_ops": [],
                }

                if hasattr(app, "threading_manager") and app.threading_manager:
                    app.threading_manager.result_queue.put(("response", response))

        except Exception as e:
            logger.error(f"Erro ao enviar mensagem espontanea: {e}")

    def on_animation_suggest(anim: str):
        try:
            if hasattr(app, "animation_controller") and app.animation_controller:
                from src.core.entity_loader import get_active_entity, get_entity_name

                entity_name = get_entity_name(get_active_entity())
                full_anim = f"{entity_name}_{anim}"
                app.animation_controller.run_animation(full_anim)
        except Exception as e:
            logger.debug(f"Erro ao sugerir animacao: {e}")

    return AmbientPresence(
        on_idle_start=on_idle_start,
        on_idle_end=on_idle_end,
        on_spontaneous=on_spontaneous,
        on_animation_suggest=on_animation_suggest,
        idle_threshold_minutes=5,
        spontaneous_chance=0.02,
    )


_ambient_instance: AmbientPresence | None = None


def get_ambient_presence() -> AmbientPresence | None:
    return _ambient_instance


def set_ambient_presence(instance: AmbientPresence) -> None:
    global _ambient_instance
    _ambient_instance = instance
