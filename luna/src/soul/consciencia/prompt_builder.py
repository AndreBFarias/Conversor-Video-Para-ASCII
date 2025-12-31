from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.soul.model_helpers import get_user_profile
from src.soul.personalidade import get_personalidade

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def init_soul_prompt(consciencia: Consciencia) -> None:
    try:
        personalidade = get_personalidade()
        consciencia.soul_prompt = personalidade.get_soul_prompt()

        if not consciencia.soul_prompt:
            raise ValueError("Soul prompt vazio")

        user_profile = get_user_profile()
        for key, value in user_profile.items():
            consciencia.soul_prompt = consciencia.soul_prompt.replace(f"{{{key}}}", str(value))

        logger.info("Alma carregada com sucesso via EntityLoader")
    except Exception as e:
        logger.warning(f"Falha ao carregar alma via EntityLoader: {e}")
        consciencia.soul_prompt = "Voce e Luna, uma assistente virtual gotica e sarcastica."


def build_full_prompt(
    consciencia: Consciencia,
    user_text: str,
    visual_context: str | None,
    attached_content: str | None,
    contexto_memoria: str,
) -> str:
    has_document = attached_content is not None and len(attached_content) > 100

    message_parts = []
    if user_text:
        message_parts.append(f"Usuario disse: {user_text}")
    if visual_context:
        message_parts.append(f"Contexto visual (voce acabou de olhar): {visual_context}")
    if attached_content:
        doc_instruction = "\n\nIMPORTANTE: O usuario anexou um documento. Leia ATENTAMENTE o conteudo completo e responda de forma DETALHADA sobre ele. NAO resuma excessivamente.\n"
        message_parts.append(f"{doc_instruction}ARQUIVO(S) ANEXADO(S):\n{attached_content}")

    full_message = " | ".join(message_parts)

    history_text = ""
    if consciencia.conversation_history:
        if has_document:
            history_limit = 2
            max_chars = 80
        else:
            history_limit = 3 if consciencia.provider == "local" else 10
            max_chars = 150 if consciencia.provider == "local" else 300

        history_text = (
            "HISTORICO:\n" if consciencia.provider == "local" else "HISTORICO DE CONVERSA (Ultimas interacoes):\n"
        )
        recent_history = consciencia.conversation_history[-history_limit:]
        for turn in recent_history:
            if "user" not in turn and "luna" not in turn:
                continue
            u = turn.get("user", "")[:max_chars]
            l = turn.get("luna", {}).get("fala_tts", "")[:max_chars]
            if not u and not l:
                continue
            entity_name = get_entity_name(consciencia.active_entity_id)
            history_text += f"User: {u}\n{entity_name}: {l}\n"

    anchor_injection = consciencia.personality_anchor.get_anchor_injection()
    effective_instruction = consciencia.system_instruction
    if anchor_injection:
        effective_instruction = f"{anchor_injection}\n\n{consciencia.system_instruction}"
        logger.debug("Ancoragem de personalidade injetada")

    if consciencia.provider == "local":
        return f"{effective_instruction}\n\n{history_text}\nAgora:\n{full_message}"
    else:
        return f"{effective_instruction}\n\n{contexto_memoria}\n{history_text}\nINTERACAO ATUAL:\n{full_message}"
