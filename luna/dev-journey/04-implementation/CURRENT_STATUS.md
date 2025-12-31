# Status Atual do Projeto Luna

**Data:** 2025-12-29
**Branch:** main
**Versao:** 3.8.0

---

## TL;DR

Luna v3.8.0 operacional com ETAPAs 01-15 concluidas. Novo sistema de providers UniversalLLM com fallback automatico, type hints completos, constantes centralizadas, memory tiers, streaming de respostas, AI-friendliness (DEPENDENCY_MAP, docstrings) e **Web Dashboard com FastAPI + WebSockets**. 1468 testes passando.

---

## Alteracoes Recentes (2025-12-29)

### ETAPAs 01-06: Refatoracao Base
1. **Silent Exceptions** - ~70 ocorrencias de `except: pass` corrigidas com logging
2. **Memory Locks** - Hierarquia de excecoes (MemoryError, MemoryLoadError, etc)
3. **Interface de Memoria** - `ISmartMemory` abstrata em `src/core/interfaces.py`
4. **Logging Centralizado** - `get_logger()` em todos os modulos
5. **Separacao Consciencia** - Extraido `response_parser.py`, `context_builder.py`
6. **Personality Anchor** - Sistema de ancora de personalidade

### ETAPAs 07-12: Provider System
1. **UniversalLLM** - `src/soul/providers/` com fallback Gemini->Ollama
2. **Type Hints** - 23 arquivos criticos tipados
3. **Module Indices** - `__all__` em todos os `__init__.py`
4. **Constants** - `src/core/constants.py` (TimeoutConstants, etc)
5. **Memory Tiers** - ShortTermMemory + MemoryTierManager
6. **Streaming** - `ResponsePipeline.process_stream()` completo

### ETAPAs 13-15: AI-Friendliness e Finalizacao
1. **DEPENDENCY_MAP.md** - Mapa de dependencias entre modulos
2. **Docstrings** - 9 arquivos principais documentados
3. **Web Dashboard** - `src/web/` com FastAPI + WebSockets

---

## Alteracoes Anteriores (2025-12-24 - Sessao 2)

### Daemon Mode / System Tray
1. **SystemTrayManager** - `src/core/tray.py` usando pystray com backend Ayatana
2. **DaemonController** - `src/core/daemon.py` gerencia show/hide/quit/toggle voice
3. **Icone personalizado** - `src/assets/icons/luna_tray.png`
4. **Configuracao via .env** - `DAEMON_MODE`, `START_MINIMIZED`, `MINIMIZE_TO_TRAY`

### Wake Word Detection
1. **WakeWordDetector** - `src/soul/wake_word.py` usando Whisper+VAD
2. **Padroes suportados** - nome da entidade ativa + variantes
3. **Cooldown configuravel** - `WAKE_WORD_COOLDOWN` (default 2s)
4. **Ativacao** - Via daemon (botao direito em Voz)

### Voice Profile (Speaker ID)
1. **VoiceProfile** - `src/soul/voice_profile.py` via Resemblyzer embeddings
2. **Threshold configuravel** - `VOICE_SIMILARITY_THRESHOLD` (default 0.75)

### Correcoes de Infraestrutura
1. **install.sh** - Migracao para Ayatana AppIndicator (compatibilidade Pop!_OS)
2. **requirements.txt** - Adicionado `PyGObject>=3.42.0,<3.48.0`
3. **config.py** - Defaults unificados em `reload_config()`

---

## Alteracoes Anteriores (2025-12-24 - Sessao 1)

### Simetria Visual Startup/Shutdown
1. **Startup Cinematico** - Tela inicia preenchida de static, fade_out revela conteudo (efeito "TV sintonizando")
2. **Shutdown Cinematico** - Fade_in cobre tela de static (efeito "TV desligando")
3. **Mesma paleta visual** - Caracteres roxos (accent color) em ambas direcoes

### Sistema de Interrupcao TTS
1. **Funcao `_interrupt_luna()`** - Para TTS de forma consistente em qualquer ponto
2. **Limpeza de Filas** - `tts_queue` e `tts_playback_queue` esvaziadas ao interromper
3. **Sincronizacao de Eventos** - `is_speaking` sincronizado com `luna_speaking_event`
4. **Lock em `gerar_audio()`** - Protege geracao de audio contra race conditions

### Deteccao de Genero por Nome
1. **Novo modulo** - `src/core/gender_detector.py`
2. **~130 nomes brasileiros** - 70 masculinos, 60 femininos
3. **Heuristicas** - Terminacoes (a=F, o/os/or=M) como fallback
4. **Tratamentos personalizados** - eleito/eleita, meu/minha, senhor/senhora

### Portabilidade
1. **run_luna.sh** - Detecta versao Python dinamicamente
2. **Sem hardcoded paths** - Funciona em Python 3.10, 3.11, 3.12+

---

