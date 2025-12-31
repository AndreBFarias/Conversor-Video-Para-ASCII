"""Chamadas aos provedores LLM (Ollama e Gemini)."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.app.luna_app import TemploDaAlma
    from src.core.ollama_client import OllamaSyncClient

import config
from src.core.logging_config import get_logger
from src.core.metricas import get_api_tracker, get_metrics
from src.soul.model_helpers import (
    COMPACT_MODEL_THRESHOLD_GB,
    SMALL_MODEL_THRESHOLD_GB,
    get_model_size_gb,
    sanitize_for_log,
)
from src.soul.response_parser import get_parser

logger = get_logger(__name__)


class LLMCaller:
    def __init__(
        self,
        provider: str,
        model_name: str,
        gemini_client: Any = None,
        ollama_client: "OllamaSyncClient" = None,
        app: "TemploDaAlma" = None,
    ):
        self.provider = provider
        self.model_name = model_name
        self.gemini_client = gemini_client
        self.ollama_client = ollama_client
        self.app = app

        self.metrics = get_metrics()
        self.api_tracker = get_api_tracker()
        self._model_lock = threading.Lock()

        self.response_cache: dict[str, str] = {}
        self.cache_max_size = config.GEMINI_CONFIG["CACHE_SIZE"]

        self.response_parser = get_parser()
        self.use_simple_prompt = False
        self.json_failures = 0
        self.json_failure_threshold = 3

        self._system_instruction: str = ""
        self._simple_instruction_builder: Callable[[], str] = None
        self._ultra_compact_builder: Callable[[], str] = None

    def set_system_instruction(self, instruction: str) -> None:
        self._system_instruction = instruction

    def set_instruction_builders(
        self,
        simple_builder: Callable[[], str] = None,
        ultra_compact_builder: Callable[[], str] = None,
    ) -> None:
        self._simple_instruction_builder = simple_builder
        self._ultra_compact_builder = ultra_compact_builder

    def _get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()[:16]

    def _is_shutdown(self) -> bool:
        if self.app and hasattr(self.app, "threading_manager"):
            return self.app.threading_manager.shutdown_event.is_set()
        return False

    def call(self, prompt: str) -> str:
        cache_key = self._get_cache_key(prompt)

        if cache_key in self.response_cache:
            logger.info(f"Resposta encontrada no cache (key: {cache_key})")
            self.metrics.increment("consciencia.cache_hits")
            return self.response_cache[cache_key]

        if self.provider == "gemini":
            can_request, reason = self.api_tracker.can_make_request()
            if not can_request:
                logger.warning(f"Request bloqueada: {reason}")
                raise Exception(f"Request bloqueada: {reason}")

        try:
            if self.provider == "local" and self.ollama_client:
                response_text = self._call_ollama(prompt)
            elif self.provider == "gemini" and self.gemini_client:
                raw_response = self._call_gemini(prompt)
                parsed_data, method = self.response_parser.parse(raw_response)
                logger.info(f"Gemini parse method: {method}")
                response_text = json.dumps(parsed_data, ensure_ascii=False)
            else:
                raise Exception("Nenhum provider LLM disponivel")

            if len(self.response_cache) >= self.cache_max_size:
                oldest_key = next(iter(self.response_cache))
                del self.response_cache[oldest_key]

            self.response_cache[cache_key] = response_text
            return response_text

        except Exception as e:
            logger.error(f"Erro no provider {self.provider}: {e}")
            raise

    def _call_ollama(self, prompt: str) -> str:
        try:
            max_context = config.CHAT_LOCAL.get("context_length", 8192)
            max_prompt_chars = int(max_context * 3.5)
            timeout_seconds = config.CHAT_LOCAL.get("timeout", 60)

            model_size = get_model_size_gb(self.model_name)

            if model_size < COMPACT_MODEL_THRESHOLD_GB and self._ultra_compact_builder:
                system_prompt = self._ultra_compact_builder()
                logger.info(
                    f"Modelo compacto ({self.model_name}, {model_size}B), usando prompt ultra-compacto ({len(system_prompt)} chars)"
                )
            elif (self.use_simple_prompt or model_size < SMALL_MODEL_THRESHOLD_GB) and self._simple_instruction_builder:
                system_prompt = self._simple_instruction_builder()
                logger.info(
                    f"Usando prompt simplificado ({self.model_name}, {model_size}B, {len(system_prompt)} chars)"
                )
            else:
                system_prompt = (
                    self._system_instruction
                    if self._system_instruction
                    else (
                        "Voce e Luna, uma assistente gotica sarcastica. "
                        "Responda de forma curta e direta em portugues brasileiro. Sem emojis."
                    )
                )

            if len(prompt) > max_prompt_chars:
                logger.warning(f"Prompt truncado de {len(prompt)} para {max_prompt_chars} chars")
                prompt = prompt[-max_prompt_chars:]

            def _do_ollama_request():
                logger.info(f"[OLLAMA] Iniciando requisicao com modelo: {self.model_name}")
                with self._model_lock:
                    loaded = self.ollama_client.list_loaded_models()
                    logger.info(f"[OLLAMA] Modelos carregados: {loaded}")
                    for model in loaded:
                        if model != self.model_name:
                            logger.info(f"Descarregando modelo {model} para liberar VRAM...")
                            self.ollama_client.unload_model(model)

                    logger.info(f"[OLLAMA] Chamando generate com modelo: {self.model_name}")
                    return self.ollama_client.generate(
                        prompt=prompt,
                        model=self.model_name,
                        system=system_prompt,
                        temperature=config.CHAT_LOCAL.get("temperature", 0.7),
                        max_tokens=config.CHAT_LOCAL.get("max_tokens", 512),
                    )

            if self._is_shutdown():
                logger.debug("Shutdown detectado, abortando chamada Ollama")
                raise Exception("Shutdown em andamento")

            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_do_ollama_request)
                    elapsed = 0.0
                    check_interval = 2.0
                    while elapsed < timeout_seconds:
                        if self._is_shutdown():
                            logger.info("Shutdown detectado durante espera Ollama, abortando")
                            future.cancel()
                            raise Exception("Shutdown durante requisicao Ollama")
                        try:
                            response = future.result(timeout=check_interval)
                            break
                        except FuturesTimeoutError:
                            elapsed += check_interval
                            continue
                    else:
                        logger.error(f"Ollama timeout apos {timeout_seconds}s")
                        raise Exception(f"Ollama timeout apos {timeout_seconds}s")
            except RuntimeError as e:
                if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                    logger.debug(f"Executor fechado durante shutdown: {e}")
                    raise Exception("Executor fechado durante shutdown")
                raise

            if response.error:
                logger.error(f"Ollama erro: {response.error}")
                raise Exception(response.error)

            raw_text = response.text.strip()
            logger.info(f"Ollama raw: {sanitize_for_log(raw_text, max_len=100)}")

            if not raw_text or len(raw_text) < 3:
                raise Exception("Resposta vazia do Ollama")

            parsed_data, method = self.response_parser.parse(raw_text)
            logger.info(f"Parse method: {method}")

            if method == "raw_fallback":
                self.json_failures += 1
                if self.json_failures >= self.json_failure_threshold and not self.use_simple_prompt:
                    logger.warning(f"Muitas falhas JSON ({self.json_failures}), ativando prompt simplificado")
                    self.use_simple_prompt = True
            else:
                if self.json_failures > 0:
                    self.json_failures = max(0, self.json_failures - 1)

            return json.dumps(parsed_data, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Falha ao chamar Ollama: {e}")
            raise

    def _call_gemini(self, prompt: str) -> str:
        max_retries = config.GEMINI_CONFIG["MAX_RETRIES"]
        base_delay = config.GEMINI_CONFIG["RETRY_DELAY"]
        timeout_seconds = config.GEMINI_CONFIG.get("TIMEOUT", 30)

        prompt_preview = sanitize_for_log(prompt, max_len=100)
        request_info = self.api_tracker.start_request("consciencia", prompt_preview)

        def _do_request():
            return self.gemini_client.models.generate_content(model=self.model_name, contents=prompt)

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[{request_info['id']}] Tentativa {attempt + 1}/{max_retries} (timeout: {timeout_seconds}s)"
                )

                if self._is_shutdown():
                    logger.debug("Shutdown detectado, abortando chamada Gemini")
                    self.api_tracker.end_request(request_info, success=False, error="shutdown")
                    raise Exception("Shutdown em andamento")

                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(_do_request)
                        try:
                            response = future.result(timeout=timeout_seconds)
                        except FuturesTimeoutError:
                            logger.warning(f"[{request_info['id']}] Timeout apos {timeout_seconds}s")
                            if attempt < max_retries - 1:
                                continue
                            self.api_tracker.end_request(request_info, success=False, error="timeout")
                            raise Exception(f"Timeout apos {timeout_seconds}s")
                except RuntimeError as e:
                    if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                        logger.debug(f"Executor fechado durante shutdown: {e}")
                        self.api_tracker.end_request(request_info, success=False, error="shutdown")
                        raise Exception("Executor fechado durante shutdown")
                    raise

                response_text = response.text
                self.api_tracker.end_request(request_info, success=True)
                return response_text

            except FuturesTimeoutError:
                raise
            except Exception as e:
                error_msg = str(e)
                is_quota_error = "429" in error_msg or "Resource exhausted" in error_msg

                if is_quota_error:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2**attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        self.api_tracker.end_request(request_info, success=False, error="429_quota_exceeded")
                        raise Exception("Cota da API excedida (429).")
                else:
                    self.api_tracker.end_request(request_info, success=False, error=error_msg[:100])
                    raise

        self.api_tracker.end_request(request_info, success=False, error="max_retries_exceeded")
        raise Exception("Maximo de tentativas excedido")

    def has_provider(self) -> bool:
        return self.ollama_client is not None or self.gemini_client is not None


def create_llm_caller(
    provider: str, model_name: str, gemini_client: Any = None, ollama_client: Any = None, app: Any = None
) -> LLMCaller:
    return LLMCaller(provider, model_name, gemini_client, ollama_client, app)
