# Luna - DNA da Arquitetura

## Mapeamento de Threads

```
+------------------+     +-------------------+     +------------------+
|  AUDIO_CAPTURE   | --> |  TRANSCRIPTION    | --> |   PROCESSING     |
|  (PyAudio)       |     |  (Whisper+VAD)    |     |   (LLM)          |
+------------------+     +-------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +-------------------+     +------------------+
|  audio_input     |     |  transcription    |     |   response       |
|  (RingBuffer)    |     |  (Queue)          |     |   (Queue)        |
+------------------+     +-------------------+     +------------------+
                                                          |
                                                          v
                                              +-------------------+
                                              |   COORDINATOR     |
                                              |   (UI Updates)    |
                                              +-------------------+
                                                    |    |
                                         +----------+    +----------+
                                         v                          v
                              +------------------+      +------------------+
                              |   ANIMATION      |      |   TTS            |
                              |   (Frames)       |      |   (Geracao)      |
                              +------------------+      +------------------+
                                                               |
                                                               v
                                                    +------------------+
                                                    |   TTS_PLAYBACK   |
                                                    |   (Audio Out)    |
                                                    +------------------+
```

## Threads Ativas

| Thread | Funcao | CPU | Bloqueio | Prioridade |
|--------|--------|-----|----------|------------|
| audio_capture | Captura mic | Baixa | I/O | Alta |
| transcription | Whisper STT | Alta (GPU) | CPU/GPU | Alta |
| processing | Gemini/Ollama | Baixa (rede) | I/O | Media |
| coordinator | UI updates | Baixa | - | Media |
| animation | Frames ASCII | Baixa | Timer | Baixa |
| tts | Geracao audio | Alta (GPU) | CPU/GPU | Media |
| tts_playback | Tocar audio | Baixa | I/O | Alta |
| monitor | Health check | Minima | Sleep | Baixa |

## Fluxo de Eventos (Timeline Tipica)

```
t=0.000s  [AUDIO_CAPTURE] Chunk capturado (1024 samples @ 16kHz = 64ms)
t=0.064s  [AUDIO_CAPTURE] Chunk enviado para audio_input_queue
t=0.065s  [TRANSCRIPTION] Chunk recebido, VAD analisa
t=0.070s  [VAD] RMS=1200 (threshold=6000), silence
...
t=1.500s  [VAD] RMS=8500, FALA DETECTADA
t=1.501s  [VAD] user_speaking_event.set()
t=2.800s  [VAD] Silencio detectado (12 frames)
t=2.801s  [WHISPER] Submetendo 1.3s de audio
t=3.500s  [WHISPER] Transcricao: "Ola Luna" (0.7s)
t=3.501s  [PROCESSING] Recebido, enviando para LLM
t=4.200s  [GEMINI] Resposta recebida (0.7s)
t=4.201s  [COORDINATOR] Atualizando UI
t=4.210s  [ANIMATION] Transicao para 'feliz'
t=4.220s  [TTS] Gerando audio (Coqui)
t=6.500s  [TTS] Audio gerado (2.3s)
t=6.501s  [PLAYBACK] Iniciando reproducao
t=6.502s  [PLAYBACK] luna_speaking_event.set()
t=9.000s  [PLAYBACK] Fim, luna_speaking_event.clear()
```

## Gargalos Identificados

### 1. Whisper Load Time (CRITICO)
- **Tempo**: 15-45s na primeira execucao
- **Causa**: Download/carregamento do modelo
- **Impacto**: audio_capture aguarda whisper_ready_event
- **Solucao**: Pre-loading assincrono ou modelo menor

### 2. TTS Coqui Generation (ALTO)
- **Tempo**: 2-5s por frase
- **Causa**: XTTS v2 e pesado mesmo com GPU
- **Impacto**: Delay entre resposta do LLM e fala
- **Solucao**: Piper como default (0.3s), Coqui sob demanda

### 3. Gemini Network Latency (MEDIO)
- **Tempo**: 0.5-2s
- **Causa**: RTT de rede + processamento
- **Impacto**: Usuario espera resposta
- **Solucao**: Streaming, cache semantico

### 4. Animation Frame Rate (BAIXO)
- **Tempo**: 12 FPS = 83ms/frame
- **Causa**: UI Textual refresh rate
- **Impacto**: Sensacao de lentidao visual
- **Solucao**: call_from_thread correto, batch updates

## Eventos de Sincronizacao

| Evento | Proposito | Setado Por | Limpo Por |
|--------|-----------|------------|-----------|
| whisper_ready_event | Whisper carregado | transcription | - |
| audio_ready_event | Audio stream aberto | audio_capture | - |
| tts_ready_event | TTS inicializado | tts | - |
| listening_event | Mic ativo | watch_em_chamada | watch_em_chamada |
| user_speaking_event | Usuario falando | VAD | VAD |
| luna_speaking_event | Luna falando | playback | playback |
| interrupt_event | Cancelar tudo | trigger_interrupt | clear_interrupt |
| shutdown_event | Encerrar app | stop_all_threads | - |

## Filas e Capacidades

| Fila | Capacidade | Tipo | Overflow |
|------|------------|------|----------|
| audio_input | 100 | RingBuffer | Descarta antigo |
| transcription | 50 | Queue | Bloqueia |
| processing | 20 | Queue | Bloqueia |
| response | 10 | Queue | Bloqueia |
| tts | 30 | Queue | Bloqueia |
| tts_playback | 30 | Queue | Bloqueia |
| animation | 20 | Queue | Bloqueia |
| vision | 5 | Queue | Bloqueia |

## Metricas Criticas para Hardware Modesto

### CPU (2-4 cores)
- Whisper: Usar `small` ao inves de `medium`
- VAD: Energy-based (sem WebRTC se CPU limitada)
- Animation: Reduzir FPS para 8

### RAM (4-8 GB)
- Whisper small: ~500MB
- Coqui XTTS: ~2GB VRAM ou ~4GB RAM
- Piper: ~100MB (alternativa leve)

### GPU (RTX 3050 4GB / sem GPU)
- Whisper: float16 com GPU, int8 sem GPU
- Coqui: Precisa GPU. Sem GPU, usar Piper
- Ollama: Modelos 1-3B (tinyllama, phi3:mini)

## Configuracoes Recomendadas por Tier

### Tier 1: Minimo (4GB RAM, sem GPU)
```env
WHISPER_MODEL_SIZE=tiny
WHISPER_COMPUTE_TYPE=int8
TTS_ENGINE=piper
CHAT_PROVIDER=local
CHAT_LOCAL_MODEL=tinyllama
LUNA_ANIM_FPS=8
```

### Tier 2: Modesto (8GB RAM, GPU 4GB)
```env
WHISPER_MODEL_SIZE=small
WHISPER_COMPUTE_TYPE=float16
TTS_ENGINE=piper
CHAT_PROVIDER=local
CHAT_LOCAL_MODEL=phi3:mini
LUNA_ANIM_FPS=12
```

### Tier 3: Padrao (16GB RAM, GPU 8GB+)
```env
WHISPER_MODEL_SIZE=medium
WHISPER_COMPUTE_TYPE=float16
TTS_ENGINE=coqui
CHAT_PROVIDER=gemini
LUNA_ANIM_FPS=24
```
