# Otimizacao de Performance - Luna

## Resumo das Melhorias

Data: 2025-12-19

---

## 1. Correcao Critica: TTSPlaybackThread

### Problema
A `TTSPlaybackThread` existia no codigo mas nao era registrada no `setup_threading()` do `main.py`. Isso causava:
- Playback de audio acontecendo em thread incorreta
- Potencial bloqueio do pipeline
- Evento `luna_speaking_event` nao sendo setado corretamente

### Solucao
Arquivo: `main.py:404-407`
```python
self.threading_manager.register_thread(
    "tts_playback",
    TTSPlaybackThread(self.threading_manager, self.boca)
)
```

---

## 2. Sistema de Profiling v2

### Arquivo: `src/core/profiler.py`

### Novas Funcionalidades

#### 2.1 InteractionTrace
Rastreia cada interacao do inicio ao fim com timeline visual:
```
[INTERACTION #1] Timeline:
  stt.whisper          | 1234.5ms |============| [SLOW]
  llm.process          |  890.2ms |========| [OK]
  tts.generate         | 1567.8ms |===============| [SLOW]
  TOTAL                | 3692.5ms |
```

#### 2.2 Thresholds por Estagio
Limites de latencia configurados para cada estagio:
```python
LATENCY_THRESHOLDS = {
    "audio_capture": 50,     # ms
    "vad": 30,
    "stt.whisper": 2000,
    "stt.inference": 1500,
    "llm.process": 3000,
    "llm.request": 2500,
    "tts.generate": 2000,
    "tts.playback": 5000,
    "animation": 50,
    "ui.update": 100,
    "pipeline": 8000,
}
```

#### 2.3 Alertas Automaticos
Quando latencia excede threshold, alerta e dispara:
```
[PROFILER] [WARNING] stt.whisper excedeu threshold: 2500ms > 2000ms
```

#### 2.4 Recomendacoes
Cada gargalo vem com sugestao de acao:
```python
recommendations = {
    "stt.whisper": "Considere usar modelo menor (tiny/base) ou habilitar GPU",
    "llm.process": "LLM lento: considere cache semantico ou modelo local",
    "tts.generate": "TTS lento: considere Piper (mais leve) ou pre-cache",
}
```

---

## 3. Pipeline de Threads

### Arquitetura Atual (Corrigida)

```
[MIC] --> AudioCaptureThread --> audio_input_queue (RingBuffer)
                                      |
                                      v
[VAD+WHISPER] TranscriptionThread --> transcription_queue
                                           |
                                           v
[GEMINI/OLLAMA] ProcessingThread --> response_queue
                                           |
                     +---------------------+---------------------+
                     v                                           v
            animation_queue                               tts_queue
                   |                                            |
                   v                                            v
           AnimationThread                                TTSThread
                                                               |
                                                               v
                                                     tts_playback_queue
                                                               |
                                                               v
                                                     TTSPlaybackThread [NOVA]

[MONITOR] MonitorThread (health check a cada 30s)
[COORDINATOR] CoordinatorThread (UI updates)
```

### Eventos de Sincronizacao
- `interrupt_event` - Para Luna no meio da fala
- `shutdown_event` - Sinalizador global de parada
- `user_speaking_event` - Usuario detectado falando
- `luna_speaking_event` - Luna esta falando (TTS)
- `listening_event` - Ativar/desativar captura de audio
- `whisper_ready_event` - Whisper carregado e pronto
- `tts_ready_event` - TTS pronto
- `audio_ready_event` - AudioCapture pronto

---

## 4. Harmonizacao Visual do Canone

### Alteracoes
- Substituido `Button` por `GlitchButton` nos botoes do Canone
- CSS ajustado para mesmas dimensoes da main (width: 15, height: 3)
- Efeito glitch ativo nos botoes de acao

---

## 5. Script de Diagnostico

### Arquivo: `src/tools/diagnostico_luna.py`

Testa cada modulo isoladamente:
1. Config - Variaveis de ambiente
2. ThreadingManager - Filas e RingBuffer
3. Profiler - Sistema de rastreamento
4. AudioDevices - Dispositivos de entrada
5. VADConfig - Configuracoes de deteccao de voz
6. WhisperLoad - Carregamento do modelo STT
7. TTSEngine - Engine de sintese de voz
8. AnimationFrames - Animacoes ASCII
9. OllamaConnection - Conexao local
10. GeminiConnection - Conexao cloud

### Uso
```bash
python src/tools/diagnostico_luna.py
```

---

## 6. Proximos Passos

### Otimizacoes Pendentes
1. **VAD Tuning** - Ajustar thresholds de energia e silencio
2. **Whisper Streaming** - Implementar transcricao em tempo real
3. **TTS Chunking** - Dividir respostas longas em chunks
4. **Pre-warming** - Aquecer modelos no startup

### Metricas a Monitorar
- Latencia end-to-end (user speech -> playback)
- Taxa de drops no RingBuffer
- Cache hit rate (semantico e resposta)
- Quotas de API consumidas

---

## 7. Como Usar o Profiler

### Obter Diagnostico
```python
from src.core.profiler import get_pipeline_logger

plog = get_pipeline_logger()
print(plog.get_diagnostics())
```

### Instrumentar Novo Codigo
```python
from src.core.profiler import get_profiler, profile

profiler = get_profiler()

# Opcao 1: Context manager
with profiler.span("meu.estagio"):
    # codigo lento
    pass

# Opcao 2: Decorator
@profile("meu.estagio")
def minha_funcao():
    pass
```

### Ver Gargalos
```python
profiler = get_profiler()
bottlenecks = profiler.get_bottlenecks()
for b in bottlenecks:
    print(f"[{b['severity']}] {b['stage']}: {b['avg_ms']:.1f}ms")
    print(f"  Acao: {b['recommendation']}")
```

---

"O que nao me mata, me fortalece." - Friedrich Nietzsche
