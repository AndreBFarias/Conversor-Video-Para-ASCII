# 2025-12-29: ETAPA 12 - Streaming Response

## Objetivo
Implementar streaming de respostas LLM token-by-token para melhor UX.

## Arquitetura de Streaming

```
[User Input]
     |
     v
[ResponsePipeline.process_stream()]
     |
     +---> context build
     |
     +---> prompt ready
     |
     +---> [LLM Stream] ---> chunk1 --> chunk2 --> ... --> chunkN
     |
     +---> llm_complete
     |
     +---> parsed (animation, fala_tts)
     |
     v
[complete]
```

## Arquivos Modificados

### src/soul/providers/base.py
Adicionados metodos opcionais na classe base:

- `generate_stream(prompt, system, **kwargs) -> Generator[str, None, None]`
  - Implementacao default: faz fallback para `generate()` e retorna texto completo

- `supports_streaming() -> bool`
  - Retorna False por default
  - Providers com streaming real sobrescrevem para True

### src/soul/providers/ollama_provider.py
Implementado streaming nativo via `OllamaSyncClient.stream()`:

```python
def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
    for chunk in client.stream(prompt, model, system, ...):
        yield chunk

def supports_streaming(self) -> bool:
    return True
```

### src/soul/providers/gemini_provider.py
Implementado streaming via `generate_content_stream`:

```python
def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
    response = client.models.generate_content_stream(...)
    for chunk in response:
        if chunk.text:
            yield chunk.text

def supports_streaming(self) -> bool:
    return True
```

### src/soul/providers/universal_llm.py
Adicionado metodo com fallback chain:

```python
def generate_stream(self, prompt: str, system: str, **kwargs) -> Generator[str, None, None]:
    # Prioriza providers com streaming
    streaming_providers = [p for p in available if p.supports_streaming()]

    # Tenta cada provider ate um funcionar
    for provider in streaming_providers:
        try:
            for chunk in provider.generate_stream(prompt, system, **kwargs):
                yield chunk
            return
        except Exception:
            continue  # fallback para proximo
```

### src/soul/response_pipeline.py
Completado `process_stream()` com:

- Stages de progresso: context, prompt_ready, chunk, llm_complete, parsed, complete
- Acumulacao de texto para parsing final
- Callback opcional `llm_stream_caller`
- Atualizacao de memoria apos completar
- Timing em milliseconds

## Testes Adicionados

### src/tests/test_streaming.py (33 testes total)
Novos testes:

**TestProviderBaseStreaming** (2 testes)
- `test_base_supports_streaming_default_false`
- `test_base_generate_stream_fallback`

**TestOllamaProviderStreaming** (2 testes)
- `test_supports_streaming`
- `test_generate_stream_yields_chunks`

**TestGeminiProviderStreaming** (1 teste)
- `test_supports_streaming`

**TestUniversalLLMStreaming** (2 testes)
- `test_generate_stream_uses_streaming_provider`
- `test_generate_stream_fallback_on_error`

**TestResponsePipelineProcessStream** (2 testes)
- `test_process_stream_yields_stages`
- `test_process_stream_accumulates_text`

## Uso

### Streaming direto via UniversalLLM:
```python
from src.soul.providers import get_universal_llm

llm = get_universal_llm()
for chunk in llm.generate_stream(prompt, system):
    print(chunk, end="", flush=True)
```

### Streaming via ResponsePipeline:
```python
from src.soul.response_pipeline import get_response_pipeline
from src.soul.providers import get_universal_llm

pipeline = get_response_pipeline("luna")
llm = get_universal_llm()

def stream_caller(prompt):
    return llm.generate_stream(prompt, system)

for event in pipeline.process_stream(user_input, llm_stream_caller=stream_caller):
    if event["stage"] == "chunk":
        print(event["text"], end="", flush=True)
    elif event["stage"] == "complete":
        print(f"\nCompleto em {event['timing_ms']}ms")
```

## Validacao

- [x] `generate_stream` adicionado a base.py
- [x] OllamaProvider implementa streaming
- [x] GeminiProvider implementa streaming
- [x] UniversalLLM com fallback de stream
- [x] ResponsePipeline.process_stream completo
- [x] 33 testes passando
- [x] Pre-commit passa

## Proximos Passos (para integracao UI)

1. Criar callback em `widgets.py` para receber chunks
2. Atualizar `TextArea` gradualmente
3. Animacao de "pensando" enquanto aguarda primeiro chunk
4. Sincronizar TTS com chunks usando `SentenceStreamer`
