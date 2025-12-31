# Architecture - Luna

**Data:** 2025-12-18
**Status:** Estavel

---

## TL;DR

Luna usa arquitetura multi-threaded com filas de mensagens para coordenar input de audio, transcricao, processamento de IA, animacao e TTS. O main.py e um orquestrador que delega toda logica para modulos em `src/`.

---

## Contexto

Luna foi projetada para processar multiplas entradas simultaneas (texto, voz, visao) sem bloquear a interface. Cada subsistema roda em thread dedicada e se comunica via filas thread-safe.

---

## Conteudo

### Diagrama de Arquitetura (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py (Orchestrator)                   │
│                     TemploDeLuna (Textual App)                   │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├─► Threading Manager (LunaThreadingManager)
                │   ├─► AudioCaptureThread ──► audio_queue
                │   ├─► TranscriptionThread ──► transcription_queue
                │   ├─► ProcessingThread ──► processing_queue
                │   ├─► CoordinatorThread ──► response_queue
                │   ├─► AnimationThread ──► animation_queue
                │   ├─► TTSThread ──► tts_queue
                │   └─► MonitorThread (health checks)
                │
                ├─► Consciencia (AI Logic)
                │   ├─► API Optimizer (rate limiting, cache)
                │   ├─► Consciencia Prompt (system instructions)
                │   └─► Gemini API (google-generativeai)
                │
                ├─► Boca (TTS Output)
                │   ├─► Coqui TTS (local, GPU/CPU)
                │   ├─► Piper TTS (local, CPU)
                │   └─► ElevenLabs TTS (cloud)
                │
                ├─► Ouvido (STT Input)
                │   ├─► PyAudio (capture)
                │   ├─► WebRTC VAD (voice detection)
                │   └─► Faster-Whisper (transcription)
                │
                ├─► Visao (Vision)
                │   ├─► OpenCV (camera)
                │   ├─► face_recognition (faces)
                │   ├─► imagehash (scene detection)
                │   └─► Gemini Vision API (description)
                │
                ├─► Session Manager (persistence)
                │   └─► /src/sessions/*.json
                │
                ├─► Memory Manager (embeddings)
                │   └─► /src/data_memory/
                │       ├─► user_profile.json
                │       ├─► faces/
                │       └─► events/
                │
                └─► UI (Textual Widgets)
                    ├─► BannerGlitchWidget (ASCII animation)
                    ├─► AudioVisualizer (waveform)
                    ├─► StatusDecryptWidget (status/emotion)
                    ├─► ChatMessage (conversation)
                    └─► GlitchButton (controls)
```

### Fluxo de Dados

**Entrada de Voz (Voice Input Flow):**
```
User fala
  ↓
AudioCaptureThread (captura chunks de audio)
  ↓ [audio_queue]
TranscriptionThread (detecta silencio via VAD)
  ↓ (acumula audio)
Faster-Whisper (transcreve quando usuario para)
  ↓ [transcription_queue]
CoordinatorThread (adiciona ao chat, envia para processamento)
  ↓ [processing_queue]
ProcessingThread (Consciencia gera resposta)
  ↓ [response_queue]
CoordinatorThread (exibe resposta no chat)
  ↓ [tts_queue]
TTSThread (sintetiza audio)
  ↓
Boca (reproduz audio)
```

**Entrada de Texto (Text Input Flow):**
```
User digita
  ↓
on_input_submitted (main.py)
  ↓
submit_interaction()
  ↓ [transcription_queue] (reutiliza fila)
ProcessingThread (mesma logica de voz)
  ↓ [response_queue]
CoordinatorThread
  ↓ [tts_queue]
TTSThread
  ↓
Boca
```

**Entrada de Visao (Vision Input Flow):**
```
User clica "Ver" (ou loop automatico)
  ↓
action_olhar()
  ↓
Visao.olhar_inteligente()
  ├─► Captura frame (OpenCV)
  ├─► Detecta faces (face_recognition)
  ├─► Calcula hash de cena (imagehash)
  ├─► Compara com ultimo frame
  └─► (se mudanca) Gemini Vision descreve cena
  ↓
submit_interaction("O que voce ve?", visual_context=descricao)
  ↓ [transcription_queue]
ProcessingThread
  ↓
...
```

### Componentes Principais

**1. main.py (Orquestrador)**
- Classe `TemploDeLuna` (Textual App)
- Inicializa subsistemas (Consciencia, Boca, Ouvido, Visao)
- Configura threading (setup_threading)
- Gerencia UI (compose, watch_em_chamada)
- Nao possui logica de negocio (apenas coordena)

**2. src/soul/consciencia.py**
- Interface com Gemini API
- Carrega personalidade de `src/assets/alma/alma_da_luna.txt`
- Gerencia historico de conversa
- Delega rate limiting para API Optimizer

**3. src/soul/boca.py**
- Abstrai multiplos TTS engines
- Suporta: Coqui (local), Piper (local), ElevenLabs (cloud)
- Ajusta velocidade/estabilidade baseado em emocao

**4. src/soul/voice_system.py (Ouvido)**
- Captura audio via PyAudio
- Detecta voz com WebRTC VAD
- Transcreve com Faster-Whisper (GPU/CPU)
- Configuravel via `config.py` (WHISPER_CONFIG, VAD_CONFIG)

**5. src/soul/visao.py**
- Captura frames via OpenCV
- Reconhece faces com face_recognition
- Detecta mudancas de cena com imagehash
- Descreve cena via Gemini Vision API
- Armazena rostos conhecidos em `/src/data_memory/faces/`

**6. src/soul/threading_manager.py**
- Classe `LunaThreadingManager`
- Registra e inicia todas as threads
- Filas thread-safe (Queue.Queue)
- Events para sincronizacao (listening_event, user_speaking_event)
- MonitorThread verifica saude das threads

**7. src/core/**
- `animation.py`: Carrega/exibe animacoes ASCII
- `session.py`: Salva/carrega historico de conversas
- `file_handler.py`: Anexa arquivos/diretorios para contexto

**8. src/ui/**
- Widgets customizados em Textual
- `banner.py`: BannerGlitchWidget (animacao de entrada)
- `audio_visualizer.py`: Waveform em tempo real
- `status_decrypt.py`: Efeito de "decriptacao" para status/emocao
- `glitch_button.py`: Botoes com efeito glitch

**9. config.py**
- Carrega variaveis do `.env`
- Define todas as configuracoes do sistema
- Sem logica, apenas constantes e validacoes

---

## Links Relacionados

- [QUICK_START.md](QUICK_START.md) - Como rodar Luna
- [TECH_STACK.md](TECH_STACK.md) - Tecnologias usadas
- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Estrutura de diretorios
- `/home/andrefarias/Desenvolvimento/Luna/src/soul/threading_manager.py` - Threading core
- `/home/andrefarias/Desenvolvimento/Luna/main.py` - Entry point
