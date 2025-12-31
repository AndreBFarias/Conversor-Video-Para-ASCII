"""
Short-Term Memory - Buffer volatil com TTL.

Armazena informacoes temporarias da conversa atual.
Memorias expiram automaticamente apos TTL (default 5 minutos).
Memorias importantes sao promovidas para medium-term.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.constants import MemoryConstants
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ShortTermEntry:
    id: str
    content: str
    timestamp: float
    importance: float = 0.5
    category: str = "context"
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, ttl_seconds: float) -> bool:
        return time.time() - self.timestamp > ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "category": self.category,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }


class ShortTermMemory:
    """Buffer volatil para memorias de curto prazo."""

    DEFAULT_TTL = 300.0
    DEFAULT_MAX_SIZE = 50
    PROMOTION_THRESHOLD = 0.7
    MIN_ACCESSES_FOR_PROMOTION = 2

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL,
        max_size: int = DEFAULT_MAX_SIZE,
        promotion_threshold: float = PROMOTION_THRESHOLD,
    ):
        self._buffer: deque[ShortTermEntry] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._promotion_threshold = promotion_threshold

        self._stats = {
            "added": 0,
            "expired": 0,
            "promoted": 0,
            "evicted": 0,
        }

        logger.info(f"ShortTermMemory: TTL={ttl_seconds}s, max_size={max_size}")

    def add(
        self,
        content: str,
        importance: float = 0.5,
        category: str = "context",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not content or len(content.strip()) < MemoryConstants.MIN_TEXT_LENGTH:
            return ""

        entry = ShortTermEntry(
            id=str(uuid.uuid4())[:8],
            content=content.strip(),
            timestamp=time.time(),
            importance=importance,
            category=category,
            metadata=metadata or {},
        )

        with self._lock:
            self._cleanup_expired()

            if len(self._buffer) >= self._max_size:
                self._stats["evicted"] += 1

            self._buffer.append(entry)
            self._stats["added"] += 1

        logger.debug(f"STM add: {entry.id} (imp={importance:.2f})")
        return entry.id

    def get(self, query: str, limit: int = 5) -> list[ShortTermEntry]:
        with self._lock:
            self._cleanup_expired()

            query_lower = query.lower()
            results = []

            for entry in self._buffer:
                if query_lower in entry.content.lower():
                    entry.access_count += 1
                    results.append(entry)

            results.sort(key=lambda e: (e.importance, e.timestamp), reverse=True)
            return results[:limit]

    def get_recent(self, limit: int = 10) -> list[ShortTermEntry]:
        with self._lock:
            self._cleanup_expired()
            entries = list(self._buffer)
            entries.sort(key=lambda e: e.timestamp, reverse=True)
            return entries[:limit]

    def get_promotable(self) -> list[ShortTermEntry]:
        with self._lock:
            self._cleanup_expired()

            promotable = []
            for entry in self._buffer:
                if entry.importance >= self._promotion_threshold:
                    promotable.append(entry)
                elif entry.access_count >= self.MIN_ACCESSES_FOR_PROMOTION:
                    promotable.append(entry)

            return promotable

    def mark_promoted(self, entry_id: str) -> bool:
        with self._lock:
            for i, entry in enumerate(self._buffer):
                if entry.id == entry_id:
                    del self._buffer[i]
                    self._stats["promoted"] += 1
                    logger.debug(f"STM promoted: {entry_id}")
                    return True
            return False

    def _cleanup_expired(self) -> int:
        expired_count = 0
        while self._buffer and self._buffer[0].is_expired(self._ttl):
            self._buffer.popleft()
            expired_count += 1
            self._stats["expired"] += 1

        if expired_count > 0:
            logger.debug(f"STM cleanup: {expired_count} expired")

        return expired_count

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            logger.info("STM cleared")

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "current_size": len(self._buffer),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl,
                **self._stats,
            }

    def render_context(self, max_chars: int = 300) -> str:
        entries = self.get_recent(10)
        if not entries:
            return ""

        lines = ["[SHORT-TERM]"]
        total_chars = 15

        for entry in entries:
            line = f"- {entry.content[:50]}..."
            if total_chars + len(line) > max_chars:
                break
            lines.append(line)
            total_chars += len(line)

        return "\n".join(lines)

    def __len__(self) -> int:
        with self._lock:
            self._cleanup_expired()
            return len(self._buffer)


_short_term_memories: dict[str, ShortTermMemory] = {}
_stm_lock = threading.Lock()


def get_short_term_memory(entity_id: str = "default") -> ShortTermMemory:
    global _short_term_memories
    if entity_id not in _short_term_memories:
        with _stm_lock:
            if entity_id not in _short_term_memories:
                _short_term_memories[entity_id] = ShortTermMemory()
    return _short_term_memories[entity_id]


def clear_all_short_term() -> None:
    global _short_term_memories
    with _stm_lock:
        for stm in _short_term_memories.values():
            stm.clear()
        _short_term_memories.clear()
