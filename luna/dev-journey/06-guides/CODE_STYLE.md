# Guia de Estilo de Codigo - Luna

**Data:** 2025-12-18

## TL;DR

Codigo Python limpo: type hints obrigatorios, zero comentarios, PEP 8 com black, nomes semanticos, logica em `src/`, docs em `.md`. Leia o codigo como prosa tecnica, documente em markdown.

## Contexto

Luna segue o Protocolo Luna: separacao estrita entre codigo executavel e documentacao humana. O codigo deve ser autoexplicativo atraves de nomes semanticos e type hints. Toda explicacao textual vai para arquivos `.md` em `dev-journey/`.

## Principios Fundamentais

### 1. Zero Comentarios no Codigo

**PROIBIDO:**

```python
def process_data(data):
    # Loop through each item
    for item in data:
        # Check if item is valid
        if item.is_valid():
            # Process the item
            result = item.process()
```

**CORRETO:**

```python
def process_validated_items(items: list[Item]) -> list[ProcessedItem]:
    return [item.process() for item in items if item.is_valid()]
```

Explicacoes vao para `dev-journey/04-docs/data_processing.md`.

### 2. Type Hints Obrigatorios

**PROIBIDO:**

```python
def calculate(x, y):
    return x + y

def fetch_user(id):
    return database.get(id)
```

**CORRETO:**

```python
from typing import Optional

def calculate_sum(x: int, y: int) -> int:
    return x + y

def fetch_user_by_id(user_id: str) -> Optional[User]:
    return database.get(user_id)
```

### 3. Nomes Semanticos

Use nomes que revelam intencao:

**PROIBIDO:**

```python
d = {}
lst = []
tmp = get_data()
x = process(tmp)
```

**CORRETO:**

```python
user_cache: dict[str, User] = {}
pending_tasks: list[Task] = []
raw_api_response = fetch_external_data()
normalized_response = normalize_api_response(raw_api_response)
```

## Convencoes de Nomenclatura

### Funcoes

Verbos no imperativo, descritivos:

```python
def validate_user_credentials(username: str, password: str) -> bool:
    pass

def transform_raw_data_to_dataframe(raw_data: list[dict]) -> pd.DataFrame:
    pass

def invoke_external_api_with_retry(endpoint: str, retries: int = 3) -> dict:
    pass
```

### Classes

Substantivos, CamelCase:

```python
class ApiClient:
    pass

class DataProcessor:
    pass

class ConversationMemoryManager:
    pass
```

### Variaveis

snake_case, descritivas:

```python
user_session_token: str
max_retry_attempts: int = 5
is_authenticated: bool = False
conversation_history: list[Message] = []
```

### Constantes

UPPER_SNAKE_CASE:

```python
MAX_TOKENS_PER_REQUEST: int = 4096
DEFAULT_MODEL_NAME: str = "gpt-4"
API_TIMEOUT_SECONDS: int = 30
```

## Estrutura de Arquivos Python

### Imports

Ordem obrigatoria:

1. Standard library
2. Third-party
3. Local imports

```python
import os
import sys
from pathlib import Path
from typing import Optional, Union

import google.genai
import pandas as pd
from textual.app import App

from src.core.processor import DataProcessor
from src.utils.logger import setup_logging
```

### Estrutura de Modulo

```python
from typing import Protocol, Optional

class DataSourceProtocol(Protocol):
    def fetch(self) -> dict:
        ...

class ConcreteDataSource:
    def __init__(self, config: dict[str, str]) -> None:
        self.config = config
        self._connection: Optional[Connection] = None

    def fetch(self) -> dict:
        if not self._connection:
            self._connection = self._establish_connection()
        return self._connection.query()

    def _establish_connection(self) -> Connection:
        return Connection(self.config)
```

## Formatacao com Black

Sempre rode antes de commitar:

```bash
black src/
```

Configuracao em `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
```

## Type Checking com Mypy

Sempre valide:

```bash
mypy src/
```

Configuracao em `mypy.ini`:

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Logging ao Inves de Print

**PROIBIDO:**

```python
def process():
    print("Starting process...")
    result = heavy_computation()
    print(f"Result: {result}")
```

**CORRETO:**

```python
import logging

logger = logging.getLogger(__name__)

def process() -> ComputationResult:
    logger.info("Iniciando processamento pesado")
    result = heavy_computation()
    logger.debug(f"Resultado obtido: {result}")
    return result
```

Setup de logging em `src/utils/logger.py`.

## Error Handling

Seja explicito:

```python
class InvalidUserInputError(Exception):
    pass

def validate_api_key(key: str) -> None:
    if not key or len(key) < 32:
        raise InvalidUserInputError(
            "API key invalida: deve conter ao menos 32 caracteres"
        )
```

## Documentacao de Codigo

Use docstrings minimalistas (apenas assinatura):

```python
def transform_conversation_to_prompt(
    messages: list[Message],
    system_prompt: str
) -> str:
    """
    Converte lista de mensagens em prompt formatado.

    Args:
        messages: Historico de conversacao
        system_prompt: Instrucoes de sistema

    Returns:
        Prompt formatado para API
    """
    pass
```

Detalhes de implementacao vao para `dev-journey/04-docs/`.

## Proibicoes Absolutas

1. Comentarios explicativos no codigo
2. `print()` para debug (use logging)
3. Funcoes sem type hints
4. Nomes genericos (`data`, `tmp`, `x`)
5. Magic numbers (use constantes nomeadas)
6. Codigo morto (delete ao inves de comentar)

## Excecoes Permitidas

Unico tipo de comentario permitido: citacoes filosoficas no final de scripts completos.

```python
# "A perfeicao e alcancada nao quando nao ha mais nada a adicionar, mas quando nao ha mais nada a remover."
# - Antoine de Saint-Exupery
```

## Checklist Pre-Commit

- [ ] `black src/` executado
- [ ] `mypy src/` sem erros
- [ ] Zero comentarios explicativos
- [ ] Type hints em todas as funcoes
- [ ] Logging implementado
- [ ] Nomes semanticos
- [ ] Imports organizados

## Links Relacionados

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [DEBUGGING.md](DEBUGGING.md)
- [PEP 8](https://pep8.org/)
- [Black Documentation](https://black.readthedocs.io/)

---

**Licenca:** GPLv3
