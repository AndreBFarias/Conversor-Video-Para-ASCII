from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .protocols import IConfigProvider


class ConfigProviderAdapter:
    def __init__(self) -> None:
        import config as cfg

        self._config = cfg

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._config, key, default)

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        current = self._config
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                current = getattr(current, key, None)
            if current is None:
                return default
        return current if current is not None else default

    def get_api_key(self, provider: str) -> str | None:
        key_map = {
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "elevenlabs": "ELEVENLABS_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        key_name = key_map.get(provider.lower())
        if key_name:
            return self.get(key_name)
        return None


class LLMClientAdapter:
    def __init__(self, provider: str, config: IConfigProvider) -> None:
        self._provider = provider
        self._config = config
        self._client: Any = None
        self._model: str = ""
        self._initialize()

    def _initialize(self) -> None:
        if self._provider == "local":
            from ollama import Client as OllamaSyncClient

            self._client = OllamaSyncClient()
            local_config = self._config.get("CHAT_LOCAL", {})
            self._model = local_config.get("model", "llama3.2")
        elif self._provider in ("gemini", "google"):
            import google.genai as genai

            api_key = self._config.get_api_key("google")
            if api_key:
                self._client = genai.Client(api_key=api_key)
            gemini_config = self._config.get("CHAT_GEMINI", {})
            self._model = gemini_config.get("model", "gemini-2.0-flash")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        if self._provider == "local" and self._client:
            response = self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt or ""},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": temperature, "num_predict": max_tokens},
            )
            return response.get("message", {}).get("content", "")

        if self._provider in ("gemini", "google") and self._client:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "system_instruction": system_prompt,
                },
            )
            return response.text

        return ""

    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        return self.generate(prompt, system_prompt, temperature, max_tokens)

    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> Any:
        if self._provider == "local" and self._client:
            return self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt or ""},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": temperature},
                stream=True,
            )
        return iter([])

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return self._provider


class TTSEngineAdapter:
    def __init__(self, config: IConfigProvider) -> None:
        self._config = config
        self._engine: Any = None
        self._engine_name: str = "none"
        self._available = False

    def synthesize(self, text: str) -> bytes | None:
        return None

    def synthesize_to_file(self, text: str, output_path: Path) -> bool:
        return False

    @property
    def engine_name(self) -> str:
        return self._engine_name

    @property
    def is_available(self) -> bool:
        return self._available


class VisionProviderAdapter:
    def __init__(self, config: IConfigProvider) -> None:
        self._config = config
        self._provider: Any = None
        self._provider_name: str = "none"
        self._available = False

    def analyze_image(self, image_path: Path, prompt: str) -> str:
        return ""

    def analyze_base64(self, image_b64: str, prompt: str) -> str:
        return ""

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def is_available(self) -> bool:
        return self._available
