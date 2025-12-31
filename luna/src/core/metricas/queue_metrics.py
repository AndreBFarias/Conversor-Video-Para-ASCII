from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock


class QueueMetrics:
    def __init__(self):
        self.lock = Lock()
        self._wait_times: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._drops: dict[str, int] = defaultdict(int)
        self._puts: dict[str, int] = defaultdict(int)

    def record_wait(self, queue_name: str, wait_time: float):
        with self.lock:
            self._wait_times[queue_name].append(wait_time)

    def record_drop(self, queue_name: str):
        with self.lock:
            self._drops[queue_name] += 1

    def record_put(self, queue_name: str):
        with self.lock:
            self._puts[queue_name] += 1

    def get_stats(self) -> dict:
        with self.lock:
            stats = {}
            for queue_name in set(self._wait_times.keys()) | set(self._drops.keys()):
                waits = list(self._wait_times.get(queue_name, []))
                drops = self._drops.get(queue_name, 0)
                puts = self._puts.get(queue_name, 0)
                stats[queue_name] = {
                    "avg_wait": sum(waits) / len(waits) if waits else 0,
                    "max_wait": max(waits) if waits else 0,
                    "drops": drops,
                    "puts": puts,
                    "drop_rate": drops / max(puts, 1),
                }
            return stats
