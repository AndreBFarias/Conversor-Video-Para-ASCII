from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.metricas.collector import MetricsCollector

logger = logging.getLogger(__name__)

PERF_THRESHOLDS = {
    "slow": 1.0,
    "very_slow": 3.0,
    "critical": 10.0,
}


def perf_monitor(metric_name: str = None, log_args: bool = False):
    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            from src.core.metricas.singletons import get_metrics

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start

                metrics = get_metrics()
                metrics.record_time(name, elapsed)
                metrics.record_success(name)

                if elapsed > PERF_THRESHOLDS["critical"]:
                    logger.error(f"PERF CRITICAL: {name} took {elapsed:.3f}s")
                elif elapsed > PERF_THRESHOLDS["very_slow"]:
                    logger.warning(f"PERF SLOW: {name} took {elapsed:.3f}s")
                elif elapsed > PERF_THRESHOLDS["slow"]:
                    logger.info(f"PERF: {name} took {elapsed:.3f}s")

                return result

            except Exception as e:
                elapsed = time.perf_counter() - start
                metrics = get_metrics()
                metrics.record_time(name, elapsed)
                metrics.record_failure(name)
                logger.error(f"PERF FAIL: {name} failed after {elapsed:.3f}s - {e}")
                raise

        return wrapper

    return decorator
