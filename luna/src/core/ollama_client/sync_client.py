from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Generator

import requests

import config

from .async_client import OllamaClient
from .models import OllamaResponse

logger = logging.getLogger(__name__)


class OllamaSyncClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = base_url or config.OLLAMA_CONFIG["BASE_URL"]
        self.timeout = timeout or config.OLLAMA_CONFIG["TIMEOUT"]
        self._shutdown = False

    def _run_async(self, coro):
        if self._shutdown:
            raise RuntimeError("Client em shutdown")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            try:
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            except RuntimeError as e:
                if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                    self._shutdown = True
                    logger.debug(f"Shutdown detectado em OllamaSyncClient: {e}")
                    raise
                raise
        else:
            try:
                return asyncio.run(coro)
            except RuntimeError as e:
                if "shutdown" in str(e).lower() or "cannot" in str(e).lower():
                    self._shutdown = True
                    logger.debug(f"Shutdown detectado em asyncio.run: {e}")
                raise

    def check_health(self) -> bool:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.check_health())
        finally:
            self._run_async(client.close())

    def unload_model(self, model: str) -> bool:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.unload_model(model))
        finally:
            self._run_async(client.close())

    def unload_all_models(self) -> int:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.unload_all_models())
        finally:
            self._run_async(client.close())

    def list_loaded_models(self) -> list:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.list_loaded_models())
        finally:
            self._run_async(client.close())

    def list_models(self) -> list:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.list_models())
        finally:
            self._run_async(client.close())

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> OllamaResponse:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.generate(prompt, model, system, temperature, max_tokens))
        finally:
            self._run_async(client.close())

    def chat(self, prompt: str, system_prompt: str | None = None) -> OllamaResponse:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.chat(prompt, system_prompt))
        finally:
            self._run_async(client.close())

    def code(self, prompt: str, language: str = "python") -> OllamaResponse:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.code(prompt, language))
        finally:
            self._run_async(client.close())

    def vision(self, prompt: str, image_base64: str) -> OllamaResponse:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.vision(prompt, image_base64))
        finally:
            self._run_async(client.close())

    def vision_from_file(self, prompt: str, image_path: str) -> OllamaResponse:
        client = OllamaClient(self.base_url, self.timeout)
        try:
            return self._run_async(client.vision_from_file(prompt, image_path))
        finally:
            self._run_async(client.close())

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        model = model or config.CHAT_LOCAL["model"]

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": config.OLLAMA_CONFIG.get("KEEP_ALIVE", "30m"),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": config.OLLAMA_CONFIG.get("NUM_CTX", 8192),
                "num_gpu": config.OLLAMA_CONFIG.get("NUM_GPU", -1),
            },
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=self.timeout)

            if response.status_code != 200:
                logger.error(f"Ollama stream erro: {response.status_code}")
                yield f"[Erro: {response.text}]"
                return

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.Timeout:
            logger.error("Timeout no stream Ollama")
            yield "[Erro: Timeout]"
        except Exception as e:
            logger.error(f"Erro no stream sync: {e}")
            yield f"[Erro: {str(e)}]"
