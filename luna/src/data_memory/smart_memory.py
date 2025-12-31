"""
SmartMemory - Sistema de memoria semantica.

Gerencia armazenamento e recuperacao de memorias:
- Armazenamento vetorial com embeddings
- Tagging emocional automatico
- Decay temporal de relevancia
- Busca semantica por similaridade

Este modulo e um wrapper de compatibilidade.
A implementacao real esta em src/data_memory/smart_memory/
"""

from src.data_memory.smart_memory import (
    CATEGORY_KEYWORDS,
    ContextWindow,
    MemoryCategorizer,
    MemoryCategory,
    MemorySlice,
    SmartMemory,
    get_entity_smart_memory,
    get_smart_memory,
    switch_smart_memory_entity,
)

__all__ = [
    "MemoryCategory",
    "CATEGORY_KEYWORDS",
    "MemorySlice",
    "ContextWindow",
    "MemoryCategorizer",
    "SmartMemory",
    "get_smart_memory",
    "get_entity_smart_memory",
    "switch_smart_memory_entity",
]
