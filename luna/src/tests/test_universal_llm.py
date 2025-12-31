from unittest.mock import MagicMock, patch

import pytest


class TestProviderStatus:
    def test_status_values(self):
        from src.soul.providers.base import ProviderStatus

        assert ProviderStatus.UNKNOWN.value == "unknown"
        assert ProviderStatus.HEALTHY.value == "healthy"
        assert ProviderStatus.DEGRADED.value == "degraded"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"


class TestLLMResponse:
    def test_response_fields(self):
        from src.soul.providers.base import LLMResponse

        response = LLMResponse(
            text="Hello",
            model="test-model",
            provider="test",
            tokens_used=10,
            latency_ms=100.5,
            cached=True,
            fallback_used=True,
        )

        assert response.text == "Hello"
        assert response.model == "test-model"
        assert response.provider == "test"
        assert response.tokens_used == 10
        assert response.latency_ms == 100.5
        assert response.cached is True
        assert response.fallback_used is True

    def test_response_defaults(self):
        from src.soul.providers.base import LLMResponse

        response = LLMResponse(text="Test", model="model")

        assert response.provider == ""
        assert response.tokens_used == 0
        assert response.latency_ms == 0
        assert response.cached is False
        assert response.fallback_used is False
        assert response.metadata == {}


class TestHealthCheckResult:
    def test_result_fields(self):
        from src.soul.providers.base import HealthCheckResult, ProviderStatus

        result = HealthCheckResult(
            status=ProviderStatus.HEALTHY,
            latency_ms=50.0,
            message="OK",
        )

        assert result.status == ProviderStatus.HEALTHY
        assert result.latency_ms == 50.0
        assert result.message == "OK"
        assert result.last_check > 0


class TestLLMProviderBase:
    def test_circuit_breaker_opens_after_failures(self):
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="", model="")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "mock"

        from src.soul.providers.base import ProviderStatus

        provider = MockProvider("test", priority=0)

        assert provider.is_circuit_open() is False

        provider.record_failure()
        provider.record_failure()
        provider.record_failure()

        assert provider.is_circuit_open() is True

    def test_circuit_breaker_resets_on_success(self):
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="", model="")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "mock"

        provider = MockProvider("test", priority=0)

        provider.record_failure()
        provider.record_failure()
        provider.record_success()

        assert provider.is_circuit_open() is False


class TestGeminiProvider:
    @patch("src.soul.providers.gemini_provider.genai")
    @patch("src.soul.providers.gemini_provider.config")
    def test_init_with_api_key(self, mock_config, mock_genai):
        from src.soul.providers.gemini_provider import GeminiProvider

        mock_config.GOOGLE_API_KEY = "test-key"
        mock_config.GEMINI_CONFIG = {"MODEL_NAME": "gemini-pro"}

        provider = GeminiProvider(api_key="test-key")

        assert provider.name == "gemini"
        assert provider.api_key == "test-key"

    @patch("src.soul.providers.gemini_provider.config")
    def test_is_available_without_key(self, mock_config):
        from src.soul.providers.gemini_provider import GeminiProvider

        mock_config.GOOGLE_API_KEY = None
        mock_config.GEMINI_CONFIG = {"MODEL_NAME": "gemini-pro"}

        provider = GeminiProvider(api_key=None)

        assert provider.is_available() is False


class TestOllamaProvider:
    @patch("src.soul.providers.ollama_provider.OllamaSyncClient")
    @patch("src.soul.providers.ollama_provider.config")
    def test_init(self, mock_config, mock_client):
        from src.soul.providers.ollama_provider import OllamaProvider

        mock_config.CHAT_LOCAL = {"model": "llama3"}

        provider = OllamaProvider()

        assert provider.name == "ollama"
        assert provider.model_name == "llama3"

    @patch("src.soul.providers.ollama_provider.OllamaSyncClient")
    @patch("src.soul.providers.ollama_provider.config")
    def test_is_available_with_healthy_client(self, mock_config, mock_client):
        from src.soul.providers.ollama_provider import OllamaProvider

        mock_config.CHAT_LOCAL = {"model": "llama3"}
        mock_instance = MagicMock()
        mock_instance.check_health.return_value = True
        mock_client.return_value = mock_instance

        provider = OllamaProvider()
        result = provider.is_available()

        assert result is True


