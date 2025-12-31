from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .constants import LATENCY_THRESHOLDS


@dataclass
class PipelineEvent:
    stage: str
    event_type: str
    timestamp: float
    duration: float | None = None
    metadata: dict = field(default_factory=dict)
    thread_name: str = ""
    interaction_id: int = 0

    def __post_init__(self):
        if not self.thread_name:
            self.thread_name = threading.current_thread().name


@dataclass
class StageMetrics:
    stage: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    samples: list[float] = field(default_factory=list)
    last_alert_time: float = 0.0

    @property
    def avg_time(self) -> float:
        return self.total_time / max(self.count, 1)

    @property
    def p95(self) -> float:
        if len(self.samples) < 5:
            return self.max_time
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[idx]

    @property
    def p50(self) -> float:
        if len(self.samples) < 2:
            return self.avg_time
        sorted_samples = sorted(self.samples)
        idx = len(sorted_samples) // 2
        return sorted_samples[idx]

    def record(self, duration: float):
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.samples.append(duration)
        if len(self.samples) > 100:
            self.samples = self.samples[-100:]


@dataclass
class InteractionTrace:
    interaction_id: int
    start_time: float
    stages: dict[str, dict] = field(default_factory=dict)
    end_time: float | None = None
    total_duration: float | None = None
    user_input: str = ""
    response_preview: str = ""

    def add_stage(self, stage: str, duration: float, metadata: dict = None):
        self.stages[stage] = {
            "duration_ms": round(duration * 1000, 2),
            "timestamp": time.time(),
            "metadata": metadata or {},
        }

    def complete(self):
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time

    def to_timeline(self) -> str:
        if not self.stages:
            return "No stages recorded"

        lines = [f"[INTERACTION #{self.interaction_id}] Timeline:"]
        total = 0
        for stage, data in self.stages.items():
            dur = data["duration_ms"]
            total += dur
            bar_len = min(int(dur / 100), 40)
            bar = "=" * bar_len
            threshold = LATENCY_THRESHOLDS.get(stage, 1000)
            status = "OK" if dur < threshold else "SLOW"
            lines.append(f"  {stage:20} | {dur:7.1f}ms |{bar}| [{status}]")

        if self.total_duration:
            lines.append(f"  {'TOTAL':20} | {self.total_duration*1000:7.1f}ms |")

        return "\n".join(lines)
