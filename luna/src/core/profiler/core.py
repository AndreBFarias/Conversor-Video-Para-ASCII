from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict

from .constants import LATENCY_THRESHOLDS, RECOMMENDATIONS
from .models import InteractionTrace, PipelineEvent, StageMetrics

logger = logging.getLogger(__name__)


class LunaProfiler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.events: deque = deque(maxlen=1000)
        self.stage_metrics: dict[str, StageMetrics] = {}
        self.active_spans: dict[str, float] = {}
        self.pipeline_start: float | None = None
        self.last_pipeline_duration: float = 0.0
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []

        self._current_interaction_id = 0
        self._interaction_traces: deque = deque(maxlen=50)
        self._current_trace: InteractionTrace | None = None

        self._alert_cooldown = 10.0
        self._diagnostics_enabled = True

        self._initialized = True
        logger.info("[PROFILER] LunaProfiler inicializado (v2 com diagnostico)")

    def enable_diagnostics(self, enabled: bool = True):
        self._diagnostics_enabled = enabled

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def _emit_event(self, event: PipelineEvent):
        with self._lock:
            self.events.append(event)

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.debug(f"Callback error: {e}")

    def _check_threshold(self, stage: str, duration: float):
        if not self._diagnostics_enabled:
            return

        threshold_ms = LATENCY_THRESHOLDS.get(stage, 1000)
        duration_ms = duration * 1000

        if duration_ms > threshold_ms:
            metrics = self.stage_metrics.get(stage)
            now = time.time()

            if metrics and (now - metrics.last_alert_time) > self._alert_cooldown:
                severity = "CRITICAL" if duration_ms > threshold_ms * 2 else "WARNING"
                logger.warning(
                    f"[PROFILER] [{severity}] {stage} excedeu threshold: "
                    f"{duration_ms:.1f}ms > {threshold_ms}ms (avg: {metrics.avg_time*1000:.1f}ms)"
                )
                metrics.last_alert_time = now

    def start_interaction(self, user_input: str = "") -> int:
        self._current_interaction_id += 1
        self._current_trace = InteractionTrace(
            interaction_id=self._current_interaction_id, start_time=time.time(), user_input=user_input[:100]
        )
        self.pipeline_start_time = time.time()
        self.mark("pipeline", "START", {"interaction_id": self._current_interaction_id})
        return self._current_interaction_id

    def end_interaction(self, response_preview: str = ""):
        if self._current_trace:
            self._current_trace.response_preview = response_preview[:100]
            self._current_trace.complete()

            logger.info(self._current_trace.to_timeline())
            self._interaction_traces.append(self._current_trace)
            self._current_trace = None

        if hasattr(self, "pipeline_start_time"):
            self.last_pipeline_duration = time.time() - self.pipeline_start_time
            self.mark(
                "pipeline",
                "END",
                {"total_duration": self.last_pipeline_duration, "interaction_id": self._current_interaction_id},
            )

            self._check_threshold("pipeline", self.last_pipeline_duration)

    def start_span(self, stage: str, metadata: dict = None) -> str:
        span_id = f"{stage}_{time.time()}_{self._current_interaction_id}"
        self.active_spans[span_id] = time.time()

        event = PipelineEvent(
            stage=stage,
            event_type="START",
            timestamp=time.time(),
            metadata=metadata or {},
            interaction_id=self._current_interaction_id,
        )
        self._emit_event(event)

        return span_id

    def end_span(self, span_id: str, metadata: dict = None):
        start_time = self.active_spans.pop(span_id, None)
        if start_time is None:
            return

        duration = time.time() - start_time
        parts = span_id.rsplit("_", 2)
        stage = parts[0] if len(parts) >= 1 else span_id

        if stage not in self.stage_metrics:
            self.stage_metrics[stage] = StageMetrics(stage=stage)
        self.stage_metrics[stage].record(duration)

        if self._current_trace:
            self._current_trace.add_stage(stage, duration, metadata)

        event = PipelineEvent(
            stage=stage,
            event_type="END",
            timestamp=time.time(),
            duration=duration,
            metadata=metadata or {},
            interaction_id=self._current_interaction_id,
        )
        self._emit_event(event)

        self._check_threshold(stage, duration)

    def mark(self, stage: str, event_type: str = "MARK", metadata: dict = None):
        event = PipelineEvent(
            stage=stage,
            event_type=event_type,
            timestamp=time.time(),
            metadata=metadata or {},
            interaction_id=self._current_interaction_id,
        )
        self._emit_event(event)

    def pipeline_start(self):
        self.pipeline_start_time = time.time()
        self.mark("pipeline", "START")

    def pipeline_end(self):
        if hasattr(self, "pipeline_start_time"):
            self.last_pipeline_duration = time.time() - self.pipeline_start_time
            self.mark("pipeline", "END", {"total_duration": self.last_pipeline_duration})

    @contextmanager
    def span(self, stage: str, metadata: dict = None):
        span_id = self.start_span(stage, metadata)
        try:
            yield span_id
        finally:
            self.end_span(span_id)

    def get_stage_summary(self) -> dict:
        summary = {}
        for stage, metrics in self.stage_metrics.items():
            threshold = LATENCY_THRESHOLDS.get(stage, 1000)
            avg_ms = metrics.avg_time * 1000
            status = "OK" if avg_ms < threshold else ("SLOW" if avg_ms < threshold * 2 else "CRITICAL")

            summary[stage] = {
                "count": metrics.count,
                "avg_ms": round(avg_ms, 2),
                "min_ms": round(metrics.min_time * 1000, 2) if metrics.min_time != float("inf") else 0,
                "max_ms": round(metrics.max_time * 1000, 2),
                "p50_ms": round(metrics.p50 * 1000, 2),
                "p95_ms": round(metrics.p95 * 1000, 2),
                "threshold_ms": threshold,
                "status": status,
            }
        return summary

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        with self._lock:
            events = list(self.events)[-limit:]
        return [asdict(e) for e in events]

    def get_bottlenecks(self, threshold_ms: float = None) -> list[dict]:
        bottlenecks = []
        for stage, metrics in self.stage_metrics.items():
            stage_threshold = threshold_ms or LATENCY_THRESHOLDS.get(stage, 500)
            avg_ms = metrics.avg_time * 1000

            if avg_ms > stage_threshold:
                severity = "CRITICAL" if avg_ms > stage_threshold * 2 else "WARNING"
                bottlenecks.append(
                    {
                        "stage": stage,
                        "avg_ms": round(avg_ms, 2),
                        "p50_ms": round(metrics.p50 * 1000, 2),
                        "p95_ms": round(metrics.p95 * 1000, 2),
                        "threshold_ms": stage_threshold,
                        "count": metrics.count,
                        "severity": severity,
                        "recommendation": RECOMMENDATIONS.get(stage, "Analise o estagio para identificar causa"),
                    }
                )
        return sorted(bottlenecks, key=lambda x: x["avg_ms"], reverse=True)

    def get_recent_traces(self, limit: int = 10) -> list[dict]:
        traces = list(self._interaction_traces)[-limit:]
        return [
            {
                "id": t.interaction_id,
                "duration_ms": round(t.total_duration * 1000, 2) if t.total_duration else None,
                "stages": t.stages,
                "user_input": t.user_input,
                "response_preview": t.response_preview,
            }
            for t in traces
        ]

    def log_summary(self):
        from . import diagnostics

        diagnostics.log_summary(self)

    def log_diagnostics(self) -> str:
        from . import diagnostics

        return diagnostics.log_diagnostics(self)

    def reset(self):
        with self._lock:
            self.events.clear()
            self.stage_metrics.clear()
            self.active_spans.clear()
            self._interaction_traces.clear()
            self._current_trace = None


def get_profiler() -> LunaProfiler:
    return LunaProfiler()
