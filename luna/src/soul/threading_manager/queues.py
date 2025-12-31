import logging
import queue
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)


class RingBuffer:
    def __init__(self, maxsize: int = 100, name: str = "buffer"):
        self.maxsize = maxsize
        self.name = name
        self._buffer: deque = deque(maxlen=maxsize)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._drops = 0
        self._total_puts = 0

    def put(self, item, block: bool = True, timeout: float = None) -> bool:
        with self._lock:
            self._total_puts += 1
            was_full = len(self._buffer) >= self.maxsize
            if was_full:
                self._drops += 1
            self._buffer.append(item)
            self._not_empty.notify()
            return not was_full

    def put_nowait(self, item) -> bool:
        return self.put(item, block=False)

    def get(self, block: bool = True, timeout: float = None):
        with self._not_empty:
            if not block:
                if not self._buffer:
                    raise queue.Empty
                return self._buffer.popleft()

            end_time = time.time() + timeout if timeout else None
            while not self._buffer:
                remaining = end_time - time.time() if end_time else None
                if remaining is not None and remaining <= 0:
                    raise queue.Empty
                self._not_empty.wait(timeout=remaining)
            return self._buffer.popleft()

    def get_nowait(self):
        return self.get(block=False)

    def qsize(self) -> int:
        with self._lock:
            return len(self._buffer)

    def empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0

    def full(self) -> bool:
        with self._lock:
            return len(self._buffer) >= self.maxsize

    def clear(self) -> int:
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._buffer),
                "maxsize": self.maxsize,
                "drops": self._drops,
                "total_puts": self._total_puts,
                "drop_rate": self._drops / max(self._total_puts, 1),
            }


class BackpressureQueue:
    def __init__(self, maxsize: int = 50, name: str = "queue", drop_oldest: bool = True):
        self.maxsize = maxsize
        self.name = name
        self.drop_oldest = drop_oldest
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._drops = 0
        self._total_puts = 0
        self._high_watermark = int(maxsize * 0.8)
        self._low_watermark = int(maxsize * 0.5)
        self._backpressure_active = False

    def put(self, item, block: bool = True, timeout: float = None) -> bool:
        with self._lock:
            self._total_puts += 1

            if len(self._queue) >= self.maxsize:
                if self.drop_oldest:
                    self._queue.popleft()
                    self._drops += 1
                    logger.debug(f"[{self.name}] Backpressure: descartou item antigo (total drops: {self._drops})")
                else:
                    self._drops += 1
                    logger.debug(f"[{self.name}] Backpressure: descartou item novo (total drops: {self._drops})")
                    return False

            self._queue.append(item)

            if len(self._queue) >= self._high_watermark and not self._backpressure_active:
                self._backpressure_active = True
                logger.warning(f"[{self.name}] HIGH WATERMARK atingido ({len(self._queue)}/{self.maxsize})")

            self._not_empty.notify()
            return True

    def put_nowait(self, item) -> bool:
        return self.put(item, block=False)

    def get(self, block: bool = True, timeout: float = None):
        with self._not_empty:
            if not block:
                if not self._queue:
                    raise queue.Empty
                item = self._queue.popleft()
                self._check_low_watermark()
                return item

            end_time = time.time() + timeout if timeout else None
            while not self._queue:
                remaining = end_time - time.time() if end_time else None
                if remaining is not None and remaining <= 0:
                    raise queue.Empty
                self._not_empty.wait(timeout=remaining)

            item = self._queue.popleft()
            self._check_low_watermark()
            return item

    def _check_low_watermark(self):
        if self._backpressure_active and len(self._queue) <= self._low_watermark:
            self._backpressure_active = False
            logger.info(f"[{self.name}] LOW WATERMARK - backpressure desativado ({len(self._queue)}/{self.maxsize})")

    def get_nowait(self):
        return self.get(block=False)

    def qsize(self) -> int:
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0

    def full(self) -> bool:
        with self._lock:
            return len(self._queue) >= self.maxsize

    def clear(self) -> int:
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._backpressure_active = False
            return count

    def is_backpressure_active(self) -> bool:
        with self._lock:
            return self._backpressure_active

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._queue),
                "maxsize": self.maxsize,
                "drops": self._drops,
                "total_puts": self._total_puts,
                "drop_rate": self._drops / max(self._total_puts, 1),
                "backpressure_active": self._backpressure_active,
                "high_watermark": self._high_watermark,
                "low_watermark": self._low_watermark,
            }