## Alteracoes Anteriores (2025-12-22)

### Sistema de Transicoes TV Static
1. **Startup** - TV static nas 3 areas (banner, status, animacao) durante boot
2. **Shutdown** - TV static apenas na area de animacao ao encerrar
3. **Processamento** - Banner e animacao ocultos, TV static aparece
4. **Entre Emocoes** - Transicao TV static antes de voltar ao `observando`
5. **Botao Ver** - Animacao piscando fullscreen + TV static ao final
6. **Botao Voz** - TV static apenas no banner ao desativar

### Funcoes Novas em banner.py
- `run_startup_static()` - Boot da aplicacao (com preenchimento inicial)
- `run_shutdown_sequence()` - Encerramento (fade_in + preenchimento final)
- `run_processing_static()` - Durante processamento
- `run_emotion_transition()` - Entre animacoes
- `run_banner_only_static()` - Apenas banner
- `run_fullscreen_piscando()` - Visao fullscreen

### Gerenciamento de VRAM (v3.1.0)
1. **Ollama keep_alive=30s** - Modelos descarregados apos 30s
2. **Whisper small** - Reduzido de medium para small (~1.5GB economia)
3. **Embeddings em CPU** - Nao compete por VRAM
4. **Modelo moondream** - Substituiu minicpm-v para visao

---

## Alteracoes Anteriores (2025-12-21)

### Correcoes Criticas
1. **Audio Device Corrigido** - AUDIO_DEVICE_ID agora usa hardware direto (ALC287) em vez de pulse
2. **Sample Rate Nativo** - AUDIO_SAMPLE_RATE alterado para 48000Hz (rate nativo do microfone)
3. **VAD Threshold Ajustado** - VAD_ENERGY_THRESHOLD reduzido para 2000 (compativel com RMS real)
4. **Warmup de Audio** - Primeiros 50 frames descartados para evitar falsos positivos do DC offset

### Limpeza de Modelos
1. **Removidos tinyllama e gemma2:2b** - Inadequados para o projeto (censura/instabilidade)
2. **install.sh atualizado** - Lista de modelos Ollama reduzida para apenas os essenciais

### Documentacao
1. **AUDIO_SETUP.md** - Guia completo de configuracao de audio (novo)
2. **Session Summary 2024-12-21** - Documentacao das descobertas

---

## Alteracoes Anteriores (2025-12-19)

### Correcoes Criticas
1. **TTSPlaybackThread registrada** - Thread de playback agora esta corretamente registrada no `setup_threading()`
2. **Profiler v2** - Sistema completo de rastreamento com InteractionTrace, thresholds por estagio e recomendacoes automaticas

### Melhorias de UI
1. **Canone harmonizado** - CSS corrigido conforme STYLE_GUIDE (cores solidas, bordas consistentes)
2. **GlitchButton no Canone** - Botoes agora usam GlitchButton igual a main

### Documentacao
1. **PERFORMANCE_OPTIMIZATION.md** - Documentacao das otimizacoes
2. **Script de diagnostico** - `src/tools/diagnostico_luna.py` para testar modulos

---

## Features Funcionais

### 1. Interface TUI (Terminal User Interface)
- Framework: Textual
- Tema: Dark Dracula (conforme STYLE_GUIDE)
- Componentes ativos:
  - Chat com historico scrollavel
  - Input de texto com suporte a Rich markup
  - Botoes de acao com GlitchButton (Confissao, Relicario, Custodia, Ver, Canone, Requiem)
  - Banner ASCII animado com emocoes
  - Indicadores de status em tempo real
  - Canone (configuracoes) com 5 abas

### 2. Sistema de Threading Paralelo
- ThreadPoolExecutor configurado
- 9 threads registradas:
  - `audio_capture` - Captura de microfone (PyAudio)
  - `transcription` - Whisper STT + VAD
  - `processing` - LLM (Gemini/Ollama)
  - `coordinator` - UI updates
  - `animation` - Frames ASCII
  - `tts` - Geracao de audio
  - `tts_playback` - Playback de audio
  - `monitor` - Health check
  - `wake_word` - Deteccao de wake word (Whisper+VAD)
- Arquivos envolvidos:
  - `src/soul/threading_manager.py`
  - `src/soul/audio_threads.py`
  - `src/soul/processing_threads.py`
  - `src/soul/wake_word.py`

### 3. Consciencia (Integracao LLM)
- Providers: Gemini (cloud) ou Ollama (local)
- Modelo Gemini: gemini-2.0-flash
- Modelo Ollama: dolphin-mistral (fallback)
- Rate limiting inteligente
- Cache semantico funcional (threshold 0.85)
- Deduplicacao de requests
- API Optimizer delegando chamadas corretamente
- Arquivo: `src/soul/consciencia.py`

