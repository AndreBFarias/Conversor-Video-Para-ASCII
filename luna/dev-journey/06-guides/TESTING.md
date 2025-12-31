# Guia de Testes - Luna

**Data:** 2025-12-18

## TL;DR

Testes obrigatorios antes de PR: pytest em `src/core/` e `src/utils/` primeiro, depois `main.py`. Mocking para APIs externas, cobertura minima 80%, logs desabilitados em testes.

## Contexto

Luna usa pytest para testes unitarios e de integracao. Hierarquia obrigatoria: testa modulos filhos (core/utils) antes do orquestrador. Testes devem ser rapidos, isolados e deterministicos.

## Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py           # Fixtures compartilhadas
├── unit/
│   ├── test_processor.py
│   ├── test_memory.py
│   └── test_utils.py
└── integration/
    ├── test_api_flow.py
    └── test_tui_interaction.py
```

## Instalacao

```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

## Como Rodar Testes

### Todos os Testes

```bash
pytest
```

### Testes Especificos

```bash
pytest tests/unit/test_processor.py
pytest tests/integration/test_api_flow.py -v
pytest -k "test_memory" -v
```

### Com Cobertura

```bash
pytest --cov=src --cov-report=html
```

Relatorio em `htmlcov/index.html`.

### Rapido (Apenas Unit)

```bash
pytest tests/unit/ -v
```

## Hierarquia de Execucao

**ORDEM OBRIGATORIA:**

1. `pytest tests/unit/test_utils.py`
2. `pytest tests/unit/test_core.py`
3. `pytest tests/integration/`
4. Teste manual do `main.py`

Razao: se modulos filhos falham, orquestrador inevitavelmente falhara.

## Escrevendo Testes

### 1. Testes Unitarios

Teste funcoes isoladas com mocking de dependencias.

```python
import pytest
from src.core.processor import DataProcessor

def test_process_valid_data():
    processor = DataProcessor()
    input_data = {"key": "value"}

    result = processor.process(input_data)

    assert result.status == "success"
    assert result.data["key"] == "value"

def test_process_invalid_data_raises_error():
    processor = DataProcessor()

    with pytest.raises(ValueError):
        processor.process(None)
```

### 2. Testes com Fixtures

Define fixtures em `conftest.py`:

```python
import pytest
from src.core.memory import ConversationMemory

@pytest.fixture
def memory_instance():
    return ConversationMemory(max_size=100)

@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
```

Use nos testes:

```python
def test_memory_stores_messages(memory_instance, sample_messages):
    memory_instance.add_messages(sample_messages)

    assert memory_instance.get_size() == 2
    assert memory_instance.get_latest().content == "Hi there"
```

### 3. Mocking APIs Externas

```python
from unittest.mock import patch, MagicMock

@patch('src.core.api_client.LLMClient')
def test_api_call_success(mock_llm_client):
    mock_client = MagicMock()
    mock_client.generate.return_value.text = "Mocked response"
    mock_llm_client.return_value = mock_client

    from src.core.api_client import ApiClient
    client = ApiClient(api_key="fake-key")
    response = client.send_message("Test prompt")

    assert response == "Mocked response"
    mock_client.messages.create.assert_called_once()
```

### 4. Testes Assincronos

```python
import pytest

@pytest.mark.asyncio
async def test_async_processing():
    from src.core.async_processor import AsyncProcessor

    processor = AsyncProcessor()
    result = await processor.process_async({"data": "test"})

    assert result.status == "completed"
```

## Mocking Patterns

### Mock de Arquivo de Configuracao

```python
from unittest.mock import mock_open, patch

def test_load_config():
    mock_config_data = "[api]\nkey=test123\n"

    with patch("builtins.open", mock_open(read_data=mock_config_data)):
        from src.utils.config import load_config
        config = load_config("fake/path.ini")

    assert config["api"]["key"] == "test123"
```

### Mock de Sistema de Arquivos

```python
from unittest.mock import patch

@patch('pathlib.Path.exists')
def test_file_exists_check(mock_exists):
    mock_exists.return_value = True

    from src.utils.file_handler import check_file
    result = check_file("/fake/path")

    assert result is True
```

### Mock de Logging

```python
@patch('src.utils.logger.logging.getLogger')
def test_logging_called(mock_logger):
    mock_log_instance = MagicMock()
    mock_logger.return_value = mock_log_instance

    from src.core.processor import process_with_logging
    process_with_logging("test")

    mock_log_instance.info.assert_called()
```

## Desabilitar Logs em Testes

Em `conftest.py`:

```python
import logging
import pytest

@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
```

## Cobertura Minima

**Regra:** 80% de cobertura obrigatoria antes de merge em `main`.

Verificar:

```bash
pytest --cov=src --cov-fail-under=80
```

### Excecoes

Nao e necessario cobrir:

- Scripts de instalacao (`install.sh`)
- Arquivos de configuracao
- `main.py` (orquestrador, testado manualmente)

## Testes de Integracao

Testam fluxo completo sem mocking excessivo.

```python
def test_full_conversation_flow():
    from src.core.conversation import ConversationManager
    from src.core.api_client import ApiClient

    manager = ConversationManager(api_client=ApiClient(api_key="test"))
    manager.start_conversation("System prompt")

    response = manager.send_message("Hello")

    assert response is not None
    assert len(manager.get_history()) == 2
```

## Testes de Performance

```python
import time

def test_processing_speed():
    from src.core.processor import DataProcessor

    processor = DataProcessor()
    large_dataset = [{"id": i} for i in range(10000)]

    start = time.time()
    processor.process_batch(large_dataset)
    duration = time.time() - start

    assert duration < 2.0, f"Processamento demorou {duration}s, limite e 2s"
```

## Parametrizacao

```python
@pytest.mark.parametrize("input_value,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase_transformation(input_value, expected):
    from src.utils.text import to_uppercase
    assert to_uppercase(input_value) == expected
```

## Testes de Erro

```python
def test_invalid_api_key_raises_exception():
    from src.core.api_client import ApiClient

    with pytest.raises(ValueError, match="API key invalida"):
        ApiClient(api_key="")
```

## Pre-Commit Hooks

Configure em `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest tests/unit/ -v
if [ $? -ne 0 ]; then
    echo "Testes unitarios falharam. Commit bloqueado."
    exit 1
fi
```

## Debugging de Testes

### Verbose

```bash
pytest -vv
```

### Mostrar Prints

```bash
pytest -s
```

### Parar no Primeiro Erro

```bash
pytest -x
```

### Debugger Interativo

```bash
pytest --pdb
```

## Checklist Pre-PR

- [ ] `pytest tests/unit/ -v` passa
- [ ] `pytest tests/integration/ -v` passa
- [ ] Cobertura >= 80%
- [ ] Nenhum teste marcado como `@pytest.mark.skip`
- [ ] Logs desabilitados em testes
- [ ] Mocking de APIs externas
- [ ] Testes rapidos (< 10s total)

## Links Relacionados

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_STYLE.md](CODE_STYLE.md)
- [DEBUGGING.md](DEBUGGING.md)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Licenca:** GPLv3
