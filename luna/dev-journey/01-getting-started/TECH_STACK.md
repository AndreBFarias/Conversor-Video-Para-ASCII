# Tech Stack - Luna

**Data:** 2025-12-18
**Status:** Estavel

---

## TL;DR

Luna e construida em Python com Textual para TUI, Google Gemini para IA, Faster-Whisper para STT, Coqui/Piper/ElevenLabs para TTS, e OpenCV/face_recognition para visao.

---

## Contexto

A stack tecnologica de Luna foi escolhida para balancear performance, facilidade de deployment e capacidades multimodais. Todos os componentes core rodam localmente exceto a IA (Gemini API) e TTS cloud (ElevenLabs, opcional).

---

## Conteudo

### Tabela de Tecnologias

| Categoria | Tecnologia | Versao | Proposito | Local/Cloud |
|-----------|-----------|--------|-----------|-------------|
| **Framework UI** | Textual | 0.76.0+ | Interface TUI (terminal) | Local |
| **Rendering** | Rich | 13.0.0+ | Formatacao de texto, syntax highlighting | Local |
| **IA/LLM** | Google Gemini | API v1.5-pro | Conversacao, raciocinio, vision | Cloud |
| **STT** | Faster-Whisper | 1.1.0+ | Speech-to-Text (transcricao) | Local (GPU/CPU) |
| **TTS (Engine 1)** | Coqui TTS | (venv separada) | Text-to-Speech local (XTTS v2) | Local (GPU/CPU) |
| **TTS (Engine 2)** | Piper TTS | (binario) | Text-to-Speech local (ONNX) | Local (CPU) |
| **TTS (Engine 3)** | ElevenLabs | API v1.0+ | Text-to-Speech cloud (opcional) | Cloud |
| **VAD** | WebRTC VAD | 2.0.10+ | Voice Activity Detection | Local |
| **Audio I/O** | PyAudio | 0.2.14+ | Captura de microfone | Local |
| **Audio Processing** | sounddevice, soundfile, scipy, numpy | - | Processamento de sinais | Local |
| **Computer Vision** | OpenCV | 4.8.0+ | Captura de camera, processamento de imagem | Local |
| **Face Recognition** | face_recognition | 1.3.0+ | Reconhecimento facial (wrapper de dlib) | Local (CPU) |
| **Image Hashing** | imagehash | 4.3.1+ | Deteccao de mudancas de cena | Local |
| **Embeddings** | sentence-transformers | 2.2.0+ | Memoria semantica | Local (GPU/CPU) |
| **ML Backend** | PyTorch | 2.0.0+ | Backend para Whisper, embeddings, TTS | Local (GPU/CPU) |
| **Config** | python-dotenv | 1.0.0+ | Carregamento de .env | Local |
| **Utilities** | requests, httpx, pyperclip | - | HTTP, clipboard | Local |

### Detalhamento por Subsistema

#### 1. Interface (TUI)

**Framework:** Textual
**Por que:** Textual e um framework moderno para TUI em Python, inspirado em React. Oferece widgets reativos, CSS-like styling, e excelente performance. Permite construir interfaces complexas sem sair do terminal.

**Alternativas consideradas:**
- urwid (muito verboso)
- blessed (sem sistema de widgets)
- curses (baixo nivel demais)

**Rich:** Usado para syntax highlighting de codigo, formatacao de texto e renderizacao de markdown no chat.

---

#### 2. IA/LLM

**API:** Google Gemini (gemini-1.5-pro)
**Por que:** Multimodal (texto + visao), contexto grande (2M tokens), pricing competitivo, baixa latencia, SDK oficial Python.

**Recursos usados:**
- Conversacao com historico
- Vision API (descreve imagens da webcam)
- System instructions (personalidade via alma_da_luna.txt)

**Otimizacoes:**
- Rate limiter customizado (rate_limiter.py)
- Cache semantico (semantic_cache.py)
- API Optimizer (api_optimizer.py) coordena ambos

---

#### 3. Speech-to-Text (STT)

**Engine:** Faster-Whisper (wrapper otimizado do Whisper da OpenAI)
**Por que:** Roda localmente (privacidade), suporta GPU (CUDA) e CPU, modelos multilinguais, alta acuracia.

**Modelo padrao:** medium (melhor balanco precisao/velocidade)
**Compute type:** float16 (GPU) ou int8 (CPU)

**VAD:** WebRTC VAD detecta quando usuario para de falar, triggando transcricao.

**Configuracao:** WHISPER_CONFIG e VAD_CONFIG em `config.py`

