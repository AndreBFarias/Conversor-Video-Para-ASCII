import logging
import time
from collections import deque
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class SmartRateLimiter:
    def __init__(self, quota_limit: int = 60, safety_margin: int = 10):
        self.quota_limit = quota_limit
        self.safety_margin = safety_margin
        self.requests: deque = deque()
        self._lock = Lock()
        self._effective_limit = quota_limit - safety_margin

    def _cleanup_old_requests(self):
        now = time.time()
        cutoff = now - 60
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

    def should_wait(self) -> float:
        with self._lock:
            self._cleanup_old_requests()

            current_count = len(self.requests)

            if current_count == 0:
                return 0.0

            if current_count >= self._effective_limit:
                oldest = self.requests[0]
                wait_time = 60 - (time.time() - oldest)
                return max(0.0, wait_time + 1.0)

            return 0.0

    def record_request(self):
        with self._lock:
            self.requests.append(time.time())

    def get_usage(self) -> tuple[int, int]:
        with self._lock:
            self._cleanup_old_requests()
            return len(self.requests), self.quota_limit

    def can_request_now(self) -> tuple[bool, float]:
        wait_time = self.should_wait()
        return wait_time == 0.0, wait_time

    def wait_if_needed(self) -> float:
        wait_time = self.should_wait()

        if wait_time > 0:
            logger.warning(
                f"Rate limit: aguardando {wait_time:.1f}s ({len(self.requests)}/{self._effective_limit} RPM)"
            )
            time.sleep(wait_time)

        self.record_request()
        return wait_time

    def get_remaining_quota(self) -> int:
        with self._lock:
            self._cleanup_old_requests()
            return max(0, self._effective_limit - len(self.requests))


class RequestDeduplicator:
    def __init__(self, window_seconds: int = 120):
        self.window_seconds = window_seconds
        self.recent_requests: dict = {}
        self._lock = Lock()

    def _cleanup_old(self):
        now = time.time()
        cutoff = now - self.window_seconds
        expired = [k for k, v in self.recent_requests.items() if v["timestamp"] < cutoff]
        for k in expired:
            del self.recent_requests[k]

    def is_duplicate(self, request_hash: str) -> bool:
        with self._lock:
            self._cleanup_old()
            return request_hash in self.recent_requests

    def get_cached(self, request_hash: str) -> Any | None:
        with self._lock:
            self._cleanup_old()

            if request_hash in self.recent_requests:
                entry = self.recent_requests[request_hash]
                logger.info(f"Dedup HIT: {request_hash[:8]} (age: {time.time() - entry['timestamp']:.0f}s)")
                return entry.get("response")

            return None

    def record(self, request_hash: str, response: any):
        with self._lock:
            self._cleanup_old()

            self.recent_requests[request_hash] = {"timestamp": time.time(), "response": response}

            logger.debug(f"Dedup recorded: {request_hash[:8]} (total: {len(self.recent_requests)})")

    def get_stats(self) -> dict:
        with self._lock:
            self._cleanup_old()
            return {"cached_requests": len(self.recent_requests), "window_seconds": self.window_seconds}
