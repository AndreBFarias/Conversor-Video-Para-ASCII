# Performance - Metricas de Desempenho

> **TL;DR:** Metricas de latencia, throughput e uso de recursos do projeto Luna.

## Contexto

Este documento registra as metricas de performance do sistema Luna, incluindo tempos de resposta, uso de recursos e benchmarks. Atualizado periodicamente para acompanhar otimizacoes.

## Metricas de Latencia

### Pipeline Completo (Voz-a-Voz)

```
User fala → Transcricao → LLM → TTS → Audio reproduzido
    ↓           ↓          ↓       ↓
  ~1.0s      ~1.0s      ~2.5s   ~1.2s   = ~5.7s total
```

### Breakdown por Componente (v2.2.0)

| Componente | Latencia Media | P95 | P99 |
|------------|----------------|-----|-----|
| Deteccao de Silencio (VAD) | 50ms | 80ms | 120ms |
| Transcricao (Whisper medium) | 1.0s | 1.5s | 2.0s |
| Gemini LLM | 2.5s | 4.0s | 6.0s |
| Embedding | 0.8s | 1.2s | 1.5s |
| TTS (ElevenLabs) | 1.2s | 1.8s | 2.5s |
| TTS (Coqui local) | 2.0s | 3.0s | 4.0s |

### Comparativo de Versoes

| Versao | Latencia Total | Otimizacao |
|--------|----------------|------------|
| v1.0.0 | ~3.0s (texto) | Baseline |
| v2.0.0 | ~7.0s (voz) | +multimodal |
| v2.2.0 | ~5.7s (voz) | -19% vs v2.0 |

## Uso de Recursos

### RAM

| Componente | Consumo |
|------------|---------|
| App base (Textual) | ~150MB |
| Whisper (medium) | ~400MB |
| Sentence-Transformers | ~200MB |
| Cache semantico | ~50MB |
| **Total medio** | **~800MB** |

### CPU

| Estado | Uso |
|--------|-----|
| Idle (aguardando input) | 5-10% |
| Capturando audio | 15-20% |
| Transcricao Whisper | 60-80% |
| Processamento LLM | 20-30% |
| TTS local (Coqui) | 50-70% |

### GPU (Quando disponivel)

| Componente | VRAM | Speedup |
|------------|------|---------|
| Whisper (CUDA) | ~2GB | 3-5x |
| Coqui TTS (CUDA) | ~4GB | 2-3x |
| Sentence-Transformers | ~1GB | 2x |

## Benchmarks

### Transcricao Whisper

```
Modelo: medium
Audio: 10 segundos
Device: CPU (i7-12700)

Configuracao Default:
  beam_size=5, best_of=5
  Tempo: 2.1s

Configuracao Otimizada (v2.2.0):
  beam_size=3, best_of=1, vad_filter=True
  Tempo: 1.0s
  Speedup: 2.1x
```

### Cache Semantico

```
Threshold: 0.85
Max Size: 100 entries
TTL: 3600s

Teste com 100 queries:
  Cache hits: 42
  Cache misses: 58
  Hit rate: 42%

Economia de API calls: ~40%
```

### Threading

```
Threads ativas: 7
  - AudioCapture
  - Transcription
  - Processing
  - Coordinator
  - Animation
  - TTS
  - Monitor

Queue sizes (max):
  audio_queue: 100
  transcription_queue: 50
  processing_queue: 20
  response_queue: 10
  tts_queue: 30

Deadlocks detectados (v2.2.0): 0
```

## Gargalos Identificados

### 1. Gemini LLM (2.5s)
- **Problema**: Maior contribuidor de latencia
- **Mitigacao**: Cache semantico, streaming (futuro)

### 2. TTS Local Coqui (2.0s)
- **Problema**: Lento sem GPU
- **Mitigacao**: ElevenLabs como alternativa, GPU quando disponivel

### 3. Whisper CPU (1.0s)
- **Problema**: Poderia ser mais rapido com GPU
- **Mitigacao**: Modelo otimizado, VAD agressivo

## Metas de Performance

### Atual vs Meta

| Metrica | Atual | Meta v3.0 | Meta v4.0 |
|---------|-------|-----------|-----------|
| Latencia voz-a-voz | 5.7s | 4.5s | 3.0s |
| Cache hit rate | 42% | 50% | 60% |
| RAM usage | 800MB | 700MB | 600MB |
| Startup time | 8s | 5s | 3s |

## Ambiente de Teste

```
Hardware:
  CPU: Intel i7-12700 (12 cores)
  RAM: 32GB DDR4
  GPU: NVIDIA RTX 3050 (4GB VRAM)
  Storage: NVMe SSD

Software:
  OS: Pop!_OS 22.04
  Python: 3.10.12
  CUDA: 12.1 (quando usado)
```

## TODO

- [ ] Implementar streaming para Gemini
- [ ] Habilitar GPU para Whisper
- [ ] Otimizar startup time
- [ ] Adicionar metricas de memoria detalhadas

## Links Relacionados

- [CODE_STATS.md](./CODE_STATS.md)
- [MILESTONES.md](./MILESTONES.md)
- [CURRENT_STATUS.md](../04-implementation/CURRENT_STATUS.md)
- [TECHNICAL_DEBT.md](../05-future/TECHNICAL_DEBT.md)

---
*Ultima atualizacao: 2025-12-18*
