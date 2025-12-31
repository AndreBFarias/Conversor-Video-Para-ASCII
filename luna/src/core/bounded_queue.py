import queue
import threading
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class BoundedQueue:
    def __init__(self, name: str, maxsize: int = 100, drop_oldest: bool = True):
        self.name = name
        self.maxsize = maxsize
        self.drop_oldest = drop_oldest
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._dropped_count = 0
        self._total_put = 0
        self._total_get = 0

    def put(self, item: Any, timeout: float | None = None) -> bool:
        self._total_put += 1

        try:
            self._queue.put_nowait(item)
            return True
        except queue.Full:
            if self.drop_oldest:
                with self._lock:
                    try:
                        self._queue.get_nowait()
                        self._dropped_count += 1
                        logger.warning(f"Queue {self.name}: dropped oldest item (total dropped: {self._dropped_count})")
                    except queue.Empty:
                        pass

                try:
                    self._queue.put_nowait(item)
                    return True
                except queue.Full:
                    return False
            else:
                logger.warning(f"Queue {self.name}: full, item rejected")
                return False

    def get(self, timeout: float | None = 1.0) -> Any | None:
        try:
            item = self._queue.get(timeout=timeout)
            self._total_get += 1
            return item
        except queue.Empty:
            return None

    def get_nowait(self) -> Any | None:
        try:
            item = self._queue.get_nowait()
            self._total_get += 1
            return item
        except queue.Empty:
            return None

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        return self._queue.full()

    def clear(self):
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "size": self.qsize(),
            "maxsize": self.maxsize,
            "dropped": self._dropped_count,
            "total_put": self._total_put,
            "total_get": self._total_get,
            "utilization": self.qsize() / self.maxsize if self.maxsize > 0 else 0,
        }


def create_bounded_queue(name: str, maxsize: int = 100, drop_oldest: bool = True) -> BoundedQueue:
    return BoundedQueue(name, maxsize, drop_oldest)