class TestUniversalLLM:
    @patch("src.soul.providers.universal_llm.config")
    def test_init_with_custom_providers(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="mock", model="mock", provider=self.name)

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "mock"

        provider1 = MockProvider("mock1", priority=0)
        provider2 = MockProvider("mock2", priority=1)

        llm = UniversalLLM(providers=[provider1, provider2])

        assert len(llm._providers) == 2

    @patch("src.soul.providers.universal_llm.config")
    def test_generate_uses_primary_provider(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text=f"from-{self.name}", model="mock", provider=self.name)

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "mock"

        provider1 = MockProvider("primary", priority=0)
        provider2 = MockProvider("fallback", priority=1)

        llm = UniversalLLM(providers=[provider1, provider2])
        response = llm.generate("test", "system")

        assert response.text == "from-primary"
        assert response.fallback_used is False

    @patch("src.soul.providers.universal_llm.config")
    def test_generate_falls_back_on_failure(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class FailingProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                raise RuntimeError("Primary failed")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "failing"

        class WorkingProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="fallback-response", model="mock", provider=self.name)

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "working"

        primary = FailingProvider("primary", priority=0)
        fallback = WorkingProvider("fallback", priority=1)

        llm = UniversalLLM(providers=[primary, fallback])
        response = llm.generate("test", "system")

        assert response.text == "fallback-response"
        assert response.fallback_used is True
        assert response.metadata["primary_provider"] == "primary"

    @patch("src.soul.providers.universal_llm.config")
    def test_generate_raises_when_all_fail(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class FailingProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                raise RuntimeError(f"{self.name} failed")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "failing"

        provider1 = FailingProvider("p1", priority=0)
        provider2 = FailingProvider("p2", priority=1)

        llm = UniversalLLM(providers=[provider1, provider2])

        with pytest.raises(RuntimeError, match="Todos os providers falharam"):
            llm.generate("test", "system")

    @patch("src.soul.providers.universal_llm.config")
    def test_health_check_all(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="", model="")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY, message="OK")

            def get_model_name(self) -> str:
                return "mock"

        provider = MockProvider("test", priority=0)
        llm = UniversalLLM(providers=[provider])

        results = llm.health_check_all()

        assert "test" in results
        assert results["test"].status == ProviderStatus.HEALTHY

    @patch("src.soul.providers.universal_llm.config")
    def test_get_status(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class MockProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="", model="")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "test-model"

        provider = MockProvider("test", priority=0)
        llm = UniversalLLM(providers=[provider])

        status = llm.get_status()

        assert "providers" in status
        assert len(status["providers"]) == 1
        assert status["providers"][0]["name"] == "test"
        assert status["providers"][0]["model"] == "test-model"

    @patch("src.soul.providers.universal_llm.config")
    def test_on_fallback_callback(self, mock_config):
        from src.soul.providers.universal_llm import UniversalLLM
        from src.soul.providers.base import LLMProvider, LLMResponse, HealthCheckResult, ProviderStatus

        mock_config.CHAT_PROVIDER = "local"

        class FailingProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                raise RuntimeError("failed")

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "failing"

        class WorkingProvider(LLMProvider):
            def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse:
                return LLMResponse(text="ok", model="", provider=self.name)

            def is_available(self) -> bool:
                return True

            def health_check(self) -> HealthCheckResult:
                return HealthCheckResult(status=ProviderStatus.HEALTHY)

            def get_model_name(self) -> str:
                return "working"

        callback_calls = []

        def on_fallback(from_provider: str, to_provider: str):
            callback_calls.append((from_provider, to_provider))

        primary = FailingProvider("primary", priority=0)
        fallback = WorkingProvider("fallback", priority=1)

        llm = UniversalLLM(providers=[primary, fallback])
        llm.set_on_fallback(on_fallback)

        llm.generate("test", "system")

        assert len(callback_calls) == 1
        assert callback_calls[0] == ("primary", "fallback")


class TestGetUniversalLLM:
    @patch("src.soul.providers.universal_llm._universal_llm", None)
    @patch("src.soul.providers.universal_llm.config")
    def test_returns_singleton(self, mock_config):
        from src.soul.providers.universal_llm import get_universal_llm, reset_universal_llm

        mock_config.CHAT_PROVIDER = "local"
        mock_config.GOOGLE_API_KEY = None
        mock_config.CHAT_LOCAL = {"model": "test"}

        reset_universal_llm()

        with patch("src.soul.providers.universal_llm.OllamaProvider") as mock_ollama:
            mock_instance = MagicMock()
            mock_ollama.return_value = mock_instance

            llm1 = get_universal_llm()
            llm2 = get_universal_llm()

            assert llm1 is llm2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
