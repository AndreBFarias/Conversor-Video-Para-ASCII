from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import LunaProfiler

logger = logging.getLogger(__name__)


class PipelineLogger:
    def __init__(self, name: str = "luna"):
        from .core import get_profiler

        self.name = name
        self.profiler = get_profiler()
        self._interaction_id = 0

    def new_interaction(self, user_input: str = "") -> int:
        self._interaction_id = self.profiler.start_interaction(user_input)
        return self._interaction_id

    def log_stage(self, stage: str, message: str, **kwargs):
        log_entry = {
            "interaction": self._interaction_id,
            "stage": stage,
            "message": message,
            "thread": threading.current_thread().name,
            "timestamp": time.time(),
            **kwargs,
        }

        formatted = f"[{self._interaction_id:04d}] [{stage:15}] {message}"
        if kwargs:
            details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            formatted += f" | {details}"

        logger.info(formatted)

    def log_timing(self, stage: str, duration: float, **kwargs):
        self.log_stage(stage, f"completed in {duration*1000:.1f}ms", **kwargs)

    def end_interaction(self, response_preview: str = ""):
        self.profiler.end_interaction(response_preview)

    def get_diagnostics(self) -> str:
        return self.profiler.log_diagnostics()


_pipeline_logger = None


def get_pipeline_logger() -> PipelineLogger:
    global _pipeline_logger
    if _pipeline_logger is None:
        _pipeline_logger = PipelineLogger()
    return _pipeline_logger
