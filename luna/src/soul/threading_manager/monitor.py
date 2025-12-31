from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import LunaThreadingManager

logger = logging.getLogger(__name__)


class MonitorThread:
    def __init__(self, manager: LunaThreadingManager, interval: float = 30.0):
        self.manager = manager
        self.interval = interval

    def run(self):
        logger.info(f"Monitor thread iniciado (intervalo: {self.interval}s)")

        while not self.manager.shutdown_event.wait(timeout=self.interval):
            try:
                health = self.manager.health_check()

                if not health["healthy"]:
                    logger.warning(f"Health check falhou: {health['warnings']}")

                dead_threads = [
                    name for name, info in health["threads"].items() if info["state"] == "running" and not info["alive"]
                ]

                if dead_threads:
                    logger.error(f"Threads mortas detectadas: {dead_threads}")

                if health["warnings"]:
                    logger.warning(f"Filas transbordando: {health['warnings']}")

            except Exception as e:
                logger.error(f"Erro no monitor: {e}", exc_info=True)

        logger.info("Monitor thread finalizado")
