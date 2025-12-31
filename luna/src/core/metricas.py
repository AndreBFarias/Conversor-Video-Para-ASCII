"""
Metricas - Sistema de metricas e profiling.

Monitora performance, latencia e uso de recursos:
- Decorators para instrumentacao automatica
- Trackers para API, latencia e filas
- Profilers para UI e performance geral

Classes principais:
    MetricsCollector: Coleta geral de metricas
    APIRequestTracker: Rastreamento de requests com circuit breaker
    LatencyTracker: Monitoramento de SLAs
    PerformanceProfiler: Profiling de operacoes

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/core/metricas/
"""

from src.core.metricas import (
    PERF_THRESHOLDS,
    APIDebugLogger,
    APIRequestTracker,
    LatencyTracker,
    MetricsCollector,
    PerformanceProfiler,
    QueueMetrics,
    TimerContext,
    UIProfiler,
    get_api_debug_logger,
    get_api_tracker,
    get_latency_tracker,
    get_metrics,
    get_perf_profiler,
    get_queue_metrics,
    get_ui_profiler,
    log_full_diagnostics,
    log_latency_report,
    log_performance_report,
    perf_monitor,
)

__all__ = [
    "PERF_THRESHOLDS",
    "perf_monitor",
    "APIDebugLogger",
    "MetricsCollector",
    "TimerContext",
    "APIRequestTracker",
    "UIProfiler",
    "PerformanceProfiler",
    "LatencyTracker",
    "QueueMetrics",
    "get_metrics",
    "get_api_tracker",
    "get_ui_profiler",
    "get_api_debug_logger",
    "get_perf_profiler",
    "get_latency_tracker",
    "get_queue_metrics",
    "log_performance_report",
    "log_latency_report",
    "log_full_diagnostics",
]
