from __future__ import annotations

import logging
import threading
from pathlib import Path

import config

from .core import SmartMemory

logger = logging.getLogger(__name__)

_smart_memory: SmartMemory | None = None
_entity_smart_memories: dict[str, SmartMemory] = {}
_entity_memory_lock = threading.Lock()


def get_smart_memory() -> SmartMemory:
    global _smart_memory
    if _smart_memory is None:
        _smart_memory = SmartMemory()
    return _smart_memory


def get_entity_smart_memory(entity_id: str) -> SmartMemory:
    global _entity_smart_memories

    if entity_id in _entity_smart_memories:
        return _entity_smart_memories[entity_id]

    with _entity_memory_lock:
        if entity_id in _entity_smart_memories:
            return _entity_smart_memories[entity_id]

        try:
            entity_storage_path = str(
                config.APP_DIR / "src" / "data_memory" / "sessions" / entity_id / "smart_memories.json"
            )

            entity_storage_dir = Path(entity_storage_path).parent
            entity_storage_dir.mkdir(parents=True, exist_ok=True)

            memory = SmartMemory.__new__(SmartMemory)
            memory._storage_path = entity_storage_path
            memory._embedding_model = "paraphrase-multilingual-MiniLM-L12-v2"
            memory._max_context_chars = 800
            memory._similarity_threshold = 0.35
            memory._lazy_load = True
            memory._embedder = None
            memory._store = None
            memory._category_index = {}
            memory._summary_cache = {}
            memory._initialized = True
            memory._loaded = False

            from .categorizer import MemoryCategorizer

            memory._categorizer = MemoryCategorizer()

            _entity_smart_memories[entity_id] = memory
            logger.info(f"SmartMemory criado para entidade: {entity_id}")
        except Exception as e:
            from src.data_memory import MemoryLoadError

            raise MemoryLoadError(f"Nao foi possivel criar SmartMemory para {entity_id}: {e}") from e

    return _entity_smart_memories[entity_id]


def switch_smart_memory_entity(new_entity_id: str) -> SmartMemory:
    return get_entity_smart_memory(new_entity_id)
