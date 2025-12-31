import logging
import time
from dataclasses import dataclass
from enum import Enum

import config
from src.core.metricas import get_latency_tracker
from src.core.ollama_client import get_ollama_client
from src.core.router import Intent, get_provider_config, should_use_local

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    name: str
    status: ProviderStatus
    latency: float
    last_check: float
    error: str | None = None


class FallbackManager:
    def __init__(self):
        self._health_cache: dict[str, ProviderHealth] = {}
        self._health_ttl = 60.0
        self._ollama_client = None
        self._gemini_available = bool(config.GOOGLE_API_KEY)

        logger.info("FallbackManager inicializado")
        logger.info(f"  Gemini API: {'disponivel' if self._gemini_available else 'nao configurado'}")

    def _get_ollama_client(self):
        if self._ollama_client is None:
            self._ollama_client = get_ollama_client()
        return self._ollama_client

    async def check_ollama_health(self) -> ProviderHealth:
        cache_key = "ollama"
        cached = self._health_cache.get(cache_key)
        if cached and (time.time() - cached.last_check) < self._health_ttl:
            return cached

        try:
            start = time.time()
            client = self._get_ollama_client()
            healthy = await client.check_health()
            latency = time.time() - start

            status = ProviderStatus.AVAILABLE if healthy else ProviderStatus.UNAVAILABLE
            health = ProviderHealth(name="ollama", status=status, latency=latency, last_check=time.time())
            self._health_cache[cache_key] = health
            return health

        except Exception as e:
            health = ProviderHealth(
                name="ollama", status=ProviderStatus.UNAVAILABLE, latency=0, last_check=time.time(), error=str(e)
            )
            self._health_cache[cache_key] = health
            return health

    async def check_model_available(self, model: str) -> bool:
        try:
            client = self._get_ollama_client()
            return await client.model_exists(model)
        except Exception:
            return False

    async def get_best_provider(self, intent: Intent) -> tuple[str, dict, bool]:
        prefer_local = should_use_local(intent)
        provider, cfg = get_provider_config(intent)

        if prefer_local:
            ollama_health = await self.check_ollama_health()
            if ollama_health.status == ProviderStatus.AVAILABLE:
                model = cfg.get("model", "")
                if await self.check_model_available(model):
                    logger.debug(f"[FALLBACK] Usando local para {intent.value}: {model}")
                    return "local", cfg, True

            logger.warning(f"[FALLBACK] Local indisponivel para {intent.value}, tentando API")

        if self._gemini_available:
            api_cfg = self._get_api_config(intent)
            logger.debug(f"[FALLBACK] Usando API para {intent.value}")
            return "api", api_cfg, False

        logger.error(f"[FALLBACK] Nenhum provider disponivel para {intent.value}")
        return "none", {}, False

    def _get_api_config(self, intent: Intent) -> dict:
        if intent == Intent.CHAT:
            return config.CHAT_GEMINI
        elif intent == Intent.CODE:
            return config.CODE_API
        elif intent == Intent.VISION:
            return config.VISION_GEMINI
        return {}

    async def generate_with_fallback(
        self, prompt: str, intent: Intent, system: str | None = None, **kwargs
    ) -> tuple[str, str, bool]:
        provider, cfg, is_local = await self.get_best_provider(intent)
        latency_tracker = get_latency_tracker()

        if provider == "none":
            return "", "Nenhum provider disponivel", False

        start_time = time.time()

        if is_local:
            try:
                client = self._get_ollama_client()
                model = cfg.get("model", "dolphin-mistral")
                temperature = cfg.get("temperature", kwargs.get("temperature", 0.7))

                response = await client.generate(
                    prompt=prompt,
                    model=model,
                    system=system,
                    temperature=temperature,
                    max_tokens=kwargs.get("max_tokens", 1024),
                )

                latency = time.time() - start_time
                latency_tracker.record("llm", latency, {"provider": "local", "model": model})

                if response.error:
                    logger.warning(f"[FALLBACK] Local falhou: {response.error}, tentando API...")
                    return await self._try_api_fallback(prompt, intent, system, **kwargs)

                return response.text, "", True

            except Exception as e:
                logger.error(f"[FALLBACK] Erro local: {e}")
                return await self._try_api_fallback(prompt, intent, system, **kwargs)
        else:
            return await self._try_api_fallback(prompt, intent, system, **kwargs)

    async def _try_api_fallback(
        self, prompt: str, intent: Intent, system: str | None = None, **kwargs
    ) -> tuple[str, str, bool]:
        if not self._gemini_available:
            return "", "API Gemini nao configurada", False

        try:
            from google import genai

            latency_tracker = get_latency_tracker()
            start_time = time.time()

            model_name = config.GEMINI_CONFIG.get("MODEL_NAME", "gemini-1.5-flash")
            client = genai.Client(api_key=config.GOOGLE_API_KEY)

            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            response = client.models.generate_content(model=model_name, contents=full_prompt)

            latency = time.time() - start_time
            latency_tracker.record("llm", latency, {"provider": "api", "model": model_name})

            return response.text, "", True

        except Exception as e:
            logger.error(f"[FALLBACK] API falhou: {e}")
            return "", str(e), False

    async def code_with_fallback(
        self, prompt: str, language: str = "python", context: str | None = None
    ) -> tuple[str, str, bool]:
        provider, cfg, is_local = await self.get_best_provider(Intent.CODE)

        if provider == "none":
            return "", "Nenhum provider disponivel", False

        if is_local:
            try:
                from src.core.models.qwen_coder import CodeLanguage, get_qwen_coder

                coder = get_qwen_coder()
                lang = CodeLanguage(language) if language in [l.value for l in CodeLanguage] else CodeLanguage.PYTHON

                response = await coder.generate(prompt, lang, context)

                if response.error:
                    logger.warning(f"[FALLBACK] Qwen falhou: {response.error}")
                    return await self._try_api_fallback(prompt, Intent.CODE, None)

                return response.code, "", True

            except Exception as e:
                logger.error(f"[FALLBACK] Erro no Qwen: {e}")
                return await self._try_api_fallback(prompt, Intent.CODE, None)
        else:
            return await self._try_api_fallback(prompt, Intent.CODE, None)

    async def vision_with_fallback(self, image_base64: str, prompt: str | None = None) -> tuple[str, str, bool]:
        provider, cfg, is_local = await self.get_best_provider(Intent.VISION)

        if provider == "none":
            return "", "Nenhum provider disponivel", False

        if is_local:
            try:
                from src.core.models.minicpm_vision import get_minicpm_vision

                vision = get_minicpm_vision()
                response = await vision.describe(image_base64, prompt)

                if response.error:
                    logger.warning(f"[FALLBACK] MiniCPM falhou: {response.error}")
                    return await self._try_vision_api(image_base64, prompt)

                return response.description, "", True

            except Exception as e:
                logger.error(f"[FALLBACK] Erro no MiniCPM: {e}")
                return await self._try_vision_api(image_base64, prompt)
        else:
            return await self._try_vision_api(image_base64, prompt)

    async def _try_vision_api(self, image_base64: str, prompt: str | None = None) -> tuple[str, str, bool]:
        if not self._gemini_available:
            return "", "API Gemini nao configurada", False

        try:
            import base64

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=config.GOOGLE_API_KEY)

            image_data = base64.b64decode(image_base64)
            image_part = types.Part.from_bytes(data=image_data, mime_type="image/jpeg")

            prompt_text = prompt or "Descreva detalhadamente o que voce ve nesta imagem."
            response = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt_text, image_part])

            return response.text, "", True

        except Exception as e:
            logger.error(f"[FALLBACK] Vision API falhou: {e}")
            return "", str(e), False

    async def get_health_summary(self) -> dict:
        ollama = await self.check_ollama_health()

        return {
            "ollama": {"status": ollama.status.value, "latency": ollama.latency, "error": ollama.error},
            "gemini": {"status": "available" if self._gemini_available else "not_configured"},
        }

    async def close(self):
        if self._ollama_client:
            await self._ollama_client.close()
            self._ollama_client = None


_instance: FallbackManager | None = None


def get_fallback_manager() -> FallbackManager:
    global _instance
    if _instance is None:
        _instance = FallbackManager()
    return _instance


async def quick_generate(prompt: str, intent: Intent = Intent.CHAT) -> str:
    manager = get_fallback_manager()
    text, error, success = await manager.generate_with_fallback(prompt, intent)
    if not success:
        return f"[Erro: {error}]"
    return text
