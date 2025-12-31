import hashlib
import pickle
import sqlite3
from pathlib import Path

import numpy as np

from src.core.logging_config import get_logger

logger = get_logger(__name__)

CACHE_PATH = Path("src/data_memory/cache/embeddings.db")


class EmbeddingsCache:
    def __init__(self):
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(CACHE_PATH), check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:32]

    def get(self, text: str) -> np.ndarray | None:
        text_hash = self._hash_text(text)
        cursor = self.conn.execute("SELECT embedding FROM embeddings WHERE text_hash = ?", (text_hash,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    def set(self, text: str, embedding: np.ndarray):
        text_hash = self._hash_text(text)
        embedding_blob = pickle.dumps(embedding)
        self.conn.execute(
            "INSERT OR REPLACE INTO embeddings (text_hash, embedding) VALUES (?, ?)", (text_hash, embedding_blob)
        )
        self.conn.commit()

    def get_or_compute(self, text: str, compute_fn) -> np.ndarray:
        cached = self.get(text)
        if cached is not None:
            return cached

        embedding = compute_fn(text)
        self.set(text, embedding)
        return embedding

    def clear_old(self, days: int = 30):
        self.conn.execute("DELETE FROM embeddings WHERE created_at < datetime('now', ?)", (f"-{days} days",))
        self.conn.commit()

    def get_stats(self) -> dict:
        cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        return {"total_entries": count, "db_path": str(CACHE_PATH)}


_cache_instance: EmbeddingsCache | None = None


def get_embeddings_cache() -> EmbeddingsCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingsCache()
    return _cache_instance
