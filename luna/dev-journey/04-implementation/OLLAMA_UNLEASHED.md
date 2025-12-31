# Ollama Unleashed - Configuracao de Alta Performance

```
STATUS: PRODUCAO
CONTEXTO: 8192 tokens (vs 2048 default)
GPU: 100% VRAM (vs ~50% default)
```

## Problema

Configuracao padrao do Ollama e conservadora:
1. Context window pequeno (2048 tokens)
2. Modelo parcialmente na GPU (camadas na CPU = 50x mais lento)
3. Modelo descarregado apos 5 minutos de inatividade

## Solucao

Configuracao agressiva para hardware dedicado:
1. `num_ctx: 8192` - Contexto 4x maior
2. `num_gpu: -1` - Todas as camadas na GPU
3. `keep_alive: 30m` - Modelo na VRAM por 30 minutos

## Configuracao

### Via .env (Recomendado)

```bash
# Contexto (default: 8192)
OLLAMA_NUM_CTX=8192

# GPU layers (-1 = todas)
OLLAMA_NUM_GPU=-1

# Manter modelo na VRAM (default: 30m)
OLLAMA_KEEP_ALIVE=30m

# Timeout de requisicao (default: 120s)
OLLAMA_TIMEOUT=120
```

### Via config.py

```python
OLLAMA_CONFIG = {
    "BASE_URL": "http://localhost:11434",
    "TIMEOUT": 120,
    "NUM_CTX": 8192,
    "NUM_GPU": -1,
    "KEEP_ALIVE": "30m",
    ...
}
```

## Modelos Recomendados

### Para RTX 3050 (4GB VRAM)

| Modelo | VRAM | Uso |
|--------|------|-----|
| `llama3.2:3b` | ~2GB | Chat rapido |
| `dolphin-mistral` | ~4GB | Roleplay, sem censura |
| `phi3:mini` | ~2.2GB | Rapido, inteligente |

### Para RTX 3060+ (8GB+ VRAM)

| Modelo | VRAM | Uso |
|--------|------|-----|
| `llama3.1:8b` | ~5GB | Chat de alta qualidade |
| `hermes3:8b` | ~5GB | Roleplay avancado |
| `qwen2.5-coder:7b` | ~5GB | Codigo |
| `minicpm-v` | ~4GB | Vision |

## Instalacao de Modelos

```bash
# Modelo principal (escolha um)
ollama pull dolphin-mistral
ollama pull llama3.2:3b

# Fallback (menor)
ollama pull llama3.2:3b

# Vision
ollama pull minicpm-v

# Codigo
ollama pull qwen2.5-coder:7b
```

## Verificacao de Performance

```bash
# Ver modelos carregados
ollama ps

# Deve mostrar:
# NAME              SIZE      PROCESSOR
# dolphin-mistral   4.1 GB    100% GPU
```

Se mostrar `CPU` ou menos de 100% GPU, aumente a VRAM disponivel ou use modelo menor.

## Otimizacao de VRAM

```bash
# Descarregar modelos nao usados
ollama stop dolphin-mistral

# Ou via API
curl http://localhost:11434/api/generate -d '{"model": "dolphin-mistral", "keep_alive": 0}'
```

## Arquitetura

```
.env
  |
  v
config.py (OLLAMA_CONFIG)
  |
  v
sync_client.py / async_client.py
  |
  +-- payload["options"]["num_ctx"]
  +-- payload["options"]["num_gpu"]
  +-- payload["keep_alive"]
```

## Troubleshooting

### Modelo lento

```bash
# Verificar se esta 100% GPU
ollama ps

# Se nao, use modelo menor
ollama pull llama3.2:3b
```

### Sem memoria

```bash
# Descarregar todos os modelos
curl http://localhost:11434/api/generate -d '{"model": "dolphin-mistral", "keep_alive": 0}'
curl http://localhost:11434/api/generate -d '{"model": "minicpm-v", "keep_alive": 0}'

# Verificar VRAM
nvidia-smi
```

### Timeout

```bash
# Aumentar timeout
export OLLAMA_TIMEOUT=180
```

## Metricas

| Configuracao | Tokens/s | Latencia |
|--------------|----------|----------|
| Default (CPU parcial) | ~5-10 | ~5s |
| Otimizado (100% GPU) | ~30-50 | ~1s |

## Testes

```bash
pytest src/tests/test_ollama_config.py -v
```

---

*Implementado em 2025-12-31*
