import logging
from typing import TYPE_CHECKING

import config
from src.core.ambient_presence import create_ambient_presence, set_ambient_presence
from src.core.daemon import DaemonController
from src.core.event_logger import EventType, get_event_logger
from src.data_memory.proactive_system import get_proactive_system
from src.soul.personalidade import get_personalidade
from src.soul.reminders import get_reminder_manager
from src.ui.banner import run_startup_static
from src.ui.emotion_manager import patch_animation_controller
from src.ui.theme_manager import update_glitch_colors_for_entity

if TYPE_CHECKING:
    from .luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class LifecycleMixin:
    async def on_mount(self: "TemploDaAlma") -> None:
        logger.info("Montando interface grafica...")

        evt_logger = get_event_logger()
        evt_logger.log(EventType.SYSTEM, "app", "mount_start", {"app_state": self.app_state})

        self.animation_controller.load_all_animations()
        patch_animation_controller(self.animation_controller, self)

        from src.core.entity_loader import get_active_entity

        active_entity = get_active_entity()
        update_glitch_colors_for_entity(active_entity)
        self._apply_entity_styles_inline(active_entity)

        self.setup_threading()

        self._setup_reminders()
        self._setup_proactive()
        self._setup_ambient()
        self._setup_desktop_integration()

        if config.DAEMON_MODE:
            self.daemon = DaemonController(self)
            if self.daemon.setup():
                logger.info("Daemon mode ativado com system tray")

        personalidade = get_personalidade()
        placeholder_frase = personalidade.obter_frase("placeholder_input")
        try:
            from src.ui import MultilineInput

            main_input = self.query_one("#main_input", MultilineInput)
            main_input.placeholder = placeholder_frase
        except Exception as e:
            logger.debug(f"Erro ao configurar placeholder: {e}")

        await run_startup_static(self, duration=1.2)
        self.animation_controller.run_animation("observando")

        evt_logger.log(EventType.SYSTEM, "app", "ui_ready", {"animation": "observando"})

        if not self.skip_onboarding and self.onboarding.verify_first_run():
            logger.info("Detectada primeira execucao. Iniciando onboarding...")
            self.hide_ui_for_onboarding()
            self.run_worker(self.onboarding.start_sequence(), exclusive=True, thread=False)
        else:
            from src.core.entity_loader import get_active_entity
            from src.soul.entity_switch import get_entity_switch_intro

            entity_switch = get_entity_switch_intro(self)
            current_entity = get_active_entity()

            if entity_switch.needs_intro(current_entity):
                logger.info(f"Detectada troca de entidade. Iniciando introducao para {current_entity}...")
                self.run_worker(entity_switch.run_intro(current_entity), exclusive=True, thread=False)
            else:
                logger.info("Iniciando nova conversa automaticamente...")
                self.call_later(self.action_nova_conversa)

    def on_unmount(self: "TemploDaAlma") -> None:
        logger.info("Desmontando aplicacao e liberando recursos...")

        evt_logger = get_event_logger()
        evt_logger.log(EventType.SYSTEM, "app", "shutdown", {"app_state": self.app_state})
        evt_logger.save_session()

        if hasattr(self, "threading_manager") and self.threading_manager:
            try:
                logger.info("Sinalizando shutdown para threads...")
                self.threading_manager.shutdown_event.set()
                self.threading_manager.stop_all_threads(timeout=3.0)
                logger.info("Threads finalizadas.")
            except Exception as e:
                logger.error(f"Erro ao parar threads: {e}")

        if self.ouvido:
            try:
                self.ouvido.close()
                logger.info("Ouvido encerrado.")
            except Exception as e:
                logger.error(f"Erro ao fechar ouvido: {e}")

        if self.visao:
            try:
                self.visao.release()
                logger.info("Visao liberada.")
            except Exception as e:
                logger.error(f"Erro ao liberar visao: {e}")

            try:
                vision_stats = self.visao.get_vision_stats()
                logger.info(f"QUOTA STATS - Vision: {vision_stats}")
            except Exception as e:
                logger.debug(f"Erro ao obter vision stats: {e}")

        if self.consciencia:
            try:
                optimizer_stats = self.consciencia.get_optimizer_stats()
                if optimizer_stats:
                    logger.info(f"QUOTA STATS - API Optimizer: {optimizer_stats}")
            except Exception as e:
                logger.debug(f"Erro ao obter optimizer stats: {e}")

        if hasattr(self, "ambient") and self.ambient:
            try:
                self.ambient.stop()
                logger.info("Presenca ambiental encerrada.")
            except Exception as e:
                logger.error(f"Erro ao parar presenca ambiental: {e}")

    def _setup_reminders(self: "TemploDaAlma") -> None:
        reminder_manager = get_reminder_manager()

        def on_reminder_triggered(reminder):
            from src.core.entity_loader import get_entity_name

            entity_name = get_entity_name(reminder.entity_id)

            response = {
                "fala_tts": f"Lembrete: {reminder.message}",
                "leitura": "Tom suave e atencioso",
                "log_terminal": f"[Lembrete] {reminder.message}",
                "animacao": f"{entity_name}_curiosa",
                "comando_visao": False,
                "tts_config": {"speed": 1.0, "stability": 0.5},
                "registrar_rosto": None,
                "filesystem_ops": [],
            }

            self.threading_manager.result_queue.put(("response", response))
            logger.info(f"Lembrete disparado: {reminder.message}")

        reminder_manager.register_callback(on_reminder_triggered)
        reminder_manager.start_checking()
        logger.info("Sistema de lembretes inicializado")

    def _setup_proactive(self: "TemploDaAlma") -> None:
        from src.core.entity_loader import get_active_entity, get_entity_name

        try:
            entity_id = get_active_entity()
            proactive = get_proactive_system(entity_id)
            triggers = proactive.check_triggers()

            if triggers:
                main_trigger = triggers[0]
                entity_name = get_entity_name(entity_id)

                response = {
                    "fala_tts": main_trigger.message,
                    "leitura": "Tom carinhoso e atencioso",
                    "log_terminal": f"[{entity_name} proativa] {main_trigger.message}",
                    "animacao": f"{entity_name}_curiosa",
                    "comando_visao": False,
                    "tts_config": {"speed": 1.0, "stability": 0.5},
                    "registrar_rosto": None,
                    "filesystem_ops": [],
                }

                self.call_later(
                    lambda: self.threading_manager.result_queue.put(("response", response)),
                    delay=2.0,
                )

                logger.info(f"Trigger proativo agendado: {main_trigger.trigger_type}")

        except Exception as e:
            logger.debug(f"Erro ao verificar triggers proativos: {e}")

    def _setup_ambient(self: "TemploDaAlma") -> None:
        try:
            self.ambient = create_ambient_presence(self)
            set_ambient_presence(self.ambient)
            self.ambient.start()
            logger.info("Presenca ambiental iniciada")
        except Exception as e:
            logger.error(f"Erro ao inicializar presenca ambiental: {e}")

    def _setup_desktop_integration(self: "TemploDaAlma") -> None:
        if not config.DESKTOP_INTEGRATION.get("enabled", False):
            logger.info("Desktop integration desabilitada")
            return

        try:
            from src.core.desktop_integration import DesktopEvent, get_desktop_integration

            self.desktop_integration = get_desktop_integration()

            for feature, enabled in config.DESKTOP_INTEGRATION.items():
                if feature in ["notifications", "clipboard", "active_window", "idle_detection", "proactivity"]:
                    self.desktop_integration.set_feature(feature, enabled)

            def on_proactive_speak(message: str):
                from src.core.entity_loader import get_active_entity, get_entity_name

                entity_name = get_entity_name(get_active_entity())

                response = {
                    "fala_tts": message,
                    "leitura": "Tom casual e amigavel",
                    "log_terminal": f"[{entity_name} proativa] {message}",
                    "animacao": f"{entity_name}_curiosa",
                    "comando_visao": False,
                    "tts_config": {"speed": 1.0, "stability": 0.5},
                    "registrar_rosto": None,
                    "filesystem_ops": [],
                }
                self.threading_manager.result_queue.put(("response", response))

            def on_notification(data):
                logger.debug(f"Notificacao recebida: {data.app_name} - {data.summary}")

            def on_idle_start():
                logger.info("Usuario ficou inativo")

            def on_idle_end():
                logger.info("Usuario retornou")

            self.desktop_integration.register_callback(DesktopEvent.NOTIFICATION, on_notification)
            self.desktop_integration.register_callback(DesktopEvent.IDLE_START, on_idle_start)
            self.desktop_integration.register_callback(DesktopEvent.IDLE_END, on_idle_end)

            self.desktop_integration.setup(
                idle_threshold=config.DESKTOP_INTEGRATION.get("idle_threshold", 300),
                proactive_interval=config.DESKTOP_INTEGRATION.get("proactive_interval", 30),
                luna_speak_callback=on_proactive_speak if config.DESKTOP_INTEGRATION.get("proactivity") else None,
            )

            self.desktop_integration.start()
            logger.info("Desktop integration iniciada")

        except Exception as e:
            logger.error(f"Erro ao inicializar desktop integration: {e}")
