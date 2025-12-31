import time
from collections.abc import Generator

from google import genai

import config
from src.core.logging_config import get_logger
from src.soul.providers.base import HealthCheckResult, LLMProvider, LLMResponse, ProviderStatus

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model_name: str | None = None, priority: int = 1):
        super().__init__(name="gemini", priority=priority)
        self.api_key = api_key or config.GOOGLE_API_KEY
        self.model_name = model_name or config.GEMINI_CONFIG.get("MODEL_NAME", "gemini-2.0-flash")
        self._client: genai.Client | None = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"GeminiProvider inicializado: {self.model_name}")
            except Exception as e:
                logger.error(f"Erro ao inicializar GeminiProvider: {e}")

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("API key nao configurada para Gemini")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
        start = time.time()

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=kwargs.get("temperature", 0.8),
                    max_output_tokens=kwargs.get("max_tokens", 1024),
                ),
            )

            latency = (time.time() - start) * 1000
            self.record_success()

            return LLMResponse(
                text=response.text,
                model=self.model_name,
                provider=self.name,
                latency_ms=latency,
            )

        except Exception as e:
            self.record_failure()
            logger.error(f"Erro em GeminiProvider.generate: {e}")
            raise

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        if self.is_circuit_open():
            return False
        return True

    def health_check(self) -> HealthCheckResult:
        if not self.api_key:
            result = HealthCheckResult(
                status=ProviderStatus.UNAVAILABLE,
                message="API key nao configurada",
            )
            self._last_health = result
            return result

        start = time.time()
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents="ping",
                config=genai.types.GenerateContentConfig(max_output_tokens=5),
            )

            latency = (time.time() - start) * 1000

            if response.text:
                result = HealthCheckResult(
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    message="OK",
                )
            else:
                result = HealthCheckResult(
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    message="Resposta vazia",
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
            response = client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=kwargs.get("temperature", 0.8),
                    max_output_tokens=kwargs.get("max_tokens", 1024),
                ),
            )

            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    self.record_success()
                    yield chunk.text

        except Exception as e:
            self.record_failure()
            logger.error(f"Erro em GeminiProvider.generate_stream: {e}")
            raise

    def supports_streaming(self) -> bool:
        return True
