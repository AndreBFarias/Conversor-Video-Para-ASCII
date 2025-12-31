import time

from src.core.logging_config import get_logger
from src.data_memory.cross_entity_memory import get_cross_entity_memory
from src.data_memory.embeddings_cache import get_embeddings_cache
from src.data_memory.smart_memory import get_entity_smart_memory

logger = get_logger(__name__)


class MemoryWarmup:
    def __init__(self):
        self.cache = get_embeddings_cache()
        self.warmed_entities = set()

    def warmup_entity(self, entity_id: str) -> dict:
        start = time.time()
        stats = {"entity": entity_id, "memories_loaded": 0, "embeddings_cached": 0, "time_ms": 0}

        try:
            memory = get_entity_smart_memory(entity_id)
            memory._ensure_loaded()

            if memory._store and hasattr(memory._store, "memories"):
                memories = memory._store.memories
                stats["memories_loaded"] = len(memories)

                important_memories = [
                    m for m in memories if m.get("metadata", {}).get("category") in ["user_info", "preference"]
                ][:20]

                for mem in important_memories:
                    content = mem.get("text", "")
                    if content and len(content) > 10:
                        cached = self.cache.get(content)
                        if cached is None:
                            from src.data_memory.embeddings import get_embedding

                            emb = get_embedding(content)
                            self.cache.set(content, emb)
                            stats["embeddings_cached"] += 1

            self.warmed_entities.add(entity_id)

        except Exception as e:
            logger.error(f"Warmup failed for {entity_id}: {e}")
            stats["error"] = str(e)

        stats["time_ms"] = int((time.time() - start) * 1000)
        logger.info(
            f"Warmup {entity_id}: {stats['memories_loaded']} memories, {stats['embeddings_cached']} cached in {stats['time_ms']}ms"
        )

        return stats

    def warmup_shared(self) -> dict:
        start = time.time()
        stats = {"shared_memories": 0, "time_ms": 0}

        try:
            cem = get_cross_entity_memory()
            shared = cem.get_shared_memories()
            stats["shared_memories"] = len(shared)

            for mem in shared[:10]:
                content = mem.get("content", "")
                if content and len(content) > 10:
                    cached = self.cache.get(content)
                    if cached is None:
                        from src.data_memory.embeddings import get_embedding

                        emb = get_embedding(content)
                        self.cache.set(content, emb)
        except Exception as e:
            logger.error(f"Shared warmup failed: {e}")
            stats["error"] = str(e)

        stats["time_ms"] = int((time.time() - start) * 1000)
        return stats

    def full_warmup(self, active_entity: str) -> dict:
        results = {"active_entity": None, "shared": None, "total_time_ms": 0}

        start = time.time()

        results["active_entity"] = self.warmup_entity(active_entity)
        results["shared"] = self.warmup_shared()

        results["total_time_ms"] = int((time.time() - start) * 1000)

        logger.info(f"Full warmup complete in {results['total_time_ms']}ms")
        return results

    def is_warmed(self, entity_id: str) -> bool:
        return entity_id in self.warmed_entities


_warmup_instance = None


def get_memory_warmup() -> MemoryWarmup:
    global _warmup_instance
    if _warmup_instance is None:
        _warmup_instance = MemoryWarmup()
    return _warmup_instance


def run_startup_warmup(entity_id: str = "luna") -> dict:
    warmup = get_memory_warmup()
    return warmup.full_warmup(entity_id)