---

#### 4. Text-to-Speech (TTS)

Luna suporta 3 engines (configuravel via `TTS_ENGINE` no .env):

**A) Coqui TTS (padrao)**
- Local, GPU/CPU
- Modelo: XTTS v2 (multilingual, clonagem de voz)
- Voz de referencia: `src/assets/voice/luna_reference.wav`
- Instalacao: venv separada (requirements_tts.txt) devido a conflito de dependencias

**B) Piper TTS**
- Local, CPU only
- Modelo: pt_BR-faber-medium.onnx
- Mais rapido que Coqui, menos expressivo
- Binario standalone em `src/models/piper/`

**C) ElevenLabs**
- Cloud, requer API key
- Alta qualidade, expressividade natural
- Usado quando qualidade > latencia

**Escolha:** Definido por `TTS_ENGINE` no .env (coqui/piper/elevenlabs)

---

#### 5. Visao Computacional

**OpenCV:** Captura frames da webcam, preprocessamento
**face_recognition:** Detecta e reconhece rostos (usa dlib internamente)
**imagehash:** Calcula hash perceptual de frames para detectar mudancas de cena
**Gemini Vision API:** Descreve cena em linguagem natural quando mudanca detectada

**Fluxo:**
1. Captura frame (OpenCV)
2. Detecta faces (face_recognition)
3. Compara embeddings com rostos conhecidos
4. Calcula hash da cena (imagehash)
5. Se mudanca > threshold: Gemini Vision descreve
6. Luna comenta a mudanca

**Armazenamento:** Rostos conhecidos em `/src/data_memory/faces/pessoa.pkl`

---

#### 6. Memoria e Embeddings

**sentence-transformers:** Gera embeddings semanticos de texto/rostos
**Modelo:** all-MiniLM-L6-v2 (padrao, multilingual)
**Uso:**
- Cache semantico (similaridade de prompts)
- Reconhecimento de rostos (embeddings faciais)
- Memoria de eventos (futura implementacao)

**PyTorch:** Backend para modelos de ML (Whisper, embeddings, Coqui TTS)

---

#### 7. Threading e Concorrencia

**Sistema:** Threading nativo do Python (threading.Thread)
**Sincronizacao:** queue.Queue (thread-safe), threading.Event
**Gerenciamento:** LunaThreadingManager (threading_manager.py)

**Threads ativas:**
- AudioCaptureThread (captura continua)
- TranscriptionThread (processa audio)
- ProcessingThread (Consciencia)
- CoordinatorThread (UI updates)
- AnimationThread (ASCII animations)
- TTSThread (sintese de fala)
- MonitorThread (health checks)

**Por que nao asyncio:** Audio I/O (PyAudio) e blocking, TTS local e CPU-bound. Threading e mais adequado.

---

#### 8. Configuracao

**python-dotenv:** Carrega variaveis de ambiente do .env
**config.py:** Centraliza todas as configuracoes, valida API keys

**Arquivos de config:**
- `.env` (ignorado no git, criado pelo usuario)
- `.env.example` (template commitado)
- `config.py` (carrega e valida)

---

### Dependencias Criticas

**Conflito de Dependencias (Coqui vs sentence-transformers):**
- sentence-transformers requer transformers >= 4.41.0
- coqui-tts requer transformers < 4.41.0
- **Solucao:** venvs separadas (venv/ e venv_tts/)

**Instalacao de dlib (face_recognition):**
- Requer cmake, compiladores C++
- `install.sh` automatiza instalacao via apt/brew

---

### Hardware Recomendado

**Minimo:**
- CPU: 4 cores
- RAM: 8GB
- Disco: 5GB (modelos Whisper + TTS)

**Recomendado:**
- CPU: 8+ cores
- RAM: 16GB
- GPU: NVIDIA com CUDA (RTX 3050+)
- Disco: SSD

**GPU acelera:**
- Faster-Whisper (4x mais rapido)
- Coqui TTS (2x mais rapido)
- sentence-transformers embeddings

---

## Links Relacionados

- [QUICK_START.md](QUICK_START.md) - Instalacao e uso
- [ARCHITECTURE.md](ARCHITECTURE.md) - Diagrama de arquitetura
- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Estrutura de diretorios
- `/home/andrefarias/Desenvolvimento/Luna/requirements.txt` - Dependencias principais
- `/home/andrefarias/Desenvolvimento/Luna/requirements_tts.txt` - Dependencias TTS
- `/home/andrefarias/Desenvolvimento/Luna/config.py` - Configuracoes centralizadas
