from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.lock = Lock()

        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.success_counts = defaultdict(int)
        self.failure_counts = defaultdict(int)

        logger.info("Sistema de metricas inicializado")

    def increment(self, metric_name: str, amount: int = 1):
        with self.lock:
            self.counters[metric_name] += amount
            logger.debug(f"{metric_name}: {self.counters[metric_name]}")

    def record_time(self, metric_name: str, duration: float):
        with self.lock:
            self.timers[metric_name].append(duration)
            logger.debug(f"{metric_name}: {duration:.3f}s")

    def record_success(self, metric_name: str):
        with self.lock:
            self.success_counts[metric_name] += 1
            logger.debug(f"{metric_name}: sucesso")

    def record_failure(self, metric_name: str):
        with self.lock:
            self.failure_counts[metric_name] += 1
            logger.debug(f"{metric_name}: falha")

    def get_average_time(self, metric_name: str) -> float:
        with self.lock:
            times = self.timers.get(metric_name, [])
            if not times:
                return 0.0
            return sum(times) / len(times)

    def get_success_rate(self, metric_name: str) -> float:
        with self.lock:
            successes = self.success_counts.get(metric_name, 0)
            failures = self.failure_counts.get(metric_name, 0)
            total = successes + failures
            if total == 0:
                return 0.0
            return successes / total

    def get_stats(self) -> dict:
        with self.lock:
            uptime = time.time() - self.start_time

            stats = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": round(uptime, 2),
                "uptime_formatted": self._format_uptime(uptime),
                "counters": dict(self.counters),
                "averages": {},
                "success_rates": {},
            }

            for metric_name, times in self.timers.items():
                if times:
                    stats["averages"][metric_name] = round(sum(times) / len(times), 3)

            all_metrics = set(self.success_counts.keys()) | set(self.failure_counts.keys())
            for metric_name in all_metrics:
                rate = self.get_success_rate(metric_name)
                stats["success_rates"][metric_name] = round(rate, 3)

            return stats

    def _format_uptime(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

    def log_summary(self):
        stats = self.get_stats()

        logger.info("=" * 40)
        logger.info("RESUMO DE METRICAS")
        logger.info("=" * 40)
        logger.info(f"Uptime: {stats['uptime_formatted']}")

        if stats["counters"]:
            logger.info("\nCONTADORES:")
            for metric, count in sorted(stats["counters"].items()):
                logger.info(f"  - {metric}: {count}")

        if stats["averages"]:
            logger.info("\nTEMPOS MEDIOS:")
            for metric, avg in sorted(stats["averages"].items()):
                logger.info(f"  - {metric}: {avg:.3f}s")

        if stats["success_rates"]:
            logger.info("\nTAXAS DE SUCESSO:")
            for metric, rate in sorted(stats["success_rates"].items()):
                percentage = rate * 100
                logger.info(f"  - {metric}: {percentage:.1f}%")

        logger.info("=" * 40)

    def save_to_file(self, filepath: str):
        try:
            stats = self.get_stats()
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            logger.info(f"Metricas salvas em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar metricas: {e}")


class TimerContext:
    def __init__(self, metrics: MetricsCollector, metric_name: str):
        self.metrics = metrics
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics.record_time(self.metric_name, duration)

        if exc_type is None:
            self.metrics.record_success(self.metric_name)
        else:
            self.metrics.record_failure(self.metric_name)
