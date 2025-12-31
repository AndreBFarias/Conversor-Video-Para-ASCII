import uuid
from datetime import datetime
from typing import Any

from src.core.logging_config import get_logger

from .memory_interface import (
    MemoryCategory,
    MemoryContext,
    MemoryEntry,
    MemoryHorizon,
    MemoryInterface,
)
from .smart_memory import SmartMemory

logger = get_logger(__name__)


class SmartMemoryAdapter(MemoryInterface):
    def __init__(self, smart_memory: SmartMemory):
        self._sm = smart_memory
        self._category_map = {
            "user_info": MemoryCategory.USER_INFO,
            "preference": MemoryCategory.PREFERENCE,
            "fact": MemoryCategory.FACT,
            "event": MemoryCategory.EVENT,
            "emotion": MemoryCategory.EMOTION,
            "context": MemoryCategory.CONTEXT,
            "task": MemoryCategory.TASK,
        }

    def remember(
        self,
        content: str,
        importance: float = 0.5,
        category: MemoryCategory | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        meta = metadata or {}
        meta["importance"] = importance
        if category:
            meta["category"] = category.value

        return self._sm.add(content, source="user", metadata=meta)

    def recall(self, query: str, limit: int = 5, min_similarity: float = 0.3) -> MemoryContext:
        raw_context = self._sm.retrieve(query)

        context = MemoryContext(max_tokens=800)

        if not raw_context:
            return context

        lines = raw_context.strip().split("\n")
        for line in lines[:limit]:
            if not line.strip() or line.startswith("[MEM]"):
                continue

            entry = MemoryEntry(
                id=str(uuid.uuid4())[:8],
                content=line.strip().lstrip("- "),
                category=MemoryCategory.CONTEXT,
                horizon=MemoryHorizon.MEDIUM,
                importance=0.5,
                timestamp=datetime.now(),
            )
            context.add(entry)

        return context

    def forget(self, memory_id: str) -> bool:
        logger.warning(f"SmartMemory nao suporta delete: {memory_id}")
        return False

    def consolidate(self) -> int:
        return self._sm.compact_old_memories()

    def get_stats(self) -> dict[str, Any]:
        return self._sm.get_stats()

    def flush(self) -> None:
        self._sm.flush()


def get_memory_adapter(entity_id: str) -> MemoryInterface:
    from .smart_memory import get_entity_smart_memory

    sm = get_entity_smart_memory(entity_id)
    return SmartMemoryAdapter(sm)
