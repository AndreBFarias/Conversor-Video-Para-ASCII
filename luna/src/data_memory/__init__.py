class MemoryError(Exception):
    pass


class MemoryLoadError(MemoryError):
    pass


class MemoryWriteError(MemoryError):
    pass


class MemoryLockError(MemoryError):
    pass


from .embeddings import EmbeddingGenerator  # noqa: E402
from .entity_memory import EntityMemoryManager, get_entity_memory, switch_entity_memory  # noqa: E402
from .memory_adapter import SmartMemoryAdapter, get_memory_adapter  # noqa: E402
from .memory_interface import (  # noqa: E402
    MemoryCategory,
    MemoryContext,
    MemoryEntry,
    MemoryHorizon,
    MemoryInterface,
    MemorySearchResult,
)
from .memory_manager import MemoryManager  # noqa: E402
from .memory_tier_manager import MemoryTierManager, get_tier_manager  # noqa: E402
from .short_term_memory import ShortTermEntry, ShortTermMemory, get_short_term_memory  # noqa: E402
from .smart_memory import SmartMemory, get_entity_smart_memory, get_smart_memory  # noqa: E402
from .vector_store import JSONVectorStore  # noqa: E402

__all__ = [
    "MemoryInterface",
    "MemoryEntry",
    "MemoryContext",
    "MemoryCategory",
    "MemoryHorizon",
    "MemorySearchResult",
    "SmartMemoryAdapter",
    "get_memory_adapter",
    "SmartMemory",
    "get_smart_memory",
    "get_entity_smart_memory",
    "MemoryManager",
    "EmbeddingGenerator",
    "JSONVectorStore",
    "EntityMemoryManager",
    "get_entity_memory",
    "switch_entity_memory",
    "MemoryTierManager",
    "get_tier_manager",
    "ShortTermMemory",
    "ShortTermEntry",
    "get_short_term_memory",
    "MemoryError",
    "MemoryLoadError",
    "MemoryWriteError",
    "MemoryLockError",
]
