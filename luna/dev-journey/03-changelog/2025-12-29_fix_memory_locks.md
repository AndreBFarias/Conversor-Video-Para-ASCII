# Fix: Correcao de Locks em SmartMemory

**Data:** 2025-12-29
**Issue:** #34
**Branch:** fix/etapa-02-memory-locks

## Problema

O sistema de memoria (`smart_memory.py` e `entity_memory.py`) usava locks para proteger inicializacao lazy, mas sem tratamento adequado de excecoes. Em caso de falha durante a inicializacao, o estado poderia ficar inconsistente.

## Solucao

### 1. Excecoes Customizadas

Criada hierarquia de excecoes em `src/data_memory/__init__.py`:

```python
class MemoryError(Exception):
    pass

class MemoryLoadError(MemoryError):
    pass

class MemoryWriteError(MemoryError):
    pass

class MemoryLockError(MemoryError):
    pass
```

### 2. Metodos Refatorados

#### `SmartMemory._ensure_loaded()`
- Adicionado try/except dentro do bloco with lock
- Em caso de falha, `_loaded` e resetado para False
- Lanca `MemoryLoadError` com mensagem descritiva

#### `get_entity_smart_memory()`
- Adicionado try/except dentro do bloco with lock
- Lanca `MemoryLoadError` com entity_id no erro

#### `_get_shared_embedding_gen()` (entity_memory.py)
- Adicionado try/except dentro do bloco with lock
- Lanca `MemoryLoadError` em caso de falha

### 3. Testes Criados

`src/tests/test_memory_locks.py`:
- `test_ensure_loaded_thread_safety`: Verifica que apenas uma instancia e criada com 10 threads
- `test_double_checked_locking_pattern`: Valida o padrao de double-checked locking
- `test_ensure_loaded_raises_memory_load_error`: Verifica excecao customizada
- `test_concurrent_entity_memory_creation`: Testa criacao concorrente de entity memory
- `test_shared_embedding_gen_thread_safety`: Testa thread safety do EmbeddingGenerator compartilhado
- `test_memory_error_hierarchy`: Valida hierarquia de excecoes

### 4. Pre-commit Hook

Adicionado `no-manual-lock-acquire`:
- Script: `src/tools/check_manual_lock.sh`
- Detecta uso de `.acquire()` sem context manager
- Sugere usar `with lock:` em vez de `lock.acquire()/release()`

## Arquivos Modificados

- `src/data_memory/__init__.py` - Excecoes customizadas
- `src/data_memory/smart_memory.py` - Tratamento de excecao em locks
- `src/data_memory/entity_memory.py` - Tratamento de excecao em lock
- `.pre-commit-config.yaml` - Novo hook
- `src/tools/check_manual_lock.sh` - Script do hook

## Arquivos Criados

- `src/tests/test_memory_locks.py`
- `dev-journey/03-changelog/2025-12-29_fix_memory_locks.md`
