"""
Memory Tier Manager - Orquestra promocao entre tiers.

Tres niveis de memoria:
- SHORT (5 min): Buffer volatil, expira automaticamente
- MEDIUM (24h): Memorias importantes da sessao
- LONG (permanente): Fatos consolidados sobre o usuario

Promocao automatica baseada em:
- Importancia >= 0.7
- Acessos frequentes >= 2
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

from src.core.constants import MemoryConstants, SessionConstants
from src.core.logging_config import get_logger
from src.data_memory.memory_interface import MemoryCategory, MemoryHorizon
from src.data_memory.short_term_memory import ShortTermEntry, get_short_term_memory

logger = get_logger(__name__)


class MemoryTierManager:
    """Gerencia promocao de memorias entre tiers."""

    PROMOTION_INTERVAL = SessionConstants.CONSOLIDATION_INTERVAL_MINUTES * 60
    HIGH_IMPORTANCE_THRESHOLD = 0.7
    MEDIUM_IMPORTANCE_THRESHOLD = 0.5

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self._lock = threading.Lock()
        self._last_promotion = 0.0
        self._running = False
        self._promotion_thread: threading.Thread | None = None

        self._stats = {
            "short_to_medium": 0,
            "medium_to_long": 0,
            "auto_promotions": 0,
            "manual_promotions": 0,
        }

        logger.info(f"MemoryTierManager inicializado para {entity_id}")

    def add_short_term(
        self,
        content: str,
        importance: float = 0.5,
        category: str = "context",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        stm = get_short_term_memory(self.entity_id)
        entry_id = stm.add(content, importance, category, metadata)

        if importance >= self.HIGH_IMPORTANCE_THRESHOLD:
            self._schedule_quick_promotion(entry_id)

        return entry_id

    def _schedule_quick_promotion(self, entry_id: str) -> None:
        def promote_after_delay():
            time.sleep(30)
            self._promote_entry(entry_id)

        thread = threading.Thread(target=promote_after_delay, daemon=True)
        thread.start()

    def _promote_entry(self, entry_id: str) -> bool:
        stm = get_short_term_memory(self.entity_id)

        with self._lock:
            for entry in stm._buffer:
                if entry.id == entry_id:
                    success = self._store_medium_term(entry)
                    if success:
                        stm.mark_promoted(entry_id)
                        self._stats["short_to_medium"] += 1
                        logger.debug(f"Promoted {entry_id} to medium-term")
                        return True
                    break

        return False

    def _store_medium_term(self, entry: ShortTermEntry) -> bool:
        try:
            from src.data_memory.smart_memory import get_entity_smart_memory

            memory = get_entity_smart_memory(self.entity_id)

            mem_id = memory.add(
                text=entry.content,
                source=entry.category,
                importance=entry.importance,
                metadata={
                    **entry.metadata,
                    "horizon": MemoryHorizon.MEDIUM.value,
                    "promoted_from": "short_term",
                    "original_timestamp": entry.timestamp,
                    "access_count": entry.access_count,
                },
            )

            return mem_id is not None

        except Exception as e:
            logger.error(f"Falha ao promover para medium-term: {e}")
            return False

    def promote_all_eligible(self) -> dict[str, int]:
        stm = get_short_term_memory(self.entity_id)
        promotable = stm.get_promotable()

        promoted_count = 0
        failed_count = 0

        for entry in promotable:
            if self._promote_entry(entry.id):
                promoted_count += 1
            else:
                failed_count += 1

        self._stats["auto_promotions"] += promoted_count
        self._last_promotion = time.time()

        logger.info(f"Promocao em lote: {promoted_count} promovidas, {failed_count} falhas")

        return {
            "promoted": promoted_count,
            "failed": failed_count,
            "remaining": len(stm),
        }

    def consolidate_medium_to_long(self) -> dict[str, Any]:
        try:
            from src.data_memory.memory_consolidator import MemoryConsolidator

            consolidator = MemoryConsolidator(self.entity_id)
            result = consolidator.consolidate()

            if result.get("consolidated", 0) > 0:
                self._stats["medium_to_long"] += result["consolidated"]

            return result

        except Exception as e:
            logger.error(f"Falha na consolidacao medium->long: {e}")
            return {"status": "error", "error": str(e)}

    def start_auto_promotion(self) -> None:
        if self._running:
            return

        self._running = True

        def promotion_loop():
            while self._running:
                try:
                    elapsed = time.time() - self._last_promotion
                    if elapsed >= self.PROMOTION_INTERVAL:
                        self.promote_all_eligible()
                except Exception as e:
                    logger.error(f"Erro no loop de promocao: {e}")

                time.sleep(60)

        self._promotion_thread = threading.Thread(target=promotion_loop, daemon=True)
        self._promotion_thread.start()
        logger.info(f"Auto-promotion thread iniciada (intervalo: {self.PROMOTION_INTERVAL}s)")

    def stop_auto_promotion(self) -> None:
        self._running = False
        if self._promotion_thread:
            self._promotion_thread.join(timeout=5)
            self._promotion_thread = None
        logger.info("Auto-promotion thread parada")

    def recall_across_tiers(
        self,
        query: str,
        include_short: bool = True,
        include_medium: bool = True,
        include_long: bool = True,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        results = []

        if include_short:
            stm = get_short_term_memory(self.entity_id)
            short_results = stm.get(query, limit=limit // 3 or 3)
            for entry in short_results:
                results.append(
                    {
                        "content": entry.content,
                        "tier": "short",
                        "importance": entry.importance,
                        "timestamp": entry.timestamp,
                        "access_count": entry.access_count,
                    }
                )

        if include_medium or include_long:
            try:
                from src.data_memory.smart_memory import get_entity_smart_memory

                memory = get_entity_smart_memory(self.entity_id)
                context = memory.retrieve(query)

                if context:
                    for line in context.split("\n"):
                        if line.startswith("-"):
                            results.append(
                                {
                                    "content": line[2:].strip(),
                                    "tier": "medium/long",
                                    "importance": 0.5,
                                    "timestamp": time.time(),
                                    "access_count": 1,
                                }
                            )

            except Exception as e:
                logger.error(f"Erro ao buscar medium/long: {e}")

        results.sort(key=lambda x: (x["importance"], x["timestamp"]), reverse=True)
        return results[:limit]

    def get_tier_stats(self) -> dict[str, Any]:
        stm = get_short_term_memory(self.entity_id)
        stm_stats = stm.get_stats()

        try:
            from src.data_memory.smart_memory import get_entity_smart_memory

            memory = get_entity_smart_memory(self.entity_id)
            long_term_stats = memory.get_stats()
        except Exception:
            long_term_stats = {}

        return {
            "entity_id": self.entity_id,
            "short_term": stm_stats,
            "long_term": long_term_stats,
            "promotion_stats": self._stats,
            "last_promotion": self._last_promotion,
            "auto_promotion_active": self._running,
        }

    def force_promotion(self, entry_id: str) -> bool:
        success = self._promote_entry(entry_id)
        if success:
            self._stats["manual_promotions"] += 1
        return success

    def clear_short_term(self) -> None:
        stm = get_short_term_memory(self.entity_id)
        stm.clear()
        logger.info(f"Short-term memory cleared for {self.entity_id}")


_tier_managers: dict[str, MemoryTierManager] = {}
_manager_lock = threading.Lock()


def get_tier_manager(entity_id: str = "default") -> MemoryTierManager:
    global _tier_managers
    if entity_id not in _tier_managers:
        with _manager_lock:
            if entity_id not in _tier_managers:
                _tier_managers[entity_id] = MemoryTierManager(entity_id)
    return _tier_managers[entity_id]


def start_all_auto_promotion() -> None:
    for manager in _tier_managers.values():
        manager.start_auto_promotion()


def stop_all_auto_promotion() -> None:
    for manager in _tier_managers.values():
        manager.stop_auto_promotion()
