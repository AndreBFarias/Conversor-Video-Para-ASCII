# Context Window Manager - Janela de Contexto Dinamica

## Visao Geral

O modulo `src/soul/context_window/` implementa um gerenciador de janela de contexto que:
1. Ajusta budgets dinamicamente baseado no modelo LLM
2. Implementa "Progressive Summary" para conversas longas
3. Centraliza todos os magic numbers em configuracao

## Problema Resolvido

Antes, o codigo tinha magic numbers espalhados:

```python
# ANTES: Magic numbers em todo lugar
history_limit = 3 if self.provider == "local" else 5      # response_streamer.py
max_chars = 150                                            # response_streamer.py
history_limit = 2                                          # prompt_builder.py (DIFERENTE!)
max_chars = 80                                             # prompt_builder.py (DIFERENTE!)
mem_context = memory.retrieve(query, max_chars=600)        # Hardcoded 600
self.conversation_history = history[-50:]                  # Hardcoded 50
```

Isso causava:
- Limites inconsistentes entre arquivos
- Modelos pequenos recebiam muito contexto (estouro)
- Modelos grandes recebiam pouco contexto (desperdicio)
- Conversas longas perdiam informacoes importantes

## Arquitetura

```
src/soul/context_window/
├── __init__.py             # Exports publicos
├── config.py               # ModelProfile, ContextWindowConfig
├── manager.py              # ContextWindowManager
└── progressive_summary.py  # Compressao inteligente de historico
```

## Model Profiles

Cada modelo tem um perfil com suas capacidades:

| Modelo | Context Window | Size | Tokens/Char |
|--------|----------------|------|-------------|
| llama3.2 | 8,192 | SMALL | 0.28 |
| llama3.2:1b | 8,192 | TINY | 0.28 |
| llama3.1:8b | 32,768 | MEDIUM | 0.28 |
| gemma2:9b | 8,192 | MEDIUM | 0.30 |
| gemini-2.0-flash | 1,048,576 | XLARGE | 0.25 |
| gpt-4o | 128,000 | XLARGE | 0.25 |

## Ajuste Automatico por Tamanho

O sistema ajusta limites baseado no tamanho do modelo:

| Size | max_turns | max_chars/turn | memory_max_chars |
|------|-----------|----------------|------------------|
| TINY | 3 | 100 | 300 |
| SMALL | 5 | 150 | 400 |
| MEDIUM | 10 | 300 | 600 |
| LARGE | 20 | 500 | 1,000 |
| XLARGE | 50 | 1,000 | 2,000 |

## Budget Allocation

O context window e dividido em partes:

| Componente | Percentual |
|------------|------------|
| System Prompt | 25% |
| Memory | 20% |
| Conversation | 40% |
| User Input | 10% |
| Reserve | 5% |

Exemplo para llama3.2 (8,192 tokens, 90% efetivo = 7,372):
- System Prompt: 1,843 tokens
- Memory: 1,474 tokens
- Conversation: 2,949 tokens
- User Input: 737 tokens

## Progressive Summary

Quando o historico atinge 80% do budget, o sistema:
1. Pega os 30% mais antigos das mensagens
2. Gera um resumo (via LLM ou extractive)
3. Substitui as mensagens brutas pelo resumo
4. Libera tokens para novas mensagens

```python
# Automatico no build_context()
result = manager.build_context(
    system_prompt="...",
    memory_context="...",
    user_input="...",
)

if result.was_compressed:
    print(f"Historico comprimido! Resumo: {result.summary_context}")
```

### Resumo Extractive (Sem LLM)

Se nao houver LLM disponivel, usa resumo extractive:
- Extrai primeira frase de cada mensagem
- Mantem as 2 primeiras e 2 ultimas
- Adiciona "..." no meio

### Resumo via LLM

Se LLM disponivel, gera resumo narrativo:
```
"O usuario perguntou sobre X. Discutimos Y e Z.
Preferencia identificada: cafe sem acucar."
```

## Uso Basico

### Criar Manager

```python
from src.soul.context_window import ContextWindowManager

manager = ContextWindowManager(
    entity_id="luna",
    model_name="llama3.2",
)
```

### Adicionar Turnos

```python
manager.add_turn("user", "Ola, como voce esta?")
manager.add_turn("assistant", "Estou bem, obrigada!")
```

