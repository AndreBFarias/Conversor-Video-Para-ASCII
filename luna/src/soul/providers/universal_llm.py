"""
UniversalLLM - Abstração unificada de providers LLM.

Gerencia múltiplos providers (Gemini, Ollama) com:
- Fallback automatico entre providers
- Circuit breaker para providers instáveis
- Streaming token-by-token
- Health checks periodicos

Classes principais:
    UniversalLLM: Orquestrador de providers

Funcoes de factory:
    get_universal_llm(): Singleton thread-safe

Dependencias:
    - providers/base: Classes base
    - providers/gemini_provider: Provider Gemini
    - providers/ollama_provider: Provider Ollama
"""

import threading
import time
from collections.abc import Generator
from typing import Callable

import config
from src.core.logging_config import get_logger
from src.soul.providers.base import HealthCheckResult, LLMProvider, LLMResponse, ProviderStatus
from src.soul.providers.gemini_provider import GeminiProvider
from src.soul.providers.ollama_provider import OllamaProvider

logger = get_logger(__name__)


class UniversalLLM:
    def __init__(self, providers: list[LLMProvider] | None = None):
        self._providers: list[LLMProvider] = []
        self._lock = threading.Lock()
        self._health_check_interval = 60.0
        self._last_health_check = 0.0
        self._on_fallback: Callable[[str, str], None] | None = None

        if providers:
            for p in providers:
                self.add_provider(p)
        else:
            self._init_default_providers()

        logger.info(f"UniversalLLM inicializado com {len(self._providers)} providers")

    def _init_default_providers(self) -> None:
        chat_provider = config.CHAT_PROVIDER

        if chat_provider == "local":
            self.add_provider(OllamaProvider(priority=0))
            if config.GOOGLE_API_KEY:
                self.add_provider(GeminiProvider(priority=1))
        else:
            if config.GOOGLE_API_KEY:
                self.add_provider(GeminiProvider(priority=0))
            self.add_provider(OllamaProvider(priority=1))

    def add_provider(self, provider: LLMProvider) -> None:
        with self._lock:
            self._providers.append(provider)
            self._providers.sort(key=lambda p: p.priority)
            logger.debug(f"Provider {provider.name} adicionado (prioridade: {provider.priority})")

    def remove_provider(self, name: str) -> bool:
        with self._lock:
            for i, p in enumerate(self._providers):
                if p.name == name:
                    self._providers.pop(i)
                    logger.info(f"Provider {name} removido")
                    return True
            return False

    def set_on_fallback(self, callback: Callable[[str, str], None]) -> None:
        self._on_fallback = callback

    def _get_available_providers(self) -> list[LLMProvider]:
        available = []
        for p in self._providers:
            if p.is_available():
                available.append(p)
            elif p.is_circuit_open():
                logger.debug(f"Provider {p.name} com circuit breaker aberto")
        return available

    def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
        available = self._get_available_providers()

        if not available:
            for p in self._providers:
                p.reset_circuit()
            available = self._get_available_providers()

        if not available:
            raise RuntimeError("Nenhum provider LLM disponivel")

        last_error: Exception | None = None
        primary_provider = available[0].name

        for i, provider in enumerate(available):
            try:
                response = provider.generate(prompt, system, **kwargs)

                if i > 0:
                    response.fallback_used = True
                    response.metadata["primary_provider"] = primary_provider
                    response.metadata["fallback_reason"] = str(last_error) if last_error else "primary unavailable"

                    if self._on_fallback:
                        self._on_fallback(primary_provider, provider.name)

                    logger.warning(f"Fallback: {primary_provider} -> {provider.name}")

                return response

            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.name} falhou: {e}")
                continue

        raise RuntimeError(f"Todos os providers falharam. Ultimo erro: {last_error}")

    def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
        available = self._get_available_providers()

        if not available:
            for p in self._providers:
                p.reset_circuit()
            available = self._get_available_providers()

        if not available:
            raise RuntimeError("Nenhum provider LLM disponivel para streaming")

        streaming_providers = [p for p in available if p.supports_streaming()]
        if not streaming_providers:
            logger.warning("Nenhum provider com streaming, usando fallback")
            streaming_providers = available

        last_error: Exception | None = None
        primary_provider = streaming_providers[0].name

        for i, provider in enumerate(streaming_providers):
            try:
                if i > 0 and self._on_fallback:
                    self._on_fallback(primary_provider, provider.name)
                    logger.warning(f"Stream fallback: {primary_provider} -> {provider.name}")

                for chunk in provider.generate_stream(prompt, system, **kwargs):
                    yield chunk
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Provider stream {provider.name} falhou: {e}")
                continue

        raise RuntimeError(f"Todos os providers de stream falharam. Ultimo erro: {last_error}")

    def health_check_all(self) -> dict[str, HealthCheckResult]:
        results = {}
        for provider in self._providers:
            try:
                results[provider.name] = provider.health_check()
            except Exception as e:
                results[provider.name] = HealthCheckResult(
                    status=ProviderStatus.UNAVAILABLE,
                    message=str(e)[:100],
                )
        self._last_health_check = time.time()
        return results

    def get_status(self) -> dict:
        return {
            "providers": [
                {
                    "name": p.name,
                    "priority": p.priority,
                    "status": p.get_status().value,
                    "available": p.is_available(),
                    "model": p.get_model_name(),
                }
                for p in self._providers
            ],
            "last_health_check": self._last_health_check,
        }

    def get_primary_provider(self) -> LLMProvider | None:
        available = self._get_available_providers()
        return available[0] if available else None

    def get_model_name(self) -> str:
        primary = self.get_primary_provider()
        return primary.get_model_name() if primary else "unknown"


_universal_llm: UniversalLLM | None = None
_lock = threading.Lock()


def get_universal_llm() -> UniversalLLM:
    global _universal_llm
    if _universal_llm is None:
        with _lock:
            if _universal_llm is None:
                _universal_llm = UniversalLLM()
    return _universal_llm


def reset_universal_llm() -> None:
    global _universal_llm
    with _lock:
        _universal_llm = None
