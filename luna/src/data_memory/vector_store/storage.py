import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class VectorStorage:
    def __init__(self, storage_path: str = "src/data_memory/memories.json", auto_save_interval: int = 60):
        self.storage_path = storage_path
        self.memories: list[dict[str, Any]] = []

        self._lock = threading.RLock()
        self._save_interval = auto_save_interval
        self._save_thread: threading.Thread | None = None
        self._running = False
        self._dirty = False

        self._ensure_storage_directory()
        self._load_from_disk()
        self._start_auto_save()

    def _ensure_storage_directory(self) -> None:
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load_from_disk(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    data = json.load(f)

                    if isinstance(data, list):
                        raw_memories = data
                    else:
                        raw_memories = data.get("memories", [])

                    self.memories = []
                    for mem in raw_memories:
                        if "vector" in mem and isinstance(mem["vector"], list):
                            mem["vector"] = np.array(mem["vector"], dtype=np.float32)
                        self.memories.append(mem)

                    logger.info(f"Carregadas {len(self.memories)} memorias do disco")

            except Exception as e:
                logger.error(f"Erro ao carregar memorias: {e}")
                self.memories = []

    def _save_to_disk(self, force: bool = False) -> None:
        with self._lock:
            if not self._dirty and not force:
                return

            try:
                data_to_save = {
                    "memories": [
                        {
                            **{k: v for k, v in mem.items() if k != "vector"},
                            "vector": mem["vector"].tolist()
                            if isinstance(mem["vector"], np.ndarray)
                            else mem["vector"],
                        }
                        for mem in self.memories
                    ],
                    "last_updated": datetime.now().isoformat(),
                    "count": len(self.memories),
                }

                temp_path = self.storage_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, ensure_ascii=False)

                os.replace(temp_path, self.storage_path)
                self._dirty = False
                logger.debug(f"Memorias salvas: {len(self.memories)}")

            except Exception as e:
                logger.error(f"Erro ao salvar memorias: {e}")

    def _start_auto_save(self) -> None:
        if self._running:
            return

        self._running = True
        self._save_thread = threading.Thread(target=self._auto_save_loop, daemon=True, name="VectorStoreAutoSave")
        self._save_thread.start()

    def _auto_save_loop(self) -> None:
        while self._running:
            time.sleep(self._save_interval)
            if self._dirty:
                self._save_to_disk()

    def stop(self) -> None:
        self._running = False
        if self._save_thread:
            self._save_thread.join(timeout=5)
        self._save_to_disk(force=True)

    def flush(self) -> None:
        self._save_to_disk(force=True)

    def add_memory(self, memory: dict[str, Any]) -> None:
        with self._lock:
            self.memories.append(memory)
            self._dirty = True

    def delete_memory(self, id: str) -> bool:
        with self._lock:
            for i, mem in enumerate(self.memories):
                if mem["id"] == id:
                    self.memories.pop(i)
                    self._dirty = True
                    return True
            return False

    def increment_frequency(self, id: str) -> bool:
        with self._lock:
            for mem in self.memories:
                if mem["id"] == id:
                    if "metadata" not in mem:
                        mem["metadata"] = {}
                    current = mem["metadata"].get("frequency", 0)
                    mem["metadata"]["frequency"] = current + 1
                    self._dirty = True
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
        with self._lock:
            initial_count = len(self.memories)
            self.memories = [m for m in self.memories if datetime.fromisoformat(m["timestamp"]) >= before_date]

            deleted_count = initial_count - len(self.memories)
            if deleted_count > 0:
                self._dirty = True

            return deleted_count

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool):
        self._dirty = value
