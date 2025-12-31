# Luna - Integracao Multi-LLM

Documentacao tecnica da arquitetura de integracao de multiplos provedores LLM.

---

## Visao Geral

Luna suporta multiplos provedores de LLM com fallback automatico entre local e API.

```
┌─────────────────────────────────────────────────────────────────┐
│                         LUNA                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FUNCAO          LOCAL (Gratis)         PAGO (Opcional)         │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  VOZ (TTS)       Coqui/Piper             ElevenLabs API         │
│  OUVIDO (STT)    Faster-Whisper          Whisper API            │
│  VISAO           MiniCPM-V               Gemini Flash Vision    │
│  CONVERSA        Dolphin Mistral         Gemini Flash/Pro       │
│  CODIGO          Qwen2.5 Coder           DeepSeek API           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Arquitetura

### Componentes Principais

```
src/core/
├── router.py           # Detecta intent do usuario
├── fallback_manager.py # Gerencia fallback local/API
├── ollama_client.py    # Cliente async para Ollama
└── models/
    ├── dolphin.py          # Wrapper para chat (Dolphin Mistral)
    ├── qwen_coder.py       # Wrapper para codigo (Qwen2.5)
    └── minicpm_vision.py   # Wrapper para visao (MiniCPM-V)
```

### Fluxo de Processamento

```
Usuario envia mensagem
        │
        ▼
┌───────────────────┐
│  detect_intent()  │ ─── Analisa patterns no texto
└────────┬──────────┘
         │
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
  CHAT      CODE     VISION
    │         │         │
    ▼         ▼         ▼
┌───────────────────────────────────┐
│       FallbackManager             │
│                                   │
│  1. Verifica provider preferido   │
│  2. Se local, testa Ollama        │
│  3. Se falhar, usa API            │
└───────────────────────────────────┘
         │
         ▼
   Resposta gerada
```

---

## Configuracao

### Variaveis de Ambiente

```bash
# Providers disponiveis: local | gemini | openai | elevenlabs | deepseek

# Chat (persona Luna)
CHAT_PROVIDER=gemini          # gemini = API, local = Ollama
CHAT_LOCAL_MODEL=dolphin-mistral
CHAT_LOCAL_TEMPERATURE=0.85

# Codigo
CODE_PROVIDER=local           # local = Ollama Qwen
CODE_LOCAL_MODEL=qwen2.5-coder:7b
CODE_LOCAL_TEMPERATURE=0.3

# Visao
VISION_PROVIDER=gemini        # gemini = API, local = Ollama MiniCPM
VISION_LOCAL_MODEL=minicpm-v

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120
```

### Instalacao dos Modelos Locais

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelos
ollama pull dolphin-mistral      # Chat (~4GB)
ollama pull qwen2.5-coder:7b     # Codigo (~4GB)
ollama pull minicpm-v            # Visao (~4GB)

# Verificar modelos
ollama list
```

---

## Router de Intents

O router detecta automaticamente a intencao do usuario:

### Intent.CHAT
- Conversas normais
- Perguntas gerais
- Interacoes sociais

### Intent.CODE
Detectado por patterns como:
- `python`, `sql`, `javascript`
- `funcao`, `classe`, `script`
- `pandas`, `dataframe`, `query`
- `git`, `docker`, `api`

### Intent.VISION
Detectado por:
- Imagem anexada
- `o que voce ve`, `analise`, `descreva`
- `camera`, `foto`, `tela`

### Intent.SYSTEM
- Comandos que iniciam com `/`
- `/nova`, `/historico`, `/ajuda`

---

## FallbackManager

Gerencia fallback automatico entre provedores.

### Uso Basico

```python
from src.core.fallback_manager import get_fallback_manager
from src.core.router import Intent

manager = get_fallback_manager()

# Geracao com fallback automatico
text, error, success = await manager.generate_with_fallback(
    prompt="Explique recursao",
    intent=Intent.CHAT,
    system="Voce e Luna, uma assistente gotica."
)

# Para codigo
code, error, success = await manager.code_with_fallback(
    prompt="Funcao que calcula fatorial",
    language="python"
)

# Para visao
desc, error, success = await manager.vision_with_fallback(
    image_base64="...",
    prompt="O que voce ve?"
)
```

### Verificar Saude dos Providers

```python
health = await manager.get_health_summary()
# {
#     "ollama": {"status": "available", "latency": 0.05},
#     "gemini": {"status": "available"}
# }
```

---

## Modelos Especializados

### DolphinChat (Chat)

```python
from src.core.models.dolphin import get_dolphin_chat

chat = get_dolphin_chat()

# Chat simples
response = await chat.chat("Ola, como voce esta?")
print(response.text)

# Chat com historico
response = await chat.chat("E voce?", include_history=True)

# Streaming
async for chunk in chat.chat_stream("Conte uma historia"):
    print(chunk, end="", flush=True)
```

### QwenCoder (Codigo)

