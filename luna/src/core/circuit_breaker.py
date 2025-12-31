import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 30, half_open_requests: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.half_open_requests = half_open_requests

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.half_open_successes = 0

        self._lock = threading.Lock()

    def _should_attempt(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if self.last_failure_time and datetime.now() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_successes = 0
                    logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
                    return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                return True

            return False

    def _record_success(self):
        with self._lock:
            self.success_count += 1

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_successes += 1
                if self.half_open_successes >= self.half_open_requests:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")

            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    def _record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN")

            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit {self.name}: CLOSED -> OPEN (failures: {self.failure_count})")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if not self._should_attempt():
            raise CircuitOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    def reset(self):
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_successes = 0
            self.last_failure_time = None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.name,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        }

    def is_available(self) -> bool:
        return self._should_attempt()


class CircuitOpenError(Exception):
    pass


_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, **kwargs)
    return _breakers[name]


def reset_all_breakers():
    for breaker in _breakers.values():
        breaker.reset()
