from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class MemoryHorizon(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class MemoryCategory(Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    EMOTION = "emotion"
    EVENT = "event"
    USER_INFO = "user_info"
    CONTEXT = "context"
    TASK = "task"


@dataclass
class MemoryEntry:
    id: str
    content: str
    category: MemoryCategory
    horizon: MemoryHorizon
    importance: float
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_compact(self) -> str:
        prefix = f"[{self.category.value.upper()}]" if self.importance > 0.7 else ""
        return f"{prefix} {self.content}".strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category.value,
            "horizon": self.horizon.value,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MemoryContext:
    entries: list[MemoryEntry] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 800

    def add(self, entry: MemoryEntry) -> bool:
        entry_tokens = len(entry.content) // 4
        if self.total_tokens + entry_tokens > self.max_tokens:
            return False
        self.entries.append(entry)
        self.total_tokens += entry_tokens
        return True

    def render(self) -> str:
        if not self.entries:
            return ""

        lines = ["[MEMORIA]"]
        for entry in sorted(self.entries, key=lambda e: e.importance, reverse=True):
            lines.append(f"- {entry.to_compact()}")

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.entries)


class MemoryInterface(ABC):
    @abstractmethod
    def remember(
        self,
        content: str,
        importance: float = 0.5,
        category: MemoryCategory | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        pass

    @abstractmethod
    def recall(self, query: str, limit: int = 5, min_similarity: float = 0.3) -> MemoryContext:
        pass

    @abstractmethod
    def forget(self, memory_id: str) -> bool:
        pass

    @abstractmethod
    def consolidate(self) -> int:
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass


class MemorySearchResult:
    def __init__(self, entry: MemoryEntry, similarity: float, source: str = "unknown"):
        self.entry = entry
        self.similarity = similarity
        self.source = source

    def __repr__(self) -> str:
        return f"MemorySearchResult(id={self.entry.id}, sim={self.similarity:.2f})"