### Construir Contexto

```python
result = manager.build_context(
    system_prompt=soul_prompt,
    memory_context=memory.retrieve(query),
    user_input="Nova pergunta do usuario",
    emotional_context="[HUMOR: curiosa]",
)

# Usar os valores truncados/otimizados
final_prompt = result.system_prompt + result.memory_context + ...
```

### Ou Usar build_prompt()

```python
prompt = manager.build_prompt(
    system_prompt=soul_prompt,
    memory_context=memory.retrieve(query),
    user_input="Nova pergunta",
)
# Prompt ja montado e otimizado
```

### Verificar Uso

```python
stats = manager.get_usage_stats()
print(f"Usando {stats['usage_percentage']}% do contexto")
print(f"Compressoes: {stats['compression_stats']['total_compressions']}")
```

## Configuracao Personalizada

```python
from src.soul.context_window import (
    ContextWindowConfig,
    BudgetAllocation,
    HistoryLimits,
    get_model_profile,
)

profile = get_model_profile("llama3.2")
config = ContextWindowConfig(
    model_profile=profile,
    budget_allocation=BudgetAllocation(
        system_prompt_pct=0.30,  # Mais espaco para system
        memory_pct=0.15,
        conversation_pct=0.40,
        user_input_pct=0.10,
        reserve_pct=0.05,
    ),
    history_limits=HistoryLimits(
        max_turns=8,
        max_chars_per_turn=200,
        summary_threshold_pct=0.75,  # Comprimir mais cedo
        summary_compress_pct=0.40,   # Comprimir mais mensagens
    ),
    enable_progressive_summary=True,
)
```

## Integracao com ContextBuilder Existente

O ContextBuilder existente pode usar o manager:

```python
class ContextBuilder:
    def __init__(self, entity_id: str, model_name: str = "llama3.2"):
        from src.soul.context_window import get_context_window_manager
        self._window_manager = get_context_window_manager(entity_id, model_name)

    def build(self, user_input: str, conversation_history: list):
        # Usar limites do manager
        max_chars = self._window_manager.memory_max_chars
        mem = self.memory.retrieve(user_input, max_chars=max_chars)
        ...
```

## Metricas

O manager registra:
- Tokens usados por componente
- Porcentagem de uso do contexto
- Numero de compressoes realizadas
- Tokens economizados com compressao
- Ratio medio de compressao

## Testes

38 testes em `src/tests/test_context_window.py`:

- TestModelSize: 1 teste
- TestModelProfile: 3 testes
- TestGetModelProfile: 4 testes
- TestBudgetAllocation: 1 teste
- TestHistoryLimits: 1 teste
- TestContextWindowConfig: 4 testes
- TestGetContextConfig: 2 testes
- TestSummaryResult: 1 teste
- TestProgressiveSummary: 8 testes
- TestContextUsage: 1 teste
- TestContextWindowManager: 9 testes
- TestGetContextWindowManager: 3 testes

## Exemplo Completo

```python
from src.soul.context_window import ContextWindowManager

# Criar manager para o modelo atual
manager = ContextWindowManager(
    entity_id="luna",
    model_name="llama3.2",
)

# Simular conversa longa
for i in range(30):
    manager.add_turn("user", f"Pergunta {i}: " + "x" * 200)
    manager.add_turn("assistant", f"Resposta {i}: " + "y" * 200)

# Construir contexto (compressao automatica se necessario)
result = manager.build_context(
    system_prompt="Voce e Luna...",
    memory_context="Usuario gosta de cafe",
    user_input="Qual foi minha primeira pergunta?",
)

print(f"Comprimido: {result.was_compressed}")
print(f"Tokens usados: {result.usage.total_tokens}")

# Ver estatisticas
stats = manager.get_usage_stats()
print(f"Uso: {stats['usage_percentage']}%")
print(f"Compressoes: {stats['compression_stats']['total_compressions']}")
print(f"Tokens salvos: {stats['compression_stats']['total_tokens_saved']}")
```

## Antes vs Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Limites | Magic numbers | ModelProfile |
| Ajuste | Manual | Automatico por tamanho |
| Compressao | Truncamento bruto | Progressive Summary |
| Configuracao | Espalhada | ContextWindowConfig |
| Metricas | Nenhuma | get_usage_stats() |
