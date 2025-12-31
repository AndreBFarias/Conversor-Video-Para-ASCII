# Folder Structure - Luna

**Data:** 2025-12-20
**Status:** Atualizado

---

## TL;DR

Luna segue arquitetura limpa: `main.py` orquestra, `config.py` configura, `src/` contem toda a logica. Modulos organizados por responsabilidade (luna/, ui/, core/, data_memory/, tools/).

---

## Contexto

A estrutura de pastas de Luna foi desenhada para separar codigo de dados, logica de UI, e facilitar navegacao. Segue principios de Clean Architecture e DDD (Domain-Driven Design).

---

## Conteudo

### Arvore Completa

```
/home/andrefarias/Desenvolvimento/Luna/
├── main.py                      # ORQUESTRADOR: Entry point, inicializa subsistemas
├── config.py                    # CONFIGURACOES: Carrega .env, define constantes
├── .env                         # Variaveis de ambiente (NAO commitado)
├── .env.example                 # Template de configuracao
├── requirements.txt             # Dependencias principais (venv)
├── requirements_tts.txt         # Dependencias TTS (venv_tts)
├── install.sh                   # Script de instalacao automatizada
├── uninstall.sh                 # Script de desinstalacao
├── run_luna.sh                  # Script de execucao (ativa venv, roda main.py)
├── run_onboarding.py            # Script de onboarding standalone
├── qa_luna.sh                   # Script de QA automatizado
├── README.md                    # Visao geral do projeto
├── CLAUDE.md                    # Protocolo de desenvolvimento (IA agents)
├── PROMPT_QA_LUNA.md            # Protocolo de QA
├── LICENSE                      # GPLv3
├── .gitignore                   # Ignora venv, logs, __pycache__, .env
│
├── dev-journey/                 # DOCUMENTACAO: Jornada de desenvolvimento
│   ├── README.md                # Indice da documentacao
│   ├── SUMMARY.md               # Sumario navegavel
│   ├── 01-getting-started/      # Primeiros passos
│   ├── 02-vision/               # Visao do projeto
│   ├── 03-changelog/            # Historico de versoes
│   ├── 04-implementation/       # Status de implementacao
│   ├── 05-future/               # Planejamento futuro
│   ├── 06-guides/               # Guias para contribuidores
│   ├── 07-metrics/              # Metricas e QA
│   ├── 08-prompts/              # Prompts de personalidade
│   └── templates/               # Templates de documentacao
│
├── Dev_log/                     # Logs de desenvolvimento (sessoes de trabalho)
│
├── venv/                        # Virtual env principal (IGNORADO no git)
├── venv_tts/                    # Virtual env TTS separada (IGNORADO no git)
│
└── src/                         # CODIGO FONTE: Toda a logica do projeto
    │
    ├── luna/                    # MODULOS CORE: Logica de IA, voz, visao
    │   ├── __init__.py
    │   ├── consciencia.py       # Interface com Gemini/Ollama, geracao de respostas
    │   ├── boca.py              # TTS (Coqui/Piper/ElevenLabs)
    │   ├── voice_system.py      # STT (Faster-Whisper, VAD)
    │   ├── visao.py             # Computer vision, face recognition
    │   ├── comunicacao.py       # OuvidoSussurrante (wrapper de voice_system)
    │   ├── memoria.py           # Sistema de memoria facial
    │   ├── metricas.py          # Metricas de performance
    │   ├── onboarding.py        # Processo de onboarding inicial
    │   ├── personalidade.py     # Configuracao de personalidade
    │   ├── threading_manager.py # Gerenciador de threads
    │   ├── audio_threads.py     # Threads de audio (capture, transcription, TTS)
    │   ├── processing_threads.py # Threads de processamento (IA, animation)
    │   ├── api_optimizer.py     # Otimizador de chamadas API
    │   ├── rate_limiter.py      # Rate limiting (RPM/quota)
    │   └── semantic_cache.py    # Cache semantico de prompts
    │
    ├── ui/                      # WIDGETS UI: Componentes Textual customizados
    │   ├── __init__.py
    │   ├── banner.py            # BannerGlitchWidget, ProgressiveStaticBackground
    │   ├── audio_visualizer.py  # AudioVisualizer (waveform em tempo real)
    │   ├── status_decrypt.py    # StatusDecryptWidget (efeito de decriptacao)
    │   ├── emotion_manager.py   # Gerenciador de emocoes/animacoes
    │   ├── glitch_button.py     # GlitchButton (botoes com efeito glitch)
    │   ├── widgets.py           # ChatMessage, CodeBlock
    │   ├── screens.py           # HistoryScreen, CanoneScreen
    │   ├── dashboard.py         # Dashboard de metricas
    │   ├── code_output_panel.py # Painel de output de codigo
    │   ├── context_menu.py      # Menu de contexto
    │   └── intro_animation.py   # Animacao de introducao
    │
    ├── core/                    # CORE UTILITIES: Logica compartilhada
    │   ├── __init__.py
    │   ├── animation.py         # AnimationController (carrega/exibe ASCII art)
    │   ├── session.py           # SessionManager (salva/carrega conversas)
    │   ├── file_handler.py      # FileAttachmentHandler (anexa arquivos/dirs)
    │   ├── router.py            # Roteamento de comandos
    │   ├── ollama_client.py     # Cliente Ollama sync
    │   ├── profiler.py          # Sistema de profiling v2
    │   ├── fallback_manager.py  # Gerenciador de fallbacks
    │   └── models/              # Wrappers de modelos LLM
    │       ├── __init__.py
    │       ├── dolphin.py       # Modelo Dolphin
    │       ├── minicpm_vision.py # Modelo MiniCPM Vision
    │       └── qwen_coder.py    # Modelo Qwen Coder
    │
    ├── data_memory/             # PERSISTENCIA: Memoria de longo prazo
    │   ├── __init__.py
    │   ├── memory_manager.py    # Gerenciador de memoria RAG
    │   ├── vector_store.py      # Armazenamento vetorial FAISS
    │   ├── embeddings.py        # Geracao de embeddings
    │   ├── cron_memory.py       # Script de purificacao de memorias
    │   ├── user_profile.json    # Perfil do usuario
    │   ├── faces/               # Embeddings de rostos conhecidos
    │   └── events/              # Eventos marcantes
    │
    ├── models/                  # MODELOS DE VOZ
    │   └── echoes/              # Referencias de voz para TTS
    │       ├── __init__.py
    │       ├── luna.py          # Configuracao de voz Luna
    │       └── coqui/           # Arquivos de referencia Coqui
    │
    ├── sessions/                # SESSOES: Historico de conversas
    │   ├── sessions_manifest.json
    │   └── session_<id>.json
    │
    ├── assets/                  # ASSETS: Recursos estaticos
    │   ├── animations/          # Animacoes ASCII (.txt)
    │   ├── css/                 # Estilos Textual
    │   │   └── templo_de_luna.css
    │   ├── voice/               # Audios de referencia para TTS
    │   ├── icons/               # Icones
    │   └── alma/                # Personalidade de Luna
    │       └── alma_da_luna.txt
    │
    ├── logs/                    # LOGS: Logs de execucao rotacionados
    │
    ├── tests/                   # TESTES: Testes automatizados
    │   ├── __init__.py
    │   └── test_providers.py    # Testes de providers
    │
    ├── temp/                    # TEMPORARIOS: Arquivos temporarios
    │   └── audio/
    │
    └── tools/                   # FERRAMENTAS: Scripts auxiliares
        ├── find_placeholders.py      # Encontra TODOs no codigo
        ├── diagnostico_luna.py       # Diagnostico do sistema
        ├── diagnostico_audio.py      # Diagnostico de audio
        ├── test_models.py            # Teste de modelos LLM
        ├── test_tts_isolado.py       # Teste de TTS isolado
        ├── test_memory.py            # Teste de memoria
        ├── test_threading_foundation.py
        ├── test_pyaudio_direct.py
        ├── test_sounddevice.py
        ├── tts_wrapper.py            # Wrapper TTS para venv isolado
        ├── chatterbox_wrapper.py     # Wrapper Chatterbox
        ├── find_working_device.py    # Encontra dispositivo audio
        ├── teste_gravacao_pipewire.py
        ├── verificar_instalacao.py   # Verifica instalacao
        └── verify_install.py
```

