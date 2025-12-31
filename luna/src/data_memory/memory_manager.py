import hashlib
import logging
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any

from .embeddings import EmbeddingGenerator
from .vector_store_optimized import OptimizedVectorStore

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.lower().strip().encode()).hexdigest()

    def get(self, text: str):
        key = self._hash(text)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["ts"] < self.ttl_seconds:
                self.cache.move_to_end(key)
                return entry["vec"]
            del self.cache[key]
        return None

    def set(self, text: str, vector):
        key = self._hash(text)
        self.cache[key] = {"vec": vector, "ts": time.time()}
        self.cache.move_to_end(key)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


class MemoryManager:
    def __init__(self, storage_path: str = "src/data_memory/memories.json", embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_gen = EmbeddingGenerator(model_name=embedding_model)
        self.vector_store = OptimizedVectorStore(storage_path=storage_path, auto_save_interval=30)
        self.embedding_cache = EmbeddingCache(max_size=500, ttl_seconds=3600)
        self.min_text_length = 20
        self.dedup_threshold = 0.92
        self.min_similarity = 0.40

        logger.info("MemoryManager inicializado (optimized store, embedding cache)")

    def _get_embedding(self, text: str):
        cached = self.embedding_cache.get(text)
        if cached is not None:
            return cached
        vector = self.embedding_gen.encode(text)
        self.embedding_cache.set(text, vector)
        return vector

    def add_memory(self, text: str, source: str = "user_input", metadata: dict[str, Any] | None = None) -> str | None:
        if not self._is_valid_memory(text):
            logger.debug(f"Memoria rejeitada (sanitizacao): '{text[:50]}...'")
            return None

        text = text.strip()
        vector = self._get_embedding(text)

        existing_id = self._find_duplicate(vector)
        if existing_id:
            self.vector_store.increment_frequency(existing_id)
            logger.debug(f"Memoria duplicada, frequencia incrementada: {existing_id}")
            return existing_id

        memory_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["frequency"] = 1

        self.vector_store.add(id=memory_id, text=text, vector=vector, source=source, metadata=meta)

        logger.info(f"Nova memoria adicionada: {memory_id[:8]}... (source: {source})")
        return memory_id

    def retrieve_context(self, query: str, max_results: int = 50, min_similarity: float | None = None) -> str:
        if not query or len(query.strip()) < 3:
            return ""

        threshold = min_similarity if min_similarity is not None else self.min_similarity

        query_vector = self._get_embedding(query)
        results = self.vector_store.search(query_vector, limit=max_results)

        filtered = [r for r in results if r["similarity"] >= threshold]

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
            timestamp = mem["timestamp"][:10]
            context_parts.append(f"-{marker} [{timestamp}] {mem['text']}")

        context = "\n".join(context_parts)
        logger.info(f"Contexto recuperado: {len(final_list)} memorias (3+3 hibrido)")
        return context

    def search_by_date(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        return self.vector_store.get_by_date_range(start_date, end_date)

    def clear_old_memories(self, days: int = 90) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = self.vector_store.clear_old(cutoff_date)

        if deleted_count > 0:
            logger.info(f"Limpadas {deleted_count} memorias antigas (>{days} dias)")

        return deleted_count

    def get_stats(self) -> dict[str, Any]:
        total_memories = self.vector_store.count()

        stats = {
            "total_memories": total_memories,
            "embedding_model": self.embedding_gen.model_name,
            "vector_dimension": self.embedding_gen.dimension,
            "storage_backend": "JSON",
            "dedup_threshold": self.dedup_threshold,
            "min_similarity": self.min_similarity,
            "retrieval_mode": "hybrid_3+3",
        }

        return stats

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

    def _find_duplicate(self, vector) -> str | None:
        results = self.vector_store.search(vector, limit=1)

        if results and results[0]["similarity"] >= self.dedup_threshold:
            return results[0]["id"]

        return None

    def get_stats(self) -> dict[str, Any]:
        total_memories = self.vector_store.count()
        store_stats = self.vector_store.get_stats()

        stats = {
            "total_memories": total_memories,
            "embedding_model": self.embedding_gen.model_name,
            "vector_dimension": self.embedding_gen.dimension,
            "storage_backend": "OptimizedVectorStore",
            "dedup_threshold": self.dedup_threshold,
            "min_similarity": self.min_similarity,
            "retrieval_mode": "hybrid_3+3",
            "embedding_cache_size": len(self.embedding_cache.cache),
            "indexed": store_stats.get("indexed", False),
        }

        return stats

    def flush(self) -> None:
        self.vector_store.flush()

    def stop(self) -> None:
        self.vector_store.stop()
