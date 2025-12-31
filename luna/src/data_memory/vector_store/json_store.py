import json
import logging
import os
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class JSONVectorStore:
    def __init__(self, storage_path: str = "src/data_memory/memories.json"):
        self.storage_path = storage_path
        self.memories: list[dict[str, Any]] = []
        self._ensure_storage_directory()
        self._load_from_disk()

    def _ensure_storage_directory(self) -> None:
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load_from_disk(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = data.get("memories", [])
                    for mem in self.memories:
                        if "vector" in mem and isinstance(mem["vector"], list):
                            mem["vector"] = np.array(mem["vector"], dtype=np.float32)
                logger.info(f"Carregadas {len(self.memories)} memórias do disco")
            except Exception as e:
                logger.error(f"Erro ao carregar memórias: {e}")
                self.memories = []

    def _save_to_disk(self) -> None:
        try:
            data_to_save = {
                "memories": [
                    {
                        **mem,
                        "vector": mem["vector"].tolist() if isinstance(mem["vector"], np.ndarray) else mem["vector"],
                    }
                    for mem in self.memories
                ],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Erro ao salvar memórias: {e}")

    def add(self, id: str, text: str, vector: np.ndarray, source: str, metadata: dict[str, Any] | None = None) -> None:
        memory = {
            "id": id,
            "text": text,
            "vector": vector,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.memories.append(memory)
        self._save_to_disk()

    def search(self, query_vector: np.ndarray, limit: int = 5) -> list[dict[str, Any]]:
        if not self.memories:
            return []

        results = []
        for mem in self.memories:
            similarity = self._cosine_similarity(query_vector, mem["vector"])
            results.append(
                {
                    "id": mem["id"],
                    "text": mem["text"],
                    "source": mem["source"],
                    "timestamp": mem["timestamp"],
                    "metadata": mem["metadata"],
                    "similarity": float(similarity),
                }
            )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def delete(self, id: str) -> bool:
        initial_count = len(self.memories)
        self.memories = [m for m in self.memories if m["id"] != id]

        if len(self.memories) < initial_count:
            self._save_to_disk()
            return True
        return False

    def increment_frequency(self, id: str) -> bool:
        for mem in self.memories:
            if mem["id"] == id:
                if "metadata" not in mem:
                    mem["metadata"] = {}
                current = mem["metadata"].get("frequency", 0)
                mem["metadata"]["frequency"] = current + 1
                self._save_to_disk()
                return True
        return False

    def count(self) -> int:
        return len(self.memories)

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        results = []
        for mem in self.memories:
            try:
                mem_date = datetime.fromisoformat(mem["timestamp"])
                if start_date <= mem_date <= end_date:
                    results.append(
                        {
                            "id": mem["id"],
                            "text": mem["text"],
                            "source": mem["source"],
                            "timestamp": mem["timestamp"],
                            "metadata": mem["metadata"],
                        }
                    )
            except Exception as e:
                logger.warning(f"Erro ao parsear timestamp: {e}")
                continue

        return results

    def clear_old(self, before_date: datetime) -> int:
        initial_count = len(self.memories)
        self.memories = [m for m in self.memories if datetime.fromisoformat(m["timestamp"]) >= before_date]

        deleted_count = initial_count - len(self.memories)
        if deleted_count > 0:
            self._save_to_disk()

        return deleted_count

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        if vec1.shape != vec2.shape:
            return 0.0

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))
