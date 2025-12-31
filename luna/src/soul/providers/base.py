import time
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ProviderStatus(Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str = ""
    tokens_used: int = 0
    latency_ms: float = 0
    cached: bool = False
    fallback_used: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    status: ProviderStatus
    latency_ms: float = 0
    message: str = ""
    last_check: float = field(default_factory=time.time)


class LLMProvider(ABC):
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self._last_health: HealthCheckResult | None = None
        self._consecutive_failures = 0
        self._max_failures = 3

    @abstractmethod
    def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

    def get_status(self) -> ProviderStatus:
        if self._last_health is None:
            return ProviderStatus.UNKNOWN
        return self._last_health.status

    def record_success(self) -> None:
        self._consecutive_failures = 0

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._max_failures:
            logger.warning(f"Provider {self.name} marcado como indisponivel apos {self._consecutive_failures} falhas")

    def is_circuit_open(self) -> bool:
        return self._consecutive_failures >= self._max_failures

    def reset_circuit(self) -> None:
        self._consecutive_failures = 0
        logger.info(f"Circuit breaker resetado para {self.name}")

    def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
        response = self.generate(prompt, system, **kwargs)
        yield response.text

    def supports_streaming(self) -> bool:
        return False
