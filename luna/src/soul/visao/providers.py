from __future__ import annotations

import base64
import logging
import time
from io import BytesIO
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

import config
from src.core.metricas import get_api_tracker

if TYPE_CHECKING:
    from google import genai
    from src.core.ollama_client import OllamaSyncClient

logger = logging.getLogger(__name__)


def frame_to_base64(frame_rgb: np.ndarray, max_size: tuple[int, int] = (640, 480)) -> str:
    img_pil = Image.fromarray(frame_rgb)
    img_pil.thumbnail(max_size)
    buffer = BytesIO()
    img_pil.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class GeminiVisionProvider:
    def __init__(self, api_key: str, model_name: str):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.api_tracker = get_api_tracker()
        self._last_api_call = 0
        self._min_api_interval = 10.0

    def safe_generate_content(self, content_list, context: str = "visao"):
        can_request, reason = self.api_tracker.can_make_request()
        if not can_request:
            logger.warning(f"Request bloqueada: {reason}")
            raise Exception(f"Request bloqueada: {reason}")

        now = time.time()
        elapsed = now - self._last_api_call
        if elapsed < self._min_api_interval:
            time.sleep(self._min_api_interval - elapsed)

        request_info = self.api_tracker.start_request(context)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._last_api_call = time.time()
                response = self.client.models.generate_content(model=self.model_name, contents=content_list)
                self.api_tracker.end_request(request_info, success=True)
                return response
            except Exception as e:
                error_msg = str(e)
                is_quota_error = "429" in error_msg or "quota" in error_msg.lower()
                if is_quota_error and attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(
                        f"[{request_info['id']}] Erro 429. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                self.api_tracker.end_request(request_info, success=False, error=error_msg[:100])
                raise

    def describe(self, frame_rgb: np.ndarray, prompt: str = None) -> str:
        prompt = prompt or "Descreva brevemente em portugues o que voce ve nesta imagem (1-2 frases)."

        logger.info("Analisando frame com Gemini Vision...")
        img_pil = Image.fromarray(frame_rgb)
        img_pil.thumbnail((640, 480))

        response = self.safe_generate_content([prompt, img_pil])
        return response.text.strip()


class OllamaVisionProvider:
    def __init__(self, client: "OllamaSyncClient", model_name: str):
        self.client = client
        self.model_name = model_name

    def verify_model(self) -> bool:
        if not self.client:
            return False

        try:
            models = self.client.list_models()
            model_found = any(self.model_name in m for m in models)

            if not model_found:
                logger.warning(f"Modelo de visao '{self.model_name}' nao encontrado.")
                logger.warning(f"Modelos disponiveis: {models}")
                logger.warning(f"Execute: ollama pull {self.model_name}")
                return False

            logger.info(f"Modelo de visao '{self.model_name}' verificado")
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar modelo de visao: {e}")
            return False

    def describe(self, frame_rgb: np.ndarray, prompt: str = None) -> str:
        if not self.client:
            logger.warning("describe: ollama_client nao inicializado")
            return "Ollama nao inicializado."

        prompt = prompt or "Descreva brevemente o que voce ve nesta imagem em portugues brasileiro (1-2 frases curtas)."

        logger.info(f"describe: iniciando com modelo {self.model_name}")

        try:
            loaded = self.client.list_loaded_models()
            for model in loaded:
                if model != self.model_name:
                    logger.info(f"Descarregando modelo {model} para liberar VRAM...")
                    self.client.unload_model(model)

            image_base64 = frame_to_base64(frame_rgb)
            logger.info(f"Chamando Ollama Vision (modelo: {self.model_name})...")

            response = self.client.vision(prompt, image_base64)

            if response.error:
                logger.error(f"Erro Ollama Vision: {response.error}")
                return f"Erro na visao local: {response.error[:50]}"

            descricao = response.text.strip()
            if not descricao:
                logger.warning("Ollama Vision retornou resposta vazia")
                return "Modelo de visao nao conseguiu processar a imagem. Tente novamente."

            logger.info(f"Ollama Vision: {descricao[:80]}...")
            return descricao

        except Exception as e:
            logger.error(f"Erro ao descrever com Ollama: {e}")
            return f"Erro na visao: {str(e)[:50]}"

    def unload_model(self):
        if self.client:
            try:
                logger.info(f"Descarregando modelo de visao {self.model_name} para liberar VRAM...")
                self.client.unload_model(self.model_name)
            except Exception as e:
                logger.debug(f"Erro ao descarregar modelo de visao: {e}")


class VisionProviderFactory:
    @staticmethod
    def create() -> tuple[str, GeminiVisionProvider | OllamaVisionProvider | None, str | None]:
        provider_name = config.VISION_PROVIDER
        provider = None
        error = None

        if provider_name == "local":
            try:
                from src.core.ollama_client import OllamaSyncClient

                ollama_client = OllamaSyncClient()
                if ollama_client.check_health():
                    model_name = config.VISION_LOCAL["model"]
                    ollama_provider = OllamaVisionProvider(ollama_client, model_name)
                    if ollama_provider.verify_model():
                        logger.info(f"Visao LOCAL inicializada (modelo: {model_name})")
                        return "local", ollama_provider, None
                    else:
                        error = f"Modelo {model_name} nao instalado"
                        provider_name = "gemini"
                else:
                    error = "Ollama nao esta rodando"
                    provider_name = "gemini"
            except Exception as e:
                logger.error(f"Erro ao inicializar Ollama Vision: {e}")
                error = str(e)
                provider_name = "gemini"

        if provider_name == "gemini" and config.GOOGLE_API_KEY:
            try:
                model_name = config.GEMINI_CONFIG["MODEL_NAME"]
                gemini_provider = GeminiVisionProvider(config.GOOGLE_API_KEY, model_name)
                logger.info(f"Visao GEMINI inicializada ({model_name})")
                return "gemini", gemini_provider, None
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini para visao: {e}")
                return "gemini", None, str(e)
        elif provider_name == "gemini":
            logger.warning("GOOGLE_API_KEY ausente. Visao sem IA.")
            return "gemini", None, "API key do Gemini nao configurada"

        return provider_name, None, error
