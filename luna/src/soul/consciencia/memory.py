from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.data_memory.memory_warmup import run_startup_warmup
from src.data_memory.proactive_recall import get_proactive_recall

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def warmup_memory(consciencia: Consciencia) -> None:
    try:
        warmup_result = run_startup_warmup(consciencia.active_entity_id)
        logger.info(
            f"Memory warmup concluido em {warmup_result.get('total_time_ms', 0)}ms (entidade: {consciencia.active_entity_id})"
        )

        consciencia.smart_memory.migrate_legacy_memories()
        consciencia.global_memory.warm_up()
        consciencia.global_memory.migrate_legacy_memories()

        consciencia.proactive_recall = get_proactive_recall(consciencia.active_entity_id)
        logger.info("Proactive recall inicializado")
    except Exception as e:
        logger.warning(f"Erro no warm-up de memoria: {e}")
        consciencia.proactive_recall = None


def build_memory_context(consciencia: Consciencia, user_text: str) -> str:
    contexto_memoria = ""
    proactive_context = ""
    try:
        mem_context = consciencia.smart_memory.retrieve(user_text, max_chars=600)
        user_profile = consciencia.smart_memory.get_user_profile_context()

        if hasattr(consciencia, "proactive_recall") and consciencia.proactive_recall:
            recall_data = consciencia.proactive_recall.find_relevant_memory(user_text, "")
            if recall_data:
                proactive_context = consciencia.proactive_recall.format_recall_prompt(recall_data)
                logger.info(f"Proactive recall ativado: {recall_data.get('trigger_type', 'unknown')}")

        if mem_context or user_profile or proactive_context:
            parts = []
            if user_profile:
                parts.append(user_profile)
            if proactive_context:
                parts.append(proactive_context)
            if mem_context:
                parts.append(mem_context)
            contexto_memoria = "\n".join(parts) + "\n"
            logger.info(f"Contexto de memoria: {len(contexto_memoria)} chars")
    except Exception as e:
        logger.error(f"Erro ao recuperar memoria: {e}")

    return contexto_memoria


def save_to_memory(consciencia: Consciencia, user_text: str, data: dict) -> None:
    if len(user_text.strip()) > 15:
        consciencia.smart_memory.add(
            f"Usuario disse: {user_text}", source="user_input", metadata={"type": "user_message"}
        )

    response_summary = data.get("fala_tts", "")[:80]
    if len(response_summary) > 20:
        entity_name = get_entity_name(consciencia.active_entity_id)
        consciencia.smart_memory.add(
            f"{entity_name} respondeu: {response_summary}",
            source="entity_response",
            metadata={"type": "assistant_message", "animacao": data.get("animacao")},
        )


def update_memory_tiers(consciencia: Consciencia, user_text: str, data: dict) -> None:
    response_tts = data.get("fala_tts", "")

    consciencia.short_term_memory.add(
        content=user_text,
        importance=0.5,
        category="user_input",
    )
    consciencia.short_term_memory.add(
        content=response_tts,
        importance=0.6,
        category="luna_response",
    )

    if consciencia._interaction_count % 10 == 0:
        result = consciencia.memory_tier_manager.promote_all_eligible()
        total_promoted = sum(result.values())
        if total_promoted > 0:
            logger.info(f"Memorias promovidas: {result}")
