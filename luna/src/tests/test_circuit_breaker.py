import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCircuitState:
    def test_all_states_exist(self):
        from src.core.circuit_breaker import CircuitState

        assert CircuitState.CLOSED is not None
        assert CircuitState.OPEN is not None
        assert CircuitState.HALF_OPEN is not None

    def test_states_are_unique(self):
        from src.core.circuit_breaker import CircuitState

        states = [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
        assert len(set(states)) == 3


class TestCircuitBreakerInit:
    def test_initial_state_closed(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_initial_failure_count_zero(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")
        assert cb.failure_count == 0

    def test_initial_success_count_zero(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")
        assert cb.success_count == 0

    def test_custom_failure_threshold(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test", failure_threshold=10)
        assert cb.failure_threshold == 10

    def test_custom_recovery_timeout(self):
        from datetime import timedelta

        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test", recovery_timeout=60)
        assert cb.recovery_timeout == timedelta(seconds=60)


class TestCircuitBreakerTransitions:
    def test_opens_after_failures(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            cb._record_failure()
        assert cb.state == CircuitState.OPEN

    def test_stays_closed_before_threshold(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test", failure_threshold=5)
        for _ in range(4):
            cb._record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_success_decrements_failure_count(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")
        cb._record_failure()
        cb._record_failure()
        initial = cb.failure_count
        cb._record_success()
        assert cb.failure_count < initial

    def test_success_increments_success_count(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")
        cb._record_success()
        assert cb.success_count == 1


class TestCircuitBreakerHalfOpen:
    def test_half_open_to_closed_on_successes(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test", failure_threshold=1, half_open_requests=2)
        cb._record_failure()
        assert cb.state == CircuitState.OPEN

        cb.state = CircuitState.HALF_OPEN
        cb._record_success()
        cb._record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test", failure_threshold=1)
        cb.state = CircuitState.HALF_OPEN
        cb._record_failure()
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerCall:
    def test_call_success(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.success_count == 1

    def test_call_failure_raises(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test")

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.failure_count == 1

    def test_call_blocked_when_open(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState

        cb = CircuitBreaker("test")
        cb.state = CircuitState.OPEN
        cb.last_failure_time = None

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)


class TestCircuitBreakerReset:
    def test_reset_clears_state(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test")
        cb._record_failure()
        cb._record_failure()
        cb._record_success()

        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.half_open_successes == 0
        assert cb.last_failure_time is None


class TestCircuitBreakerStatus:
    def test_get_status_returns_dict(self):
        from src.core.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker("test_circuit")
        status = cb.get_status()

        assert isinstance(status, dict)
        assert status["name"] == "test_circuit"
        assert "state" in status
        assert "failure_count" in status
        assert "success_count" in status

    def test_is_available_when_closed(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_available() is True

    def test_is_available_when_open(self):
        from src.core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("test")
        cb.state = CircuitState.OPEN
        cb.last_failure_time = None
        assert cb.is_available() is False


class TestCircuitBreakerFactory:
    def test_get_circuit_breaker_creates_new(self):
        from src.core.circuit_breaker import _breakers, get_circuit_breaker

        _breakers.clear()
        cb = get_circuit_breaker("new_breaker")
        assert cb.name == "new_breaker"
        assert "new_breaker" in _breakers

    def test_get_circuit_breaker_returns_cached(self):
        from src.core.circuit_breaker import _breakers, get_circuit_breaker

        _breakers.clear()
        cb1 = get_circuit_breaker("cached_breaker")
        cb2 = get_circuit_breaker("cached_breaker")
        assert cb1 is cb2

    def test_reset_all_breakers(self):
        from src.core.circuit_breaker import _breakers, get_circuit_breaker, reset_all_breakers

        _breakers.clear()
        cb1 = get_circuit_breaker("breaker1")
        cb2 = get_circuit_breaker("breaker2")

        cb1._record_failure()
        cb2._record_failure()

        reset_all_breakers()

        assert cb1.failure_count == 0
        assert cb2.failure_count == 0


class TestCircuitOpenError:
    def test_circuit_open_error_is_exception(self):
        from src.core.circuit_breaker import CircuitOpenError

        error = CircuitOpenError("Test message")
        assert isinstance(error, Exception)
        assert str(error) == "Test message"
