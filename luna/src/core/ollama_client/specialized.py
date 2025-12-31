from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

import config

from .models import OllamaResponse

if TYPE_CHECKING:
    from .async_client import OllamaClient

logger = logging.getLogger(__name__)

CODE_SYSTEM_TEMPLATE = """Voce e um assistente especializado em programacao.
Linguagem principal: {language}
Regras:
- Responda APENAS com codigo, sem explicacoes longas
- Use type hints quando aplicavel
- Siga as melhores praticas da linguagem
- Se precisar explicar, seja breve e direto"""


async def chat(
    client: OllamaClient,
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.85,
) -> OllamaResponse:
    model = config.CHAT_LOCAL["model"]
    max_tokens = config.CHAT_LOCAL.get("max_tokens", 1024)

    return await client.generate(
        prompt=prompt,
        model=model,
        system=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def code(
    client: OllamaClient,
    prompt: str,
    language: str = "python",
    temperature: float = 0.3,
) -> OllamaResponse:
    model = config.CODE_LOCAL["model"]
    max_tokens = config.CODE_LOCAL.get("max_tokens", 4096)

    system = CODE_SYSTEM_TEMPLATE.format(language=language)

    return await client.generate(
        prompt=prompt,
        model=model,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def vision(
    client: OllamaClient,
    prompt: str,
    image_base64: str,
    temperature: float = 0.5,
) -> OllamaResponse:
    model = config.VISION_LOCAL["model"]

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30s",
        "images": [image_base64],
        "options": {
            "temperature": temperature,
            "num_predict": 512,
        },
    }

    try:
        session = await client._get_session()
        async with session.post(
            f"{client.base_url}/api/generate",
            json=payload,
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Ollama vision erro: {response.status}")
                return OllamaResponse(
                    text="",
                    model=model,
                    done=True,
                    error=error_text,
                )

            data = await response.json()
            text = data.get("response", "").strip()

            if not text:
                logger.warning(f"Ollama Vision {model} retornou resposta vazia (HTTP 200)")
                return OllamaResponse(
                    text="",
                    model=model,
                    done=True,
                    error="Modelo de visao retornou resposta vazia",
                )

            return OllamaResponse(
                text=text,
                model=model,
                done=True,
                total_duration=data.get("total_duration"),
            )

    except Exception as e:
        logger.error(f"Erro na visao: {e}")
        return OllamaResponse(
            text="",
            model=model,
            done=True,
            error=str(e),
        )


async def vision_from_file(
    client: OllamaClient,
    prompt: str,
    image_path: str,
    temperature: float = 0.5,
) -> OllamaResponse:
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        return await vision(client, prompt, image_base64, temperature)
    except FileNotFoundError:
        return OllamaResponse(
            text="",
            model=config.VISION_LOCAL["model"],
            done=True,
            error=f"Arquivo nao encontrado: {image_path}",
        )
    except Exception as e:
        return OllamaResponse(
            text="",
            model=config.VISION_LOCAL["model"],
            done=True,
            error=str(e),
        )
