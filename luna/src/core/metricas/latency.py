from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)


class LatencyTracker:
    def __init__(self):
        self.lock = Lock()
        self._latencies: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._targets = {
            "stt": 0.8,
            "llm": 2.0,
            "tts_generate": 3.0,
            "tts_playback": 0.5,
            "total_response": 5.0,
            "queue_wait": 0.1,
        }
        logger.info("LatencyTracker inicializado")

    def record(self, metric: str, latency: float, metadata: dict = None):
        with self.lock:
            self._latencies[metric].append({"value": latency, "timestamp": time.time(), "metadata": metadata or {}})

        target = self._targets.get(metric)
        if target and latency > target:
            logger.warning(f"[LATENCY] {metric}: {latency:.2f}s (target: {target}s)")
        else:
            logger.debug(f"[LATENCY] {metric}: {latency:.2f}s")

    def get_stats(self, metric: str = None) -> dict:
        with self.lock:
            if metric:
                samples = list(self._latencies.get(metric, []))
                if not samples:
                    return {}
                values = [s["value"] for s in samples]
                target = self._targets.get(metric, 0)
                over_target = sum(1 for v in values if v > target) if target else 0
                return {
                    "metric": metric,
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
                    "target": target,
                    "over_target_pct": over_target / len(values) * 100 if values else 0,
                }

            stats = {}
            for m, samples_deque in self._latencies.items():
                samples = list(samples_deque)
                if samples:
                    values = [s["value"] for s in samples]
                    target = self._targets.get(m, 0)
                    over_target = sum(1 for v in values if v > target) if target else 0
                    stats[m] = {
                        "count": len(values),
                        "avg": round(sum(values) / len(values), 3),
                        "max": round(max(values), 3),
                        "target": target,
                        "over_target_pct": round(over_target / len(values) * 100, 1) if values else 0,
                    }
            return stats

    def get_health_status(self) -> dict:
        stats = self.get_stats()
        issues = []

        for metric, data in stats.items():
            if data.get("over_target_pct", 0) > 20:
                issues.append(f"{metric}: {data['over_target_pct']:.1f}% over target")

        return {"healthy": len(issues) == 0, "issues": issues, "stats": stats}

    def generate_report(self) -> str:
        stats = self.get_stats()
        lines = ["=" * 50, "LATENCY REPORT", "=" * 50, ""]

        if stats:
            lines.append(f"{'Metric':<20} {'Avg':>8} {'Max':>8} {'Target':>8} {'Over%':>8}")
            lines.append("-" * 52)
            for metric, data in sorted(stats.items()):
                lines.append(
                    f"{metric:<20} {data['avg']:>7.2f}s {data['max']:>7.2f}s "
                    f"{data['target']:>7.1f}s {data['over_target_pct']:>7.1f}%"
                )
        else:
            lines.append("Nenhuma metrica de latencia registrada.")

        lines.append("")
        lines.append("=" * 50)
        return "\n".join(lines)
