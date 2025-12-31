# Interface Unificada de Memoria

## Visao Geral

O sistema de memoria da Luna agora possui uma interface unificada que abstrai as diferentes implementacoes.

## Arquitetura

```
MemoryInterface (ABC)
    |
    +-- SmartMemoryAdapter
    |       |
    |       +-- SmartMemory (implementacao atual)
    |
    +-- [Futuro] UnifiedMemory
            |
            +-- ShortTermMemory
            +-- MediumTermMemory
            +-- LongTermMemory
```

## Uso

```python
from src.data_memory import get_memory_adapter, MemoryCategory

memory = get_memory_adapter("luna")

mem_id = memory.remember(
    "Usuario prefere cafe sem acucar",
    importance=0.7,
    category=MemoryCategory.PREFERENCE
)

context = memory.recall("preferencias de cafe")
prompt_injection = context.render()
```

## Classes Principais

### MemoryInterface
Interface abstrata com metodos:
- `remember()` - Armazena memoria
- `recall()` - Busca memorias
- `forget()` - Remove memoria
- `consolidate()` - Promove memorias
- `get_stats()` - Estatisticas

### MemoryEntry
Dataclass representando uma memoria:
- `id`, `content`, `category`
- `horizon` (SHORT, MEDIUM, LONG)
- `importance` (0 a 1)
- `timestamp`, `metadata`

### MemoryContext
Container para injecao em prompt:
- `entries` - Lista de MemoryEntry
- `render()` - Gera texto para prompt
- `add()` - Adiciona respeitando budget
