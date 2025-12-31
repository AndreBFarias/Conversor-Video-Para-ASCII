from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime
from threading import Lock

from src.core.metricas.decorators import PERF_THRESHOLDS


class PerformanceProfiler:
    def __init__(self, window_size: int = 100):
        self.lock = Lock()
        self.window_size = window_size
        self.samples: dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.slow_operations: deque = deque(maxlen=50)

    def record(self, operation: str, duration: float, metadata: dict = None):
        with self.lock:
            sample = {"timestamp": time.time(), "duration": duration, "metadata": metadata or {}}
            self.samples[operation].append(sample)

            if duration > PERF_THRESHOLDS["slow"]:
                self.slow_operations.append(
                    {
                        "operation": operation,
                        "duration": duration,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata or {},
                    }
                )

    def get_stats(self, operation: str = None) -> dict:
        with self.lock:
            if operation:
                samples = list(self.samples.get(operation, []))
                if not samples:
                    return {}
                durations = [s["duration"] for s in samples]
                return {
                    "operation": operation,
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
                }

            stats = {}
            for op, samples_deque in self.samples.items():
                samples = list(samples_deque)
                if samples:
                    durations = [s["duration"] for s in samples]
                    stats[op] = {
                        "count": len(durations),
                        "avg": sum(durations) / len(durations),
                        "min": min(durations),
                        "max": max(durations),
                    }
            return stats

    def get_slow_operations(self) -> list:
        with self.lock:
            return list(self.slow_operations)

    def generate_report(self) -> str:
        stats = self.get_stats()
        slow_ops = self.get_slow_operations()

        lines = ["=" * 50, "PERFORMANCE REPORT", "=" * 50, ""]

        if stats:
            lines.append("OPERATION STATS:")
            for op, data in sorted(stats.items(), key=lambda x: x[1]["avg"], reverse=True):
                lines.append(f"  {op}:")
                lines.append(
                    f"    avg: {data['avg']:.3f}s | min: {data['min']:.3f}s | max: {data['max']:.3f}s | count: {data['count']}"
                )
            lines.append("")

        if slow_ops:
            lines.append(f"SLOW OPERATIONS (last {len(slow_ops)}):")
            for op in slow_ops[-10:]:
                lines.append(f"  [{op['timestamp']}] {op['operation']}: {op['duration']:.3f}s")
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)
