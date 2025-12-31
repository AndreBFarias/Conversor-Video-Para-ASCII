# 2025-12-29: ETAPA 11 - Memoria Curto/Medio/Longo Prazo

## Objetivo
Implementar sistema de memoria em tres niveis com TTL e promocao automatica.

## Arquitetura de Tiers

### SHORT (5 minutos)
- Buffer volatil em memoria
- Deque com max_size configuravel
- Expira automaticamente apos TTL
- Promocao baseada em importancia ou frequencia de acesso

### MEDIUM (24 horas)
- Memorias da sessao atual
- Promovidas de SHORT via MemoryTierManager
- Armazenadas no SmartMemory com horizon="medium"

### LONG (permanente)
- Fatos consolidados sobre o usuario
- Consolidadas pelo MemoryConsolidator existente
- Armazenadas com horizon="long"

## Arquivos Criados

### src/data_memory/short_term_memory.py (~220 linhas)
Buffer volatil com TTL:

**ShortTermEntry** (dataclass):
- `id`: identificador unico
- `content`: texto da memoria
- `timestamp`: momento de criacao
- `importance`: 0.0-1.0
- `category`: tipo da memoria
- `access_count`: contador de acessos
- `is_expired()`: verifica se expirou

**ShortTermMemory**:
- `DEFAULT_TTL = 300.0` (5 minutos)
- `DEFAULT_MAX_SIZE = 50`
- `PROMOTION_THRESHOLD = 0.7`
- `MIN_ACCESSES_FOR_PROMOTION = 2`
- `add()`: adiciona memoria ao buffer
- `get()`: busca por query com incremento de access_count
- `get_recent()`: retorna N memorias mais recentes
- `get_promotable()`: retorna memorias elegiveis para promocao
- `mark_promoted()`: remove memoria promovida
- `clear()`: limpa buffer
- `render_context()`: formata para contexto LLM

### src/data_memory/memory_tier_manager.py (~250 linhas)
Orquestrador de promocao:

**MemoryTierManager**:
- `add_short_term()`: adiciona ao tier curto
- `_schedule_quick_promotion()`: agenda promocao para alta importancia
- `_promote_entry()`: move de short para medium
- `_store_medium_term()`: persiste no SmartMemory
- `promote_all_eligible()`: promocao em lote
- `consolidate_medium_to_long()`: usa MemoryConsolidator
- `start_auto_promotion()`: thread de promocao automatica
- `stop_auto_promotion()`: para thread
- `recall_across_tiers()`: busca em todos os tiers
- `get_tier_stats()`: estatisticas completas
- `force_promotion()`: promocao manual
- `clear_short_term()`: limpa tier curto

### src/tests/test_memory_tiers.py (27 testes)
Cobertura completa:

- **TestShortTermEntry**: 4 testes (criacao, expiracao, to_dict)
- **TestShortTermMemory**: 11 testes (add, reject, get, promotable, eviction)
- **TestShortTermMemorySingleton**: 2 testes (instancia unica por entidade)
- **TestMemoryTierManager**: 6 testes (add, stats, clear, promocao)
- **TestMemoryTierManagerSingleton**: 2 testes (singleton)
- **TestMemoryTierIntegration**: 2 testes (lifecycle, exports)

## Arquivos Modificados

### src/data_memory/smart_memory.py
- Adicionado parametro `importance` no metodo `add()`
- Importancia armazenada no metadata da memoria

### src/data_memory/__init__.py
- Exports adicionados:
  - `ShortTermMemory`
  - `ShortTermEntry`
  - `get_short_term_memory`
  - `MemoryTierManager`
  - `get_tier_manager`

## Fluxo de Promocao

```
[USER INPUT]
     |
     v
[SHORT-TERM BUFFER]  ---(TTL expira)---> [DESCARTADO]
     |
     | (importancia >= 0.7 OU acessos >= 2)
     v
[MEDIUM-TERM (SmartMemory)]
     |
     | (MemoryConsolidator a cada 30 min)
     v
[LONG-TERM (consolidado)]
```

## Criterios de Promocao

1. **Por Importancia**: `importance >= 0.7` -> promocao imediata (30s delay)
2. **Por Frequencia**: `access_count >= 2` -> promocao no proximo ciclo
3. **Manual**: `force_promotion(entry_id)` -> promocao instantanea

## Validacao

- [x] short_term_memory.py criado com buffer TTL
- [x] memory_tier_manager.py criado com promocao
- [x] SmartMemory atualizado com parametro importance
- [x] 27 testes passando
- [x] Pre-commit passa
- [x] Exports no __init__.py

## Uso

```python
from src.data_memory import get_tier_manager

# Obter manager para entidade
manager = get_tier_manager("luna")

# Adicionar memoria de curto prazo
manager.add_short_term("Usuario mencionou que gosta de cafe", importance=0.8)

# Buscar em todos os tiers
results = manager.recall_across_tiers("cafe", limit=5)

# Estatisticas
stats = manager.get_tier_stats()
```
