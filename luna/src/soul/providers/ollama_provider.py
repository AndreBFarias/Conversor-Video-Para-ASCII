import time
from collections.abc import Generator

import config
from src.core.logging_config import get_logger
from src.core.ollama_client import OllamaSyncClient
from src.soul.providers.base import HealthCheckResult, LLMProvider, LLMResponse, ProviderStatus

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str | None = None, priority: int = 0):
        super().__init__(name="ollama", priority=priority)
        self.model_name = model_name or config.CHAT_LOCAL.get("model", "dolphin-mistral")
        self._client: OllamaSyncClient | None = None

        try:
            self._client = OllamaSyncClient()
            logger.info(f"OllamaProvider inicializado: {self.model_name}")
        except Exception as e:
            logger.error(f"Erro ao inicializar OllamaProvider: {e}")

    def _get_client(self) -> OllamaSyncClient:
        if self._client is None:
            self._client = OllamaSyncClient()
        return self._client

    def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
        start = time.time()

        try:
            client = self._get_client()
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                system=system,
                stream=False,
            )

            latency = (time.time() - start) * 1000
            self.record_success()

            text = ""
            if hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "response"):
                text = response.response
            elif isinstance(response, dict):
                text = response.get("response", "")

            return LLMResponse(
                text=text,
                model=self.model_name,
                provider=self.name,
                latency_ms=latency,
            )

        except Exception as e:
            self.record_failure()
            logger.error(f"Erro em OllamaProvider.generate: {e}")
            raise

    def is_available(self) -> bool:
        if self.is_circuit_open():
            return False
        try:
            client = self._get_client()
            return client.check_health()
        except Exception:
            return False

    def health_check(self) -> HealthCheckResult:
        start = time.time()

        try:
            client = self._get_client()
            is_healthy = client.check_health()
            latency = (time.time() - start) * 1000

            if is_healthy:
                result = HealthCheckResult(
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    message="OK",
                )
            else:
                result = HealthCheckResult(
                    status=ProviderStatus.UNAVAILABLE,
                    latency_ms=latency,
                    message="Health check falhou",
                )

        except Exception as e:
            result = HealthCheckResult(
                status=ProviderStatus.UNAVAILABLE,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)[:100],
            )

        self._last_health = result
        return result

    def get_model_name(self) -> str:
        return self.model_name

    def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
        try:
            client = self._get_client()
            for chunk in client.stream(
                prompt=prompt,
                model=self.model_name,
                system=system,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
            ):
                if chunk and not chunk.startswith("[Erro"):
                    self.record_success()
                    yield chunk
        except Exception as e:
            self.record_failure()
            logger.error(f"Erro em OllamaProvider.generate_stream: {e}")
            raise

    def supports_streaming(self) -> bool:
        return True
