from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

import aiohttp

import config

from .models import OllamaResponse

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = base_url or config.OLLAMA_CONFIG["BASE_URL"]
        self.timeout = timeout or config.OLLAMA_CONFIG["TIMEOUT"]
        self._session: aiohttp.ClientSession | None = None
        self._closed = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._closed:
            raise RuntimeError("Client foi fechado")
        if self._session is None or self._session.closed:
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._session = aiohttp.ClientSession(timeout=timeout)
            except Exception as e:
                logger.debug(f"Erro ao criar sessao aiohttp: {e}")
                raise
        return self._session

    async def close(self):
        self._closed = True
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                logger.debug(f"Erro ao fechar sessao aiohttp: {e}")
            finally:
                self._session = None

    async def check_health(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check falhou: {e}")
            return False

    async def unload_model(self, model: str) -> bool:
        try:
            session = await self._get_session()
            payload = {"model": model, "keep_alive": 0}
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    logger.info(f"Modelo {model} descarregado da VRAM")
                    return True
                return False
        except Exception as e:
            logger.warning(f"Erro ao descarregar modelo {model}: {e}")
            return False

    async def unload_all_models(self) -> int:
        loaded = await self.list_loaded_models()
        count = 0
        for model_name in loaded:
            if await self.unload_model(model_name):
                count += 1
        return count

    async def list_loaded_models(self) -> list:
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/ps") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.warning(f"Erro ao listar modelos carregados: {e}")
            return []

    async def list_models(self) -> list:
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []

    async def model_exists(self, model_name: str) -> bool:
        models = await self.list_models()
        return any(model_name in m for m in models)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> OllamaResponse:
        model = model or config.CHAT_LOCAL["model"]

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
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
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama generate erro: {response.status} - {error_text}")
                    return OllamaResponse(
                        text="",
                        model=model,
                        done=True,
                        error=f"HTTP {response.status}: {error_text}",
                    )

                data = await response.json()
                text = data.get("response", "").strip()

                if not text:
                    logger.warning(f"Ollama {model} retornou resposta vazia (HTTP 200)")
                    return OllamaResponse(
                        text="",
                        model=model,
                        done=True,
                        error="Modelo retornou resposta vazia",
                    )

                return OllamaResponse(
                    text=text,
                    model=model,
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    eval_count=data.get("eval_count"),
                )

        except asyncio.TimeoutError:
            logger.error(f"Timeout ao gerar resposta com {model}")
            return OllamaResponse(
                text="",
                model=model,
                done=True,
                error="Timeout na requisicao",
            )
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}", exc_info=True)
            return OllamaResponse(
                text="",
                model=model,
                done=True,
                error=str(e),
            )

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
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
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama stream erro: {response.status}")
                    yield f"[Erro: {error_text}]"
                    return

                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Erro no stream: {e}")
            yield f"[Erro: {str(e)}]"

    async def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.85,
    ) -> OllamaResponse:
        from . import specialized

        return await specialized.chat(self, prompt, system_prompt, temperature)

    async def code(
        self,
        prompt: str,
        language: str = "python",
        temperature: float = 0.3,
    ) -> OllamaResponse:
        from . import specialized

        return await specialized.code(self, prompt, language, temperature)

    async def vision(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.5,
    ) -> OllamaResponse:
        from . import specialized

        return await specialized.vision(self, prompt, image_base64, temperature)

    async def vision_from_file(
        self,
        prompt: str,
        image_path: str,
        temperature: float = 0.5,
    ) -> OllamaResponse:
        from . import specialized

        return await specialized.vision_from_file(self, prompt, image_path, temperature)
