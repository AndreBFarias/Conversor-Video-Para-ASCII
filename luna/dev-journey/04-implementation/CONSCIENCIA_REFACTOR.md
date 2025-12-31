# Refatoracao da Consciencia - Separacao de Responsabilidades

```
STATUS: PRODUCAO
ANTES: 1 God Object (Consciencia)
DEPOIS: 1 Orquestrador + 3 Servicos especializados
```

## Problema

A classe `Consciencia` era um **God Object** com multiplas responsabilidades:
- Gerenciar memoria (short-term, long-term, vector store)
- Chamar LLM (Gemini, Ollama)
- Construir prompts
- Executar comandos de terminal
- Processar buscas web
- Gerenciar historico de conversacao

Isso dificultava:
1. Testes unitarios (mockear tudo era complexo)
2. Manutencao (qualquer mudanca podia quebrar algo)
3. Extensibilidade (adicionar novos recursos era arriscado)

## Solucao

Dividir em 3 servicos especializados seguindo **Single Responsibility Principle**:

```
Consciencia (Orquestrador)
    |
    +-- CognitionEngine (Pensa)
    |       - Constroi prompts
    |       - Chama LLM
    |       - Gerencia status de providers
    |
    +-- MemoryController (Lembra)
    |       - Warmup de memoria
    |       - Constroi contexto
    |       - Salva interacoes
    |       - Gerencia tiers
    |
    +-- ActionDispatcher (Age)
            - Executa filesystem_ops
            - Parse de comandos naturais
            - Busca web
```

## Arquitetura

```
src/soul/consciencia/
    |-- core.py             # Classe Consciencia (orquestrador)
    |-- services/
    |       |-- __init__.py
    |       |-- cognition_engine.py    # CognitionEngine
    |       |-- memory_controller.py   # MemoryController
    |       +-- action_dispatcher.py   # ActionDispatcher
    |-- helpers.py
    |-- llm_bridge.py
    |-- memory.py           # Funcoes legadas (deprecated)
    |-- post_process.py     # Funcoes legadas (deprecated)
    +-- ...
```

## Interfaces

### CognitionEngine

```python
class CognitionEngine:
    def init_soul_prompt(self) -> None
    def build_full_prompt(user_text, visual_context, attached_content, memory_context) -> str
    def call_llm(prompt) -> str
    def has_provider() -> bool
    def get_llm_status() -> dict
    def stream_response(user_text, visual_context, attached_content) -> Generator
    def get_model_for_intent(intent) -> tuple[str, str]
```

### MemoryController

```python
class MemoryController:
    def warmup() -> dict
    def build_context(user_text) -> str
    def save_interaction(user_text, response_data) -> None
    def update_tiers(user_text, response_data) -> None
    def reload_for_entity(entity_id) -> None
    def get_stats() -> dict
```

### ActionDispatcher

```python
class ActionDispatcher:
    def execute_filesystem_ops(response_data, user_text) -> dict
    def execute_web_search(query) -> str | None
    def dispatch(response_data, user_text) -> dict
    def get_stats() -> dict
```

## Uso

```python
class Consciencia:
    def __init__(self, app):
        # Inicializa os 3 servicos
        self.cognition = CognitionEngine(self)
        self.memory = MemoryController(self)
        self.actions = ActionDispatcher(self)

    def process_interaction(self, user_text, ...):
        # Memoria: constroi contexto
        contexto = self.memory.build_context(user_text)

        # Cognicao: gera prompt e chama LLM
        prompt = self.cognition.build_full_prompt(user_text, ..., contexto)
        response = self.cognition.call_llm(prompt)

        # Acoes: executa comandos
        data = self.actions.dispatch(data, user_text)

        # Memoria: salva interacao
        self.memory.save_interaction(user_text, data)

        return data
```

## Testes

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| test_cognition_engine.py | 18 | CognitionEngine |
| test_memory_controller.py | 15 | MemoryController |
| test_action_dispatcher.py | 16 | ActionDispatcher |
| **Total** | **49** | **100% dos servicos** |

## Beneficios

1. **Testabilidade**: Cada servico pode ser testado isoladamente com mocks simples
2. **Manutencao**: Mudar memoria nao afeta cognicao
3. **Extensibilidade**: Facil adicionar novos servicos (ex: EmotionEngine)
4. **Clareza**: Responsabilidades bem definidas
5. **Injecao de Dependencia**: Servicos podem ser substituidos por mocks em testes

## Migracao

A refatoracao foi feita de forma retrocompativel:
- Metodos publicos de `Consciencia` continuam funcionando
- Funcoes em `memory.py`, `post_process.py`, etc. ainda existem (deprecated)
- Novos servicos sao usados internamente

## Proximos Passos

1. Deprecar funcoes legadas em `memory.py`, `post_process.py`
2. Migrar chamadas diretas para usar servicos
3. Considerar adicionar `EmotionEngine` para gerenciar estado emocional

---

*Implementado em 2025-12-31*
