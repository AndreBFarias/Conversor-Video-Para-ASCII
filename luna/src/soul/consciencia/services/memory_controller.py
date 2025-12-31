from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.data_memory.memory_warmup import run_startup_warmup
from src.data_memory.proactive_recall import get_proactive_recall
from src.data_memory.smart_memory import get_entity_smart_memory, get_smart_memory

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


class MemoryController:
    def __init__(self, consciencia: Consciencia) -> None:
        self._consciencia = consciencia
        self._proactive_recall = None

    @property
    def smart_memory(self):
        return self._consciencia.smart_memory

    @property
    def global_memory(self):
        return self._consciencia.global_memory

    @property
    def proactive_recall(self):
        return self._proactive_recall

    def warmup(self) -> dict[str, Any]:
        try:
            warmup_result = run_startup_warmup(self._consciencia.active_entity_id)
            logger.info(f"Memory warmup concluido em {warmup_result.get('total_time_ms', 0)}ms")

            self.smart_memory.migrate_legacy_memories()
            self.global_memory.warm_up()
            self.global_memory.migrate_legacy_memories()

            self._proactive_recall = get_proactive_recall(self._consciencia.active_entity_id)
            self._consciencia.proactive_recall = self._proactive_recall
            logger.info("Proactive recall inicializado")

            return warmup_result
        except Exception as e:
            logger.warning(f"Erro no warm-up de memoria: {e}")
            self._proactive_recall = None
            self._consciencia.proactive_recall = None
            return {"error": str(e)}

    def build_context(self, user_text: str) -> str:
        contexto_memoria = ""
        proactive_context = ""

        try:
            mem_context = self.smart_memory.retrieve(user_text, max_chars=600)
            user_profile = self.smart_memory.get_user_profile_context()

            if self._proactive_recall:
                recall_data = self._proactive_recall.find_relevant_memory(user_text, "")
                if recall_data:
                    proactive_context = self._proactive_recall.format_recall_prompt(recall_data)
                    logger.info(f"Proactive recall: {recall_data.get('trigger_type', 'unknown')}")

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

    def save_interaction(self, user_text: str, response_data: dict) -> None:
        if len(user_text.strip()) > 15:
            self.smart_memory.add(
                f"Usuario disse: {user_text}",
                source="user_input",
                metadata={"type": "user_message"},
            )

        response_summary = response_data.get("fala_tts", "")[:80]
        if len(response_summary) > 20:
            entity_name = get_entity_name(self._consciencia.active_entity_id)
            self.smart_memory.add(
                f"{entity_name} respondeu: {response_summary}",
                source="entity_response",
                metadata={
                    "type": "assistant_message",
                    "animacao": response_data.get("animacao"),
                },
            )

    def update_tiers(self, user_text: str, response_data: dict) -> None:
        response_tts = response_data.get("fala_tts", "")

        self._consciencia.short_term_memory.add(
            content=user_text,
            importance=0.5,
            category="user_input",
        )
        self._consciencia.short_term_memory.add(
            content=response_tts,
            importance=0.6,
            category="luna_response",
        )

        if self._consciencia._interaction_count % 10 == 0:
            result = self._consciencia.memory_tier_manager.promote_all_eligible()
            total_promoted = sum(result.values())
            if total_promoted > 0:
                logger.info(f"Memorias promovidas: {result}")

    def reload_for_entity(self, entity_id: str) -> None:
        self._consciencia.active_entity_id = entity_id
        self._consciencia.smart_memory = get_entity_smart_memory(entity_id)
        self._consciencia.global_memory = get_smart_memory()
        self._proactive_recall = get_proactive_recall(entity_id)
        self._consciencia.proactive_recall = self._proactive_recall
        logger.info(f"Memoria recarregada para entidade: {entity_id}")

    def get_stats(self) -> dict[str, Any]:
        return {
            "entity_id": self._consciencia.active_entity_id,
            "smart_memory_size": len(self.smart_memory._memories) if hasattr(self.smart_memory, "_memories") else 0,
            "proactive_enabled": self._proactive_recall is not None,
        }