```python
from src.core.models.qwen_coder import get_qwen_coder, CodeLanguage

coder = get_qwen_coder()

# Gerar codigo
response = await coder.generate(
    prompt="Funcao que ordena lista",
    language=CodeLanguage.PYTHON
)
print(response.code)

# Corrigir erro
fixed = await coder.fix_code(
    code="def soma(a, b)\n    return a + b",
    error_message="SyntaxError: expected ':'"
)

# Explicar codigo
explanation = await coder.explain_code("def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)")
```

### MiniCPMVision (Visao)

```python
from src.core.models.minicpm_vision import get_minicpm_vision

vision = get_minicpm_vision()

# Descrever imagem
response = await vision.describe_from_file("/path/to/image.jpg")
print(response.description)
print(f"Objetos: {response.objects}")
print(f"Pessoas: {response.people_count}")

# Detectar mudancas
changed, description = await vision.detect_changes(
    current_image=base64_image,
    previous_description="Sala vazia com computador"
)

# Ler texto na imagem
text = await vision.read_text(base64_image)
```

---

## OllamaClient

Cliente baixo nivel para Ollama.

### Async

```python
from src.core.ollama_client import get_ollama_client

client = get_ollama_client()

# Health check
healthy = await client.check_health()

# Listar modelos
models = await client.list_models()

# Geracao
response = await client.generate(
    prompt="Ola mundo",
    model="dolphin-mistral",
    system="Voce e uma assistente.",
    temperature=0.7,
    max_tokens=1024
)
print(response.text)

# Streaming
async for chunk in client.generate_stream(prompt="Conte ate 10"):
    print(chunk, end="")

# Visao
response = await client.vision(
    prompt="O que voce ve?",
    image_base64="..."
)

await client.close()
```

### Sync (para threads)

```python
from src.core.ollama_client import get_ollama_sync_client

client = get_ollama_sync_client()

response = client.generate(prompt="Ola", model="dolphin-mistral")
print(response.text)
```

---

## Testes

### Executar Suite Completa

```bash
./venv/bin/python tests/test_providers.py
```

### Teste Rapido

```bash
python tests/test_providers.py --quick
```

### Output Esperado

```
======================================================================
LUNA MULTI-LLM PROVIDER TEST SUITE
======================================================================

[INFO] Configuracao atual:
  CHAT_PROVIDER: gemini
  CODE_PROVIDER: local
  VISION_PROVIDER: gemini
  OLLAMA_BASE_URL: http://localhost:11434

[TEST] Ollama Health Check
  [OK] Ollama esta rodando
  [INFO] Modelos disponiveis: 5

[TEST] Modelo Chat: dolphin-mistral
  [OK] Modelo dolphin-mistral disponivel

[TEST] Geracao de Chat (Dolphin)
  [OK] Resposta em 2.35s
  [INFO] Texto: Ola, viajante das sombras...

[TEST] Deteccao de Intents
  [OK] 'Ola, como voce esta?'             -> chat     (esperado: chat)
  [OK] 'Escreva um codigo Python'         -> code     (esperado: code)
  [OK] 'O que voce ve na imagem?'         -> vision   (esperado: vision)

======================================================================
RESUMO DOS TESTES
======================================================================
  Total: 10/10 testes passaram

  [SUCCESS] Todos os testes passaram!
======================================================================
```

---

## Troubleshooting

### Ollama nao responde

```bash
# Verificar se esta rodando
curl http://localhost:11434/api/tags

# Iniciar servico
ollama serve

# Verificar logs
journalctl -u ollama -f
```

### Modelo nao encontrado

```bash
# Listar modelos instalados
ollama list

# Baixar modelo faltante
ollama pull dolphin-mistral

# Remover e reinstalar
ollama rm dolphin-mistral
ollama pull dolphin-mistral
```

### API Gemini falha

1. Verificar `GOOGLE_API_KEY` no `.env`
2. Testar quota em https://makersuite.google.com/
3. Verificar conexao com internet

### Timeout em requisicoes

Aumentar timeout no `.env`:
```bash
OLLAMA_TIMEOUT=180
GEMINI_TIMEOUT=30
```

---

## Metricas

O sistema coleta metricas de latencia automaticamente:

```python
from src.soul.metricas import get_latency_tracker

tracker = get_latency_tracker()

# Registrar latencia
tracker.record("llm", 2.5, {"provider": "local", "model": "dolphin-mistral"})

# Consultar estatisticas
stats = tracker.get_stats("llm")
# {"avg": 2.3, "min": 1.8, "max": 3.1, "count": 15}
```

---

## Proximos Passos

1. **Streaming no Chat**: Implementar resposta progressiva no terminal
2. **Cache Semantico**: Cachear respostas similares
3. **Balanceamento**: Distribuir carga entre local e API
4. **Metricas Avancadas**: Dashboard de performance

---

*"A tecnologia e melhor quando aproxima as pessoas." - Matt Mullenweg*
