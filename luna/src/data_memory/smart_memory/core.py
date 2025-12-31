from __future__ import annotations

import hashlib
import logging
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Any

import config
from src.core.constants import MemoryConstants

from ..embeddings import EmbeddingGenerator
from ..emotional_tagger import get_primary_emotion, tag_emotion
from ..vector_store_optimized import OptimizedVectorStore
from .categorizer import MemoryCategorizer
from .constants import MemoryCategory
from .models import MemorySlice

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SmartMemory:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        storage_path: str | None = None,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        max_context_chars: int = MemoryConstants.MAX_CONTEXT_CHARS,
        similarity_threshold: float = MemoryConstants.SIMILARITY_THRESHOLD,
        lazy_load: bool = True,
    ):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._storage_path = storage_path or str(config.APP_DIR / "src" / "data_memory" / "memories.json")
        self._embedding_model = embedding_model
        self._max_context_chars = max_context_chars
        self._similarity_threshold = similarity_threshold
        self._lazy_load = lazy_load

        self._embedder: EmbeddingGenerator | None = None
        self._store: OptimizedVectorStore | None = None
        self._category_index: dict[str, list[str]] = {}
        self._summary_cache: dict[str, str] = {}
        self._categorizer = MemoryCategorizer()

        self._initialized = True
        self._loaded = False

        if not lazy_load:
            self._ensure_loaded()

        logger.info(f"SmartMemory inicializado (lazy={lazy_load}, threshold={similarity_threshold})")

    def _ensure_loaded(self):
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            try:
                self._embedder = EmbeddingGenerator(model_name=self._embedding_model)
                self._store = OptimizedVectorStore(storage_path=self._storage_path, auto_save_interval=30)
                self._build_category_index()
                self._loaded = True
                logger.info(f"SmartMemory carregado: {self._store.count()} memorias")
            except Exception as e:
                self._loaded = False
                from src.data_memory import MemoryLoadError

                raise MemoryLoadError(f"Nao foi possivel carregar memoria: {e}") from e

    def _build_category_index(self):
        self._category_index = {cat.value: [] for cat in MemoryCategory}

        for mem in self._store.memories:
            cat = self._categorizer.detect_category(mem.get("text", ""))
            self._category_index[cat.value].append(mem["id"])
            self._summary_cache[mem["id"]] = self._categorizer.generate_summary(mem.get("text", ""))

    def add(
        self,
        text: str,
        source: str = "user",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        self._ensure_loaded()

        if not text or len(text.strip()) < 15:
            return None

        text = text.strip()
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]

        vector = self._embedder.encode(text)

        existing = self._store.search(vector, limit=1)
        if existing and existing[0]["similarity"] > 0.92:
            self._store.increment_frequency(existing[0]["id"])
            return existing[0]["id"]

        mem_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{text_hash}"
        category = self._categorizer.detect_category(text)

        emotion_tags = tag_emotion(text)
        primary_emotion, emotion_score = get_primary_emotion(text)

        meta = metadata or {}
        meta["category"] = category.value
        meta["frequency"] = 1
        meta["importance"] = importance
        meta["emotion_tags"] = emotion_tags
        meta["primary_emotion"] = primary_emotion
        meta["emotion_score"] = emotion_score

        self._store.add(id=mem_id, text=text, vector=vector, source=source, metadata=meta)

        self._category_index[category.value].append(mem_id)
        self._summary_cache[mem_id] = self._categorizer.generate_summary(text)

        logger.debug(f"Memoria adicionada: {mem_id[:20]}... [{category.value}]")
        return mem_id

    def retrieve(
        self,
        query: str,
        max_chars: int | None = None,
        categories: list[MemoryCategory] | None = None,
        boost_recent: bool = True,
    ) -> str:
        from . import retriever

        return retriever.retrieve(self, query, max_chars, categories, boost_recent)

    def retrieve_by_category(self, category: MemoryCategory, limit: int = 5) -> list[MemorySlice]:
        from . import retriever

        return retriever.retrieve_by_category(self, category, limit)

    def get_user_profile_context(self) -> str:
        from . import retriever

        return retriever.get_user_profile_context(self)

    def recall_emotional(self, current_emotion: str, max_results: int = 3) -> list[dict]:
        from . import retriever

        return retriever.recall_emotional(self, current_emotion, max_results)

    def get_stats(self) -> dict[str, Any]:
        self._ensure_loaded()

        category_counts = {cat: len(ids) for cat, ids in self._category_index.items() if isinstance(ids, list)}

        return {
            "total_memories": self._store.count(),
            "categories": category_counts,
            "max_context_chars": self._max_context_chars,
            "similarity_threshold": self._similarity_threshold,
            "embedding_model": self._embedding_model,
            "loaded": self._loaded,
        }

    def warm_up(self) -> None:
        self._ensure_loaded()
        _ = self._embedder.encode("warmup query para carregar modelo")
        logger.info("SmartMemory warm-up completo")

    def migrate_legacy_memories(self) -> int:
        from . import maintenance

        return maintenance.migrate_legacy_memories(self)

    def compact_old_memories(self, days_threshold: int = 30, min_frequency: int = 1) -> int:
        from . import maintenance

        return maintenance.compact_old_memories(self, days_threshold, min_frequency)

    def clear_old_memories(self, days: int = 90) -> int:
        from . import maintenance

        return maintenance.clear_old_memories(self, days)

    def stop(self) -> None:
        if self._store:
            self._store.stop()

    def flush(self) -> None:
        if self._store:
            self._store.flush()
