import hashlib
import logging
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.core.constants import CacheConstants, MemoryConstants

from .embeddings import EmbeddingGenerator
from .vector_store_optimized import OptimizedVectorStore

logger = logging.getLogger(__name__)

_shared_embedding_gen: EmbeddingGenerator | None = None
_embedding_lock = threading.Lock()


def _get_shared_embedding_gen(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingGenerator:
    global _shared_embedding_gen
    if _shared_embedding_gen is None:
        with _embedding_lock:
            if _shared_embedding_gen is None:
                try:
                    _shared_embedding_gen = EmbeddingGenerator(model_name=model_name)
                    logger.info(f"EmbeddingGenerator compartilhado inicializado: {model_name}")
                except Exception as e:
                    from src.data_memory import MemoryLoadError

                    raise MemoryLoadError(f"Nao foi possivel carregar EmbeddingGenerator: {e}") from e
    return _shared_embedding_gen


class EntityMemoryManager:
    GLOBAL_SOURCES = ["user_profile", "face_recognition", "preference", "fact"]
    SESSION_SOURCES = ["conversation", "user_input", "luna_response", "entity_interaction"]

    def __init__(self, entity_id: str, base_path: str = "src/data_memory", embedding_model: str = "all-MiniLM-L6-v2"):
        self.entity_id = entity_id
        self.base_path = Path(base_path)
        self.embedding_gen = _get_shared_embedding_gen(embedding_model)
        self._embedding_cache: OrderedDict = OrderedDict()
        self._cache_max_size = CacheConstants.ENTITY_CACHE_MAX_SIZE
        self._cache_ttl = CacheConstants.ENTITY_CACHE_TTL

        self.global_store = OptimizedVectorStore(
            storage_path=str(self.base_path / "global_memories.json"), auto_save_interval=30
        )

        entity_memory_path = self.base_path / "sessions" / entity_id / "memories.json"
        entity_memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.entity_store = OptimizedVectorStore(storage_path=str(entity_memory_path), auto_save_interval=30)

        self.min_text_length = MemoryConstants.MIN_TEXT_LENGTH
        self.dedup_threshold = MemoryConstants.DEDUP_THRESHOLD
        self.min_similarity = MemoryConstants.MIN_SIMILARITY

        logger.info(f"EntityMemoryManager inicializado para {entity_id}")
        logger.info(f"  Global: {self.global_store.count()} memorias")
        logger.info(f"  {entity_id}: {self.entity_store.count()} memorias")

    def _get_cached_embedding(self, text: str):
        key = hashlib.md5(text.lower().strip().encode()).hexdigest()
        if key in self._embedding_cache:
            entry = self._embedding_cache[key]
            if time.time() - entry["ts"] < self._cache_ttl:
                self._embedding_cache.move_to_end(key)
                return entry["vec"]
            del self._embedding_cache[key]

        vector = self.embedding_gen.encode(text)
        self._embedding_cache[key] = {"vec": vector, "ts": time.time()}
        self._embedding_cache.move_to_end(key)
        while len(self._embedding_cache) > self._cache_max_size:
            self._embedding_cache.popitem(last=False)
        return vector

    def add_memory(self, text: str, source: str = "user_input", metadata: dict[str, Any] | None = None) -> str | None:
        if not self._is_valid_memory(text):
            logger.debug(f"Memoria rejeitada: '{text[:50]}...'")
            return None

        text = text.strip()
        vector = self._get_cached_embedding(text)

        store = self._get_store_for_source(source)

        existing_id = self._find_duplicate(vector, store)
        if existing_id:
            store.increment_frequency(existing_id)
            logger.debug(f"Memoria duplicada, frequencia incrementada: {existing_id}")
            return existing_id

        memory_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["frequency"] = 1
        meta["entity_origin"] = self.entity_id

        store.add(id=memory_id, text=text, vector=vector, source=source, metadata=meta)

        logger.info(
            f"Nova memoria adicionada: {memory_id[:8]}... (source: {source}, store: {'global' if store == self.global_store else self.entity_id})"
        )
        return memory_id

    def _get_store_for_source(self, source: str) -> OptimizedVectorStore:
        if source in self.GLOBAL_SOURCES:
            return self.global_store
        return self.entity_store

    def retrieve_context(
        self,
        query: str,
        max_results: int = 50,
        min_similarity: float | None = None,
        include_global: bool = True,
        include_entity: bool = True,
    ) -> str:
        if not query or len(query.strip()) < 3:
            return ""

        threshold = min_similarity if min_similarity is not None else self.min_similarity
        query_vector = self._get_cached_embedding(query)

        all_results = []

        if include_global:
            global_results = self.global_store.search(query_vector, limit=max_results)
            for r in global_results:
                r["store"] = "global"
            all_results.extend(global_results)

        if include_entity:
            entity_results = self.entity_store.search(query_vector, limit=max_results)
            for r in entity_results:
                r["store"] = self.entity_id
            all_results.extend(entity_results)

        filtered = [r for r in all_results if r["similarity"] >= threshold]

        if not filtered:
            return ""

        top_similar = sorted(filtered, key=lambda x: x["similarity"], reverse=True)[:3]
        similar_ids = {m["id"] for m in top_similar}

        remaining = [m for m in filtered if m["id"] not in similar_ids]
        top_recent = sorted(remaining, key=lambda x: x["timestamp"], reverse=True)[:3]

        final_list = sorted(top_similar + top_recent, key=lambda x: x["timestamp"])

        context_parts = ["=== BIBLIOTECA DAS PALAVRAS CONJURADAS ==="]
        for mem in final_list:
            freq = mem.get("metadata", {}).get("frequency", 1)
            marker = " [SAGRADO]" if freq > 5 else ""
            store_marker = f"[{mem['store'].upper()}]" if mem["store"] == "global" else ""
            timestamp = mem["timestamp"][:10]
            context_parts.append(f"-{marker}{store_marker} [{timestamp}] {mem['text']}")

        context = "\n".join(context_parts)
        logger.info(f"Contexto recuperado: {len(final_list)} memorias (hibrido global+{self.entity_id})")
        return context

    def retrieve_entity_only(self, query: str, max_results: int = 20, min_similarity: float | None = None) -> str:
        return self.retrieve_context(
            query=query,
            max_results=max_results,
            min_similarity=min_similarity,
            include_global=False,
            include_entity=True,
        )

    def retrieve_global_only(self, query: str, max_results: int = 20, min_similarity: float | None = None) -> str:
        return self.retrieve_context(
            query=query,
            max_results=max_results,
            min_similarity=min_similarity,
            include_global=True,
            include_entity=False,
        )

    def add_user_fact(self, fact: str, category: str = "general") -> str | None:
        return self.add_memory(text=fact, source="fact", metadata={"category": category, "type": "user_fact"})

    def add_user_preference(self, preference: str, domain: str = "general") -> str | None:
        return self.add_memory(
            text=preference, source="preference", metadata={"domain": domain, "type": "user_preference"}
        )

    def add_conversation_memory(self, text: str, role: str = "user") -> str | None:
        source = "user_input" if role == "user" else "luna_response"
        return self.add_memory(text=text, source=source, metadata={"role": role, "session_entity": self.entity_id})

    def get_stats(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "global_memories": self.global_store.count(),
            "entity_memories": self.entity_store.count(),
            "total_memories": self.global_store.count() + self.entity_store.count(),
            "embedding_model": self.embedding_gen.model_name,
            "vector_dimension": self.embedding_gen.dimension,
            "storage_backend": "OptimizedVectorStore",
            "dedup_threshold": self.dedup_threshold,
            "min_similarity": self.min_similarity,
            "retrieval_mode": "hybrid_global_entity",
            "embedding_cache_size": len(self._embedding_cache),
            "global_indexed": self.global_store.get_stats().get("indexed", False),
            "entity_indexed": self.entity_store.get_stats().get("indexed", False),
        }

    def clear_entity_memories(self, days: int | None = None) -> int:
        if days is None:
            count = self.entity_store.count()
            self.entity_store.memories = []
            self.entity_store._rebuild_index()
            self.entity_store.flush()
            logger.info(f"Limpadas {count} memorias da entidade {self.entity_id}")
            return count
        else:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = self.entity_store.clear_old(cutoff_date)
            logger.info(f"Limpadas {deleted_count} memorias antigas (>{days} dias) de {self.entity_id}")
            return deleted_count

    def switch_entity(self, new_entity_id: str) -> "EntityMemoryManager":
        logger.info(f"Trocando contexto de memoria: {self.entity_id} -> {new_entity_id}")
        return EntityMemoryManager(
            entity_id=new_entity_id, base_path=str(self.base_path), embedding_model=self.embedding_gen.model_name
        )

    def _is_valid_memory(self, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False

        text = text.strip()

        if len(text) < self.min_text_length:
            return False

        filler_phrases = [
            "ok",
            "oi",
            "ola",
            "tudo bem",
            "obrigado",
            "valeu",
            "entendi",
            "certo",
            "sim",
            "nao",
            "hum",
            "ahh",
        ]

        if text.lower() in filler_phrases:
            return False

        if text.startswith("/") or text.startswith("!"):
            return False

        return True

    def _find_duplicate(self, vector, store: OptimizedVectorStore) -> str | None:
        results = store.search(vector, limit=1)

        if results and results[0]["similarity"] >= self.dedup_threshold:
            return results[0]["id"]

        return None

    def stop(self) -> None:
        self.global_store.stop()
        self.entity_store.stop()

    def flush(self) -> None:
        self.global_store.flush()
        self.entity_store.flush()


_entity_memory_managers: dict[str, EntityMemoryManager] = {}


def get_entity_memory(entity_id: str) -> EntityMemoryManager:
    global _entity_memory_managers

    if entity_id not in _entity_memory_managers:
        _entity_memory_managers[entity_id] = EntityMemoryManager(entity_id)

    return _entity_memory_managers[entity_id]


def switch_entity_memory(old_entity_id: str, new_entity_id: str) -> EntityMemoryManager:
    return get_entity_memory(new_entity_id)
