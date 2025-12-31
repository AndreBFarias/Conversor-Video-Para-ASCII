from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.metricas.api_tracker import APIRequestTracker
    from src.core.metricas.collector import MetricsCollector
    from src.core.metricas.debug_logger import APIDebugLogger
    from src.core.metricas.latency import LatencyTracker
    from src.core.metricas.perf_profiler import PerformanceProfiler
    from src.core.metricas.queue_metrics import QueueMetrics
    from src.core.metricas.ui_profiler import UIProfiler

logger = logging.getLogger(__name__)

_global_metrics = None
_global_api_tracker = None
_global_ui_profiler = None
_global_perf_profiler = None
_global_latency_tracker = None
_global_queue_metrics = None
_global_api_debug_logger = None


def get_metrics() -> "MetricsCollector":
    global _global_metrics
    if _global_metrics is None:
        from src.core.metricas.collector import MetricsCollector

        _global_metrics = MetricsCollector()
    return _global_metrics


def get_api_tracker() -> "APIRequestTracker":
    global _global_api_tracker
    if _global_api_tracker is None:
        from src.core.metricas.api_tracker import APIRequestTracker

        _global_api_tracker = APIRequestTracker()
    return _global_api_tracker


def get_ui_profiler() -> "UIProfiler":
    global _global_ui_profiler
    if _global_ui_profiler is None:
        from src.core.metricas.ui_profiler import UIProfiler

        _global_ui_profiler = UIProfiler()
    return _global_ui_profiler


def get_api_debug_logger() -> "APIDebugLogger":
    global _global_api_debug_logger
    if _global_api_debug_logger is None:
        from src.core.metricas.debug_logger import APIDebugLogger

        _global_api_debug_logger = APIDebugLogger()
    return _global_api_debug_logger


def get_perf_profiler() -> "PerformanceProfiler":
    global _global_perf_profiler
    if _global_perf_profiler is None:
        from src.core.metricas.perf_profiler import PerformanceProfiler

        _global_perf_profiler = PerformanceProfiler()
    return _global_perf_profiler


def get_latency_tracker() -> "LatencyTracker":
    global _global_latency_tracker
    if _global_latency_tracker is None:
        from src.core.metricas.latency import LatencyTracker

        _global_latency_tracker = LatencyTracker()
    return _global_latency_tracker


def get_queue_metrics() -> "QueueMetrics":
    global _global_queue_metrics
    if _global_queue_metrics is None:
        from src.core.metricas.queue_metrics import QueueMetrics

        _global_queue_metrics = QueueMetrics()
    return _global_queue_metrics


def log_performance_report():
    profiler = get_perf_profiler()
    report = profiler.generate_report()
    logger.info(report)
    return report


def log_latency_report():
    tracker = get_latency_tracker()
    report = tracker.generate_report()
    logger.info(report)
    return report


def log_full_diagnostics():
    logger.info("=" * 60)
    logger.info("LUNA DIAGNOSTICS REPORT")
    logger.info("=" * 60)

    log_performance_report()
    log_latency_report()

    queue_stats = get_queue_metrics().get_stats()
    if queue_stats:
        logger.info("\nQUEUE METRICS:")
        for q, data in queue_stats.items():
            logger.info(
                f"  {q}: avg_wait={data['avg_wait']:.3f}s drops={data['drops']} drop_rate={data['drop_rate']:.1%}"
            )

    api_stats = get_api_tracker().get_stats()
    logger.info(
        f"\nAPI: {api_stats['successful']}/{api_stats['total_requests']} ok, avg={api_stats['avg_duration']:.2f}s"
    )

    logger.info("=" * 60)
