from __future__ import annotations

import logging
import time
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class UIProfiler:
    def __init__(self):
        self.lock = Lock()
        self.element_loads = {}
        self.render_times = []

        logger.info("UIProfiler inicializado")

    def log_element_loaded(self, element_id: str, load_time: float = None):
        with self.lock:
            self.element_loads[element_id] = {"timestamp": datetime.now().isoformat(), "load_time": load_time}
        logger.debug(f"UI Element carregado: {element_id}")

    def log_render_time(self, component: str, duration: float):
        with self.lock:
            self.render_times.append({"component": component, "duration": duration, "timestamp": time.time()})
        if duration > 0.1:
            logger.warning(f"Render lento: {component} ({duration:.3f}s)")

    def get_stats(self) -> dict:
        with self.lock:
            return {
                "elements_loaded": len(self.element_loads),
                "total_renders": len(self.render_times),
                "avg_render_time": sum(r["duration"] for r in self.render_times) / max(len(self.render_times), 1),
            }
