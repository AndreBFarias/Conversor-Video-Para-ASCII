import logging
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class VectorIndex:
    def __init__(self):
        self._vectors_matrix: np.ndarray | None = None
        self._norms: np.ndarray | None = None

    def rebuild(self, memories: list[dict[str, Any]]) -> None:
        if not memories:
            self._vectors_matrix = None
            self._norms = None
            return

        vectors = []
        for mem in memories:
            if "vector" in mem:
                v = mem["vector"]
                if isinstance(v, list):
                    v = np.array(v, dtype=np.float32)
                vectors.append(v)
            else:
                vectors.append(np.zeros(384, dtype=np.float32))

        self._vectors_matrix = np.vstack(vectors) if vectors else None

        if self._vectors_matrix is not None:
            self._norms = np.linalg.norm(self._vectors_matrix, axis=1)
            self._norms[self._norms == 0] = 1.0
        else:
            self._norms = None

    def add_vector(self, vector: np.ndarray) -> None:
        if self._vectors_matrix is None:
            self._vectors_matrix = vector.reshape(1, -1)
            self._norms = np.array([np.linalg.norm(vector) or 1.0])
        else:
            self._vectors_matrix = np.vstack([self._vectors_matrix, vector])
            norm = np.linalg.norm(vector) or 1.0
            self._norms = np.append(self._norms, norm)

    def search(self, query_vector: np.ndarray, memories: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        if not memories or self._vectors_matrix is None:
            return []

        if not isinstance(query_vector, np.ndarray):
            query_vector = np.array(query_vector, dtype=np.float32)

        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []

        similarities = np.dot(self._vectors_matrix, query_vector) / (self._norms * query_norm)

        if limit >= len(memories):
            top_indices = np.argsort(similarities)[::-1]
        else:
            top_indices = np.argpartition(similarities, -limit)[-limit:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        results = []
        for idx in top_indices[:limit]:
            mem = memories[idx]
            results.append(
                {
                    "id": mem["id"],
                    "text": mem["text"],
                    "source": mem["source"],
                    "timestamp": mem["timestamp"],
                    "metadata": mem["metadata"],
                    "similarity": float(similarities[idx]),
                }
            )

        return results

    def search_batch(
        self, query_vectors: np.ndarray, memories: list[dict[str, Any]], limit: int = 5
    ) -> list[list[dict[str, Any]]]:
        if not memories or self._vectors_matrix is None:
            return [[] for _ in range(len(query_vectors))]

        if not isinstance(query_vectors, np.ndarray):
            query_vectors = np.array(query_vectors, dtype=np.float32)

        query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
        query_norms[query_norms == 0] = 1.0

        similarities = np.dot(query_vectors, self._vectors_matrix.T) / (query_norms * self._norms)

        all_results = []
        for q_idx in range(len(query_vectors)):
            q_sims = similarities[q_idx]

            if limit >= len(memories):
                top_indices = np.argsort(q_sims)[::-1]
            else:
                top_indices = np.argpartition(q_sims, -limit)[-limit:]
                top_indices = top_indices[np.argsort(q_sims[top_indices])[::-1]]

            results = []
            for idx in top_indices[:limit]:
                mem = memories[idx]
                results.append(
                    {
                        "id": mem["id"],
                        "text": mem["text"],
                        "source": mem["source"],
                        "timestamp": mem["timestamp"],
                        "metadata": mem["metadata"],
                        "similarity": float(q_sims[idx]),
                    }
                )

            all_results.append(results)

        return all_results

    @property
    def matrix_shape(self) -> tuple | None:
        return self._vectors_matrix.shape if self._vectors_matrix is not None else None

    @property
    def is_indexed(self) -> bool:
        return self._vectors_matrix is not None
