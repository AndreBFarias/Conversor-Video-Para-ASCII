# Gemini 2.5 Live - Native Audio Streaming

## Visao Geral

O modulo LunaLiveSession implementa streaming de audio bidirecional usando a
Multimodal Live API do Gemini 2.5 Flash, permitindo conversas em tempo real
com TTS nativo do modelo.

## Arquitetura

```
src/soul/live_session.py
│
├── LunaLiveSession (classe principal)
│   ├── start()            # Inicia sessao
│   ├── stop()             # Para sessao
│   ├── send_audio()       # Envia audio do microfone
│   ├── send_text()        # Envia texto (modo hibrido)
│   └── interrupt()        # Barge-in (interrupcao)
│
├── LiveAudioBridge
│   └── Conecta AudioCaptureThread ao Gemini Live
│
└── Callbacks
    ├── on_audio_response  # Audio gerado pelo Gemini
    ├── on_text_response   # Texto da resposta
    └── on_interrupt       # Quando usuario interrompe
```

## Como Funciona

### 1. Streaming Bidirecional (#1)

```
[Microfone] → [AudioCaptureThread] → [LiveAudioBridge] → [Gemini 2.5 Flash]
                                                               ↓
[Alto-falante] ← [Native TTS] ← [Gemini Response] ←───────────┘
```

### 2. Native Audio (#2)

O Gemini 2.5 Flash gera audio diretamente (TTS nativo), sem usar boca.py:

```python
if hasattr(part, 'inline_data') and 'audio' in part.inline_data.mime_type:
    audio_bytes = base64.b64decode(part.inline_data.data)
    self.on_audio_response(audio_bytes)
```

### 3. Barge-in (#8)

Quando o usuario comeca a falar enquanto Luna responde:

```python
def interrupt(self):
    self._interrupted = True
    self._is_speaking = False
    if self.on_interrupt:
        self.on_interrupt()
```

## Uso

### Iniciar Sessao

```python
from src.soul.live_session import create_live_session
import config

def on_text(text: str):
    print(f"Luna disse: {text}")

def on_audio(audio: bytes):
    # Reproduzir audio nativo do Gemini
    play_audio(audio)

def on_interrupt():
    # Parar reproducao atual
    stop_audio()

session = create_live_session(
    api_key=config.GOOGLE_API_KEY,
    on_text_response=on_text,
    on_audio_response=on_audio,
    on_interrupt=on_interrupt
)

session.start()
```

### Enviar Audio

```python
# Do AudioCaptureThread
audio_chunk = audio_queue.get()
session.send_audio(audio_chunk, sample_rate=16000)
```

### Usar Bridge

```python
from src.soul.live_session import LiveAudioBridge

bridge = LiveAudioBridge(
    live_session=session,
    audio_queue=threading_manager.audio_queue,
    sample_rate=16000
)

bridge.start()

# Notificar quando usuario esta falando (para barge-in)
bridge.notify_user_speaking(True)
```

## Configuracao

No `.env`:

```bash
# Habilitar Gemini Live
GEMINI_LIVE_ENABLED=true

# Modelo (default: gemini-2.0-flash-exp)
GEMINI_LIVE_MODEL=gemini-2.0-flash-exp

# Voz do TTS nativo
GEMINI_LIVE_VOICE=Aoede

# Taxa de amostragem
GEMINI_LIVE_SAMPLE_RATE=16000
```

No `config.py`:

```python
GEMINI_LIVE_CONFIG = {
    "ENABLED": os.getenv("GEMINI_LIVE_ENABLED", "false").lower() == "true",
    "MODEL": os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp"),
    "VOICE_NAME": os.getenv("GEMINI_LIVE_VOICE", "Aoede"),
    "SAMPLE_RATE": int(os.getenv("GEMINI_LIVE_SAMPLE_RATE", "16000")),
}
```

## Vozes Disponiveis

| Nome | Descricao |
|------|-----------|
| Aoede | Feminina, equilibrada |
| Charon | Masculina, seria |
| Fenrir | Masculina, grave |
| Kore | Feminina, suave |
| Puck | Feminina, animada |

## Integracao com Sistema Existente

### Modo Hibrido

O sistema pode alternar entre:
- **Modo Local**: Whisper STT + Ollama/Gemini + Coqui TTS
- **Modo Gemini Live**: Audio direto para Gemini 2.5 Flash

```python
if config.GEMINI_LIVE_CONFIG["ENABLED"]:
    # Usar Gemini Live (audio nativo)
    session = get_live_session()
    session.send_audio(audio_chunk)
else:
    # Usar pipeline tradicional
    whisper_queue.put(audio_chunk)
```

### Compatibilidade com AudioCaptureThread

O `LiveAudioBridge` conecta o sistema de captura existente:

```python
from src.soul.audio_threads import AudioCaptureThread
from src.soul.live_session import LiveAudioBridge, create_live_session

# Criar sessao Live
session = create_live_session(api_key=config.GOOGLE_API_KEY)

# Criar bridge
bridge = LiveAudioBridge(
    live_session=session,
    audio_queue=threading_manager.audio_capture_queue
)

# Iniciar ambos
session.start()
bridge.start()
```

## Marcadores no Codigo

| Marcador | Funcao |
|----------|--------|
| #1 | Streaming de audio para Gemini |
| #2 | Native Audio (TTS nativo) |
| #3 | Inicializa cliente Gemini |
| #4 | Inicia sessao de streaming |
| #5 | Para sessao de streaming |
| #6 | Envia chunk de audio |
| #7 | Envia texto (modo hibrido) |
| #8 | Barge-in (interrupcao) |
| #9 | Loop de recepcao |
| #10 | Obtem resposta da fila |
| #11 | Bridge com AudioCaptureThread |
| #12 | Notifica usuario falando |
| #13 | Cria sessao singleton |
| #14 | NativeAudioPlayer (playback automatico) |
| #15 | Enfileira audio para reproducao |
| #16 | Para reproducao (barge-in) |

## NativeAudioPlayer (v4.2)

A classe `NativeAudioPlayer` gerencia o playback automatico do audio nativo:

```python
# Criacao com playback automatico (padrao)
session = create_live_session(
    api_key=config.GOOGLE_API_KEY,
    enable_native_playback=True,     # Habilita playback automatico
    native_audio_sample_rate=24000   # Taxa do Gemini (24kHz)
)

# Sem playback automatico (manual via callback)
session = create_live_session(
    api_key=config.GOOGLE_API_KEY,
    enable_native_playback=False,
    on_audio_response=my_custom_player
)
```

Backends suportados (em ordem de prioridade):
1. **pygame.mixer** - Recomendado, baixa latencia
2. **sounddevice** - Alternativa se pygame nao disponivel

## Requisitos

```bash
pip install google-genai>=0.4.0
```

## Limitacoes

1. Requer conexao com internet estavel
2. Latencia depende da rede (~200-500ms)
3. TTS nativo nao e customizavel como Coqui
4. Cota de API do Gemini se aplica
