# 2025-12-29: ETAPA 07 - Universal LLM Interface

## Objetivo
Criar abstraction layer para providers LLM com fallback automatico.

## Arquivos Criados

### src/soul/providers/
- `__init__.py` - Exports publicos do modulo
- `base.py` - Interface LLMProvider ABC com:
  - `LLMResponse` dataclass
  - `HealthCheckResult` dataclass
  - `ProviderStatus` enum
  - Circuit breaker integrado
- `gemini_provider.py` - Provider para Google Gemini
- `ollama_provider.py` - Provider para Ollama local
- `universal_llm.py` - Orquestrador com fallback chain

### src/tests/test_universal_llm.py
- 18 testes cobrindo todas as funcionalidades

## Funcionalidades

### LLMProvider (Interface Base)
```python
class LLMProvider(ABC):
    def generate(self, prompt: str, system: str, **kwargs) -> LLMResponse
    def is_available(self) -> bool
    def health_check(self) -> HealthCheckResult
    def get_model_name(self) -> str
```

### UniversalLLM (Orquestrador)
- Fallback chain dinamico baseado em prioridade
- Circuit breaker por provider (3 falhas = circuit open)
- Callback `on_fallback` para notificacao
- Health check de todos os providers
- Status report com modelo ativo

### Integracao em consciencia.py
- `_universal_llm` inicializado no `__init__`
- `_on_llm_fallback()` - callback de fallback
- `_call_with_universal_llm()` - metodo wrapper
- `get_llm_status()` - status dos providers

## Fluxo de Fallback

```
Usuario envia mensagem
       |
       v
UniversalLLM.generate()
       |
       v
[Provider Primario] --> SUCESSO --> Retorna resposta
       |
       | FALHA (circuit breaker ativo)
       v
[Provider Secundario] --> SUCESSO --> Retorna resposta (fallback_used=True)
       |
       | FALHA
       v
RuntimeError("Todos os providers falharam")
```

## Testes
- 18 testes passando
- Cobertura: providers base, Gemini, Ollama, UniversalLLM, singleton

## Validacao GUI
- [ ] Rodar com Ollama -> funciona
- [ ] Matar Ollama -> fallback pra Gemini automatico
- [ ] Log mostra "LLM Fallback: ollama -> gemini"
