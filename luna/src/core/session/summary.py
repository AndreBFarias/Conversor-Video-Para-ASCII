import logging
import threading
from collections.abc import Callable

from google import genai

import config
from src.core.entity_loader import get_active_entity, get_entity_name
from src.core.metricas import get_api_tracker

logger = logging.getLogger(__name__)


def _build_history_string(history: list, max_entries: int = 6, max_content_len: int = 150) -> str:
    history_str = ""
    for msg in history[-max_entries:]:
        entity_name = get_entity_name(get_active_entity())
        role = "Usuario" if msg.get("role") == "user" else entity_name
        parts = msg.get("parts", [])
        content_pieces = []
        for p in parts:
            if isinstance(p, tuple) and len(p) >= 2:
                content_pieces.append(str(p[1]))
            elif isinstance(p, dict):
                content_pieces.append(p.get("text", "") or p.get("video_file", ""))
            elif isinstance(p, str):
                content_pieces.append(p)
        content = " ".join(filter(None, content_pieces))
        if content:
            history_str += f"{role}: {content[:max_content_len]}\n"
    return history_str


def _generate_summary_via_ollama(prompt: str) -> str | None:
    try:
        from src.core.ollama_client import OllamaClient

        ollama = OllamaClient()
        model = config.CHAT_LOCAL_MODEL or "dolphin-mistral"
        response = ollama.generate(model=model, prompt=prompt, stream=False)
        if response and response.get("response"):
            candidate = response["response"].strip().replace('"', "").replace(".", "")
            candidate = candidate.split("\n")[0][:50]
            if candidate:
                return candidate
    except Exception as e:
        logger.warning(f"Falha ao gerar resumo via Ollama: {e}")
    return None


def _generate_summary_via_gemini(prompt: str, track_api: bool = False) -> str | None:
    if not config.GOOGLE_API_KEY:
        return None

    try:
        model_name = config.GEMINI_CONFIG.get("MODEL_NAME", "gemini-1.5-pro")
        client = genai.Client(api_key=config.GOOGLE_API_KEY)

        if track_api:
            api_tracker = get_api_tracker()
            can_request, reason = api_tracker.can_make_request()
            if not can_request:
                logger.warning(f"Titulo nao gerado: {reason}. Usando titulo padrao.")
                return None

            request_info = api_tracker.start_request("session_titler", prompt[:100])
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                candidate = response.text.strip().replace('"', "").replace(".", "")
                if candidate:
                    api_tracker.end_request(request_info, success=True)
                    return candidate
                api_tracker.end_request(request_info, success=True)
            except Exception as e:
                error_str = str(e)
                api_tracker.end_request(request_info, success=False, error=error_str[:100])
                raise
        else:
            response = client.models.generate_content(model=model_name, contents=prompt)
            candidate = response.text.strip().replace('"', "").replace(".", "")
            if candidate:
                return candidate

    except Exception as e:
        logger.warning(f"Falha ao gerar resumo via Gemini: {e}")
    return None


def generate_live_summary_background(conversation_history: list, callback: Callable[[str], None]):
    def generate_in_background():
        try:
            history_str = _build_history_string(conversation_history, max_entries=6, max_content_len=150)

            prompt = f"""Resuma este dialogo em EXATAMENTE 3-5 palavras.
REGRAS:
- Maximo 5 palavras
- Sem aspas, sem pontuacao
- Capture o tema central
- Retorne APENAS o resumo

Dialogo:
{history_str}

Resumo:"""

            summary = None

            if config.CHAT_PROVIDER == "local":
                summary = _generate_summary_via_ollama(prompt)
            elif config.GOOGLE_API_KEY:
                summary = _generate_summary_via_gemini(prompt, track_api=False)

            if summary:
                callback(summary)

        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")

    thread = threading.Thread(target=generate_in_background, daemon=True)
    thread.start()


async def generate_title_for_session(history_for_saving: list, gemini_error=None) -> str | None:
    history_str = _build_history_string(history_for_saving, max_entries=5, max_content_len=200)

    prompt = f"""Crie um titulo de EXATAMENTE 3-5 palavras para este dialogo.
REGRAS:
- Maximo 5 palavras
- Sem aspas, sem pontuacao
- Resuma o tema principal
- Seja especifico, nao generico
- Retorne APENAS o titulo

Dialogo:
{history_str}

Titulo:"""

    generated_title = None

    if config.CHAT_PROVIDER == "local":
        generated_title = _generate_summary_via_ollama(prompt)
        if generated_title:
            logger.debug(f"Titulo gerado via Ollama: '{generated_title}'")

    elif not gemini_error and config.GOOGLE_API_KEY:
        generated_title = _generate_summary_via_gemini(prompt, track_api=True)
        if generated_title:
            logger.debug(f"Titulo gerado via Gemini: '{generated_title}'")

    return generated_title
