# Integracao Multi-LLM Luna

## Visao Geral

Luna suporta multiplos providers de LLM com estrategia local-first:
1. **Local (Ollama)**: Privacidade total, sem custo por request
2. **API (Gemini)**: Fallback quando local indisponivel

## Arquitetura

```
Usuario -> Router -> Fallback Manager -> Provider
                          |
                    Local disponivel?
                    /            \
                  Sim             Nao
                   |               |
               Ollama          Gemini API
```

## Componentes

### 1. Router (`src/core/router.py`)
Detecta o intent da mensagem:
- `CHAT`: Conversa casual
- `CODE`: Geracao/explicacao de codigo
- `VISION`: Analise de imagens
- `SYSTEM`: Comandos internos

```python
from src.core import detect_intent, Intent

intent = detect_intent("Escreva um codigo Python")
# Intent.CODE
```

### 2. Ollama Client (`src/core/ollama_client.py`)
Wrapper async para API Ollama:

```python
from src.core import get_ollama_client

client = get_ollama_client()
response = await client.generate(
    prompt="Ola!",
    model="dolphin-mistral",
    temperature=0.7
)
print(response.text)
```

### 3. Fallback Manager (`src/core/fallback_manager.py`)
Gerencia fallback automatico:

```python
from src.core import get_fallback_manager, Intent

manager = get_fallback_manager()
text, error, success = await manager.generate_with_fallback(
    prompt="Explique Python",
    intent=Intent.CHAT
)
```

### 4. Modelos Especializados (`src/core/models/`)

**DolphinChat** - Chat com personalidade Luna:
```python
from src.core.models import DolphinChat
chat = DolphinChat()
response = await chat.chat("Como voce esta?")
```

**QwenCoder** - Geracao de codigo:
```python
from src.core.models import QwenCoder
coder = QwenCoder()
response = await coder.generate("Funcao para ordenar lista")
```

**MiniCPMVision** - Analise de imagens:
```python
from src.core.models import MiniCPMVision
vision = MiniCPMVision()
response = await vision.describe(image_base64)
```

## Configuracao

### .env
```bash
# Providers
CHAT_PROVIDER=local
CODE_PROVIDER=local
VISION_PROVIDER=gemini

# Ollama
OLLAMA_HOST=http://localhost:11434

# Modelos locais
CHAT_LOCAL_MODEL=dolphin-mistral
CODE_LOCAL_MODEL=qwen2.5-coder:7b
VISION_LOCAL_MODEL=minicpm-v

# API Keys (fallback)
GOOGLE_API_KEY=sua_chave_aqui
```

### Instalacao Ollama
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar servico
ollama serve

# Baixar modelos
ollama pull dolphin-mistral
ollama pull qwen2.5-coder:7b
ollama pull minicpm-v
```

## Testes

```bash
# Testar providers
python tests/test_providers.py
```

Output esperado:
```
[TEST] Ollama Health Check...
  [OK] Ollama esta rodando
[TEST] Verificando modelo: dolphin-mistral...
  [OK] Modelo dolphin-mistral disponivel
...
Total: 7/7 testes passaram
```

## Fluxo de Fallback

1. Usuario envia mensagem
2. Router detecta intent (CHAT/CODE/VISION)
3. FallbackManager verifica se local esta disponivel
4. Se local OK: usa Ollama
5. Se local FAIL: usa Gemini API
6. Retorna resposta ao usuario

## Metricas

O sistema registra latencias para cada provider:

```python
from src.soul.metricas import get_latency_tracker

tracker = get_latency_tracker()
stats = tracker.get_stats()
# {'llm': {'avg': 1.2, 'max': 3.4, 'target': 2.0}}
```

Targets de latencia:
- STT: 0.8s
- LLM: 2.0s
- TTS Generate: 3.0s
- TTS Playback: 0.5s

## Troubleshooting

### Ollama nao responde
```bash
# Verificar se esta rodando
curl http://localhost:11434/api/tags

# Reiniciar
systemctl restart ollama
# ou
ollama serve
```

### Modelo nao encontrado
```bash
# Listar modelos
ollama list

# Baixar modelo faltante
ollama pull nome-do-modelo
```

### API rate limit
O FallbackManager detecta erros 429 e faz backoff automatico.
Verifique quotas em console.cloud.google.com

## Performance

### GPU
```bash
# Verificar se Ollama usa GPU
nvidia-smi
# Deve mostrar ollama usando VRAM
```

### CPU
Se sem GPU, modelos rodam em CPU. Considere:
- Usar modelos menores (7b vs 13b)
- Aumentar RAM disponivel
- Usar quantizacao (q4_0, q5_0)