### 4. Sistema de Voz
- Speech-to-Text: Faster Whisper (medium model, CUDA)
- Text-to-Speech: Coqui XTTS ou Chatterbox
- Deteccao de silencio VAD (Voice Activity Detection)
- Parametros de Audio:
  - AUDIO_DEVICE_ID: 5 (hardware ALC287 direto)
  - AUDIO_SAMPLE_RATE: 48000Hz (rate nativo)
  - Warmup: 50 frames descartados na inicializacao
- Parametros VAD otimizados:
  - ENERGY_THRESHOLD: 2000
  - SILENCE_FRAME_LIMIT: 12
  - FRAME_BUFFER_SIZE: 6
- Arquivos:
  - `src/soul/voice_system.py`
  - `src/soul/boca.py`
  - `src/soul/audio_threads.py`

### 5. Visao Computacional
- Integracao com webcam via OpenCV
- Envio de imagens para Gemini Vision
- Reconhecimento facial com embeddings
- Arquivo: `src/soul/visao.py`

### 6. Memoria Vetorial
- Embeddings via Gemini ou local
- Vector store com FAISS
- Memoria de longo prazo funcional
- RAG (Retrieval Augmented Generation)
- Arquivos:
  - `src/data_memory/memory_manager.py`
  - `src/data_memory/vector_store.py`
  - `src/data_memory/embeddings.py`

### 7. Sistema de Profiling (v2)
- InteractionTrace: rastreia cada interacao do inicio ao fim
- Thresholds por estagio com alertas automaticos
- Recomendacoes de otimizacao
- Timeline visual de latencia
- Arquivo: `src/core/profiler.py`

### 8. Instalacao e Deploy
- `install.sh`: setup automatizado
- `uninstall.sh`: remocao limpa
- Desktop entry gerado automaticamente
- Icone para dockbar

---

## Estado dos Modulos

| Modulo | Status | Observacoes |
|--------|--------|-------------|
| `consciencia.py` | Funcional | Rate limiting OK, fallback Ollama |
| `threading_manager.py` | Funcional | 8 threads registradas |
| `audio_threads.py` | Funcional | Latencia otimizada, playback separado |
| `processing_threads.py` | Funcional | Sem deadlocks, profiler integrado |
| `voice_system.py` | Funcional | VAD operacional |
| `boca.py` | Funcional | Sanitizacao de tags OK |
| `visao.py` | Funcional | Webcam integrada |
| `memory_manager.py` | Funcional | Vector store estavel |
| `semantic_cache.py` | Funcional | Threshold 0.85 |
| `rate_limiter.py` | Funcional | Quota tracking OK |
| `api_optimizer.py` | Funcional | Delegacao corrigida |
| `profiler.py` | Funcional | v2 com diagnostico |
| `screens.py` | Funcional | Canone com GlitchButton |
| `wake_word.py` | Funcional | Whisper+VAD, daemon |
| `voice_profile.py` | Funcional | Resemblyzer embeddings |
| `daemon.py` | Funcional | Show/hide/quit/toggle |
| `tray.py` | Funcional | pystray + Ayatana backend |

---

## Resultado do Diagnostico (2025-12-19)

```
TOTAL: 9 OK | 1 FALHA (quota Gemini)

[OK] Config           - CHAT_PROVIDER: local, TTS: coqui
[OK] ThreadingManager - 8 filas configuradas
[OK] Profiler         - InteractionTrace funcionando
[OK] AudioDevices     - 11 dispositivos encontrados
[OK] VADConfig        - Threshold: 6000, Limit: 15
[OK] WhisperLoad      - Modelo medium (CUDA) em 3.55s
[OK] TTSEngine        - Coqui XTTS (CUDA)
[OK] AnimationFrames  - 12 emocoes, 2281 frames
[OK] OllamaConnection - 3 modelos disponiveis
[!!] GeminiConnection - Quota esgotada (esperado)
```

---

## Configuracao Atual

### Ambiente
- Python: 3.10+
- OS: Pop!_OS (Linux)
- Shell: zsh
- GPU: RTX 3050 (CUDA ativo para Whisper e TTS)

### Providers Ativos
- Chat: Ollama (dolphin-mistral) - local
- Vision: Gemini (gemini-1.5-flash)
- TTS: Coqui XTTS (local, CUDA)
- STT: Faster Whisper (medium, CUDA)

### Config Files
- `config.py`
- `.env`
- `src/assets/alma/alma_da_luna.txt`

---

## Links Relacionados

- [COMPLETED_FEATURES.md](./COMPLETED_FEATURES.md)
- [IN_PROGRESS.md](./IN_PROGRESS.md)
- [ARCHITECTURE_DNA.md](./ARCHITECTURE_DNA.md)
- [PERFORMANCE_OPTIMIZATION.md](../07-metrics/PERFORMANCE_OPTIMIZATION.md)
- [STYLE_GUIDE.md](../01-getting-started/STYLE_GUIDE.md)