---

### Descricao por Diretorio

#### Raiz (`/`)

**main.py**
Orquestrador da aplicacao. Define classe `TemploDeLuna` (Textual App), inicializa subsistemas (Consciencia, Boca, Ouvido, Visao), configura threading, gerencia eventos de UI.

**config.py**
Carrega variaveis de ambiente do `.env` usando python-dotenv. Define todas as configuracoes como constantes (WHISPER_CONFIG, AUDIO_CONFIG, GEMINI_CONFIG, etc).

**install.sh**
Script bash que:
1. Verifica dependencias do sistema (python3, portaudio, ffmpeg, cmake)
2. Cria venv principal e venv_tts separada
3. Instala dependencias via pip
4. Compila/instala dlib (necessario para face_recognition)
5. Cria diretorios necessarios

---

#### `src/soul/` (Modulos Core)

**consciencia.py**
Interface com Google Gemini/Ollama. Carrega personalidade de `alma_da_luna.txt`, gerencia historico de conversa, processa comandos especiais, delega rate limiting para API Optimizer.

**boca.py**
Abstrai TTS engines. Suporta Coqui (local), Piper (local), ElevenLabs (cloud). Ajusta velocidade/estabilidade baseado em emocao.

**voice_system.py**
Sistema de STT. Captura audio via PyAudio, detecta voz com WebRTC VAD, transcreve com Faster-Whisper.

**visao.py**
Computer vision. Captura frames via OpenCV, detecta faces com face_recognition, descreve cena via Gemini Vision.

**threading_manager.py**
Gerencia 8 threads: audio_capture, transcription, processing, coordinator, animation, tts, tts_playback, monitor.

---

#### `src/core/` (Core Utilities)

**animation.py**
Carrega animacoes ASCII de `assets/animations/`, exibe frame a frame. 12 emocoes disponiveis.

**profiler.py**
Sistema de profiling v2 com InteractionTrace, thresholds por estagio e recomendacoes automaticas.

**ollama_client.py**
Cliente sincrono para Ollama API.

---

#### `src/tools/` (Ferramentas)

Scripts auxiliares para diagnostico, teste e manutencao do sistema.

---

## Links Relacionados

- [QUICK_START.md](QUICK_START.md) - Como rodar Luna
- [ARCHITECTURE.md](ARCHITECTURE.md) - Diagrama de arquitetura
- [TECH_STACK.md](TECH_STACK.md) - Tecnologias usadas
