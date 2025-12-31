import logging
from datetime import datetime
from typing import Any

import numpy as np

from .search import VectorIndex
from .storage import VectorStorage

logger = logging.getLogger(__name__)


class OptimizedVectorStore:
    def __init__(self, storage_path: str = "src/data_memory/memories.json", auto_save_interval: int = 60):
        self._storage = VectorStorage(storage_path, auto_save_interval)
        self._index = VectorIndex()
        self._index.rebuild(self._storage.memories)

    def add(self, id: str, text: str, vector: np.ndarray, source: str, metadata: dict[str, Any] | None = None) -> None:
        with self._storage.lock:
            if not isinstance(vector, np.ndarray):
                vector = np.array(vector, dtype=np.float32)

            memory = {
                "id": id,
                "text": text,
                "vector": vector,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            self._storage.add_memory(memory)
            self._index.add_vector(vector)

    def search(self, query_vector: np.ndarray, limit: int = 5) -> list[dict[str, Any]]:
        with self._storage.lock:
            return self._index.search(query_vector, self._storage.memories, limit)

    def search_batch(self, query_vectors: np.ndarray, limit: int = 5) -> list[list[dict[str, Any]]]:
        with self._storage.lock:
            return self._index.search_batch(query_vectors, self._storage.memories, limit)

    def delete(self, id: str) -> bool:
        with self._storage.lock:
            if self._storage.delete_memory(id):
                self._index.rebuild(self._storage.memories)
                return True
            return False

    def increment_frequency(self, id: str) -> bool:
        return self._storage.increment_frequency(id)

    def count(self) -> int:
        return self._storage.count()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        return self._storage.get_by_date_range(start_date, end_date)

    def clear_old(self, before_date: datetime) -> int:
        with self._storage.lock:
            deleted_count = self._storage.clear_old(before_date)
            if deleted_count > 0:
                self._index.rebuild(self._storage.memories)
            return deleted_count

    def get_stats(self) -> dict[str, Any]:
        return {
            "count": len(self._storage.memories),
            "matrix_shape": self._index.matrix_shape,
            "indexed": self._index.is_indexed,
            "dirty": self._storage.dirty,
        }

    def stop(self) -> None:
        self._storage.stop()

    def flush(self) -> None:
        self._storage.flush()

    @property
    def memories(self) -> list[dict[str, Any]]:
        return self._storage.memories
