from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class VisionCache:
    def __init__(self, ttl: int = 120, max_entries: int = 20):
        self.cache: dict[str, dict] = {}
        self.ttl = ttl
        self.max_entries = max_entries

    def get(self, frame_hash: str) -> str | None:
        if frame_hash in self.cache:
            entry = self.cache[frame_hash]
            age = time.time() - entry["timestamp"]
            if age < self.ttl:
                return entry["description"]
            else:
                del self.cache[frame_hash]
        return None

    def set(self, frame_hash: str, description: str):
        self.cache[frame_hash] = {"timestamp": time.time(), "description": description}
        self._cleanup()

    def get_latest(self) -> str | None:
        if not self.cache:
            return None
        latest = max(self.cache.values(), key=lambda x: x["timestamp"])
        return latest["description"]

    def _cleanup(self):
        now = time.time()
        self.cache = {k: v for k, v in self.cache.items() if now - v["timestamp"] < self.ttl}
        while len(self.cache) > self.max_entries:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

    def clear(self):
        self.cache.clear()
