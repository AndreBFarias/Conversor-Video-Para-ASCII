import hashlib
import json
import logging
import sqlite3
import time
from collections import OrderedDict
from threading import Lock
from typing import Any

import config
from src.core.constants import CacheConstants

logger = logging.getLogger(__name__)

L2_CACHE_DB = config.APP_DIR / "src" / "data_memory" / "cache" / "semantic_l2.db"


class SemanticCache:
    def __init__(
        self,
        similarity_threshold: float = CacheConstants.SIMILARITY_THRESHOLD,
        max_size: int = CacheConstants.MAX_SIZE,
        ttl_seconds: int = CacheConstants.L1_TTL_SECONDS,
        enable_l2: bool = True,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.l2_ttl_seconds = ttl_seconds * 12
        self.l2_enabled = enable_l2

        self.cache_l1: OrderedDict = OrderedDict()
        self._lock = Lock()
        self._l2_lock = Lock()

        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "l2_hits": 0, "l2_misses": 0}

        if self.l2_enabled:
            self._init_l2_db()

        logger.info(
            f"Semantic cache: L1 ativo (max={max_size}, TTL={ttl_seconds}s), L2={'enabled' if self.l2_enabled else 'disabled'}"
        )

    def _init_l2_db(self):
        try:
            L2_CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(L2_CACHE_DB)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_l2 (
                        hash_key TEXT PRIMARY KEY,
                        response TEXT,
                        text_preview TEXT,
                        timestamp REAL,
                        access_count INTEGER DEFAULT 1
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_l2(timestamp)")
                conn.commit()
            logger.debug("L2 cache database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize L2 cache: {e}")
            self.l2_enabled = False

    def _hash_text(self, text: str) -> str:
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _is_expired(self, entry: dict) -> bool:
        return time.time() - entry["timestamp"] > self.ttl_seconds

    def _cleanup_expired(self):
        now = time.time()
        cutoff = now - self.ttl_seconds
        expired_keys = [k for k, v in self.cache_l1.items() if v["timestamp"] < cutoff]
        for k in expired_keys:
            del self.cache_l1[k]
            self.stats["evictions"] += 1

    def _enforce_size_limit(self):
        while len(self.cache_l1) > self.max_size:
            self.cache_l1.popitem(last=False)
            self.stats["evictions"] += 1

    def get(self, text: str) -> Any | None:
        with self._lock:
            hash_key = self._hash_text(text)

            if hash_key in self.cache_l1:
                entry = self.cache_l1[hash_key]
                if not self._is_expired(entry):
                    self.cache_l1.move_to_end(hash_key)
                    self.stats["hits"] += 1
                    age = time.time() - entry["timestamp"]
                    logger.info(f"L1 Cache HIT: {hash_key[:8]} (age: {age:.0f}s)")
                    return entry["response"]
                else:
                    del self.cache_l1[hash_key]

            self.stats["misses"] += 1

        l2_result = self.get_l2(text)
        if l2_result is not None:
            with self._lock:
                self.cache_l1[hash_key] = {"timestamp": time.time(), "response": l2_result, "text_preview": text[:100]}
                self.cache_l1.move_to_end(hash_key)
            return l2_result

        return None

    def set(self, text: str, response: Any):
        with self._lock:
            hash_key = self._hash_text(text)

            self._cleanup_expired()
            self._enforce_size_limit()

            self.cache_l1[hash_key] = {"timestamp": time.time(), "response": response, "text_preview": text[:100]}
            self.cache_l1.move_to_end(hash_key)

            logger.debug(f"L1 Cache SET: {hash_key[:8]} (size: {len(self.cache_l1)})")

        self.set_l2(text, response)

    def get_l1(self, text: str) -> Any | None:
        return self.get(text)

    def set_l1(self, text: str, response: Any):
        self.set(text, response)

    def get_l2(self, text: str) -> Any | None:
        if not self.l2_enabled:
            return None

        hash_key = self._hash_text(text)
        with self._l2_lock:
            try:
                with sqlite3.connect(str(L2_CACHE_DB)) as conn:
                    cursor = conn.execute("SELECT response, timestamp FROM cache_l2 WHERE hash_key = ?", (hash_key,))
                    row = cursor.fetchone()

                    if row:
                        response_json, timestamp = row
                        age = time.time() - timestamp

                        if age > self.l2_ttl_seconds:
                            conn.execute("DELETE FROM cache_l2 WHERE hash_key = ?", (hash_key,))
                            conn.commit()
                            self.stats["l2_misses"] += 1
                            return None

                        conn.execute(
                            "UPDATE cache_l2 SET access_count = access_count + 1 WHERE hash_key = ?", (hash_key,)
                        )
                        conn.commit()

                        self.stats["l2_hits"] += 1
                        logger.info(f"L2 Cache HIT: {hash_key[:8]} (age: {age:.0f}s)")
                        return json.loads(response_json)

                    self.stats["l2_misses"] += 1
                    return None

            except Exception as e:
                logger.error(f"L2 cache get error: {e}")
                return None

    def set_l2(self, text: str, response: Any):
        if not self.l2_enabled:
            return

        hash_key = self._hash_text(text)
        with self._l2_lock:
            try:
                response_json = json.dumps(response, ensure_ascii=False)

                with sqlite3.connect(str(L2_CACHE_DB)) as conn:
                    self._cleanup_l2(conn)

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cache_l2 (hash_key, response, text_preview, timestamp, access_count)
                        VALUES (?, ?, ?, ?, 1)
                    """,
                        (hash_key, response_json, text[:100], time.time()),
                    )
                    conn.commit()

                logger.debug(f"L2 Cache SET: {hash_key[:8]}")

            except Exception as e:
                logger.error(f"L2 cache set error: {e}")

    def _cleanup_l2(self, conn: sqlite3.Connection):
        cutoff = time.time() - self.l2_ttl_seconds
        conn.execute("DELETE FROM cache_l2 WHERE timestamp < ?", (cutoff,))

        cursor = conn.execute("SELECT COUNT(*) FROM cache_l2")
        count = cursor.fetchone()[0]
        if count > self.max_size * 5:
            conn.execute(
                """
                DELETE FROM cache_l2 WHERE hash_key IN (
                    SELECT hash_key FROM cache_l2 ORDER BY timestamp ASC LIMIT ?
                )
            """,
                (count - self.max_size * 5,),
            )

    def get_stats(self) -> dict:
        with self._lock:
            total_l1 = self.stats["hits"] + self.stats["misses"]
            hit_rate_l1 = (self.stats["hits"] / total_l1 * 100) if total_l1 > 0 else 0

            total_l2 = self.stats["l2_hits"] + self.stats["l2_misses"]
            hit_rate_l2 = (self.stats["l2_hits"] / total_l2 * 100) if total_l2 > 0 else 0

            l2_size = 0
            if self.l2_enabled:
                try:
                    with sqlite3.connect(str(L2_CACHE_DB)) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM cache_l2")
                        l2_size = cursor.fetchone()[0]
                except Exception as e:
                    logger.debug(f"Erro ao contar cache L2: {e}")

            return {
                "l1_size": len(self.cache_l1),
                "l2_size": l2_size,
                "l2_enabled": self.l2_enabled,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "l2_hits": self.stats["l2_hits"],
                "l2_misses": self.stats["l2_misses"],
                "hit_rate_l1_pct": round(hit_rate_l1, 1),
                "hit_rate_l2_pct": round(hit_rate_l2, 1),
                "evictions": self.stats["evictions"],
            }

    def clear(self):
        with self._lock:
            self.cache_l1.clear()
            logger.info("Cache cleared")
