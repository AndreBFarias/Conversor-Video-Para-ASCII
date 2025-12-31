# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Em Desenvolvimento
- Busca em historico de conversas
- Padronizacao completa dos DOSSIEs

## [3.8.0] - 2025-12-29

### Adicionado
- **UniversalLLM Provider System** (ETAPA 07): Abstração unificada de providers LLM
  - `src/soul/providers/` - Modulo de providers (base, gemini, ollama, universal)
  - Fallback automatico entre Gemini e Ollama
  - Circuit breaker para providers instáveis
  - Streaming token-by-token via `generate_stream()`
- **Type Hints Completos** (ETAPA 08): Tipagem em 23 arquivos criticos
  - Todos os parametros e retornos tipados
  - Uso de `TYPE_CHECKING` para evitar imports circulares
- **Indices de Modulos** (ETAPA 09): `__all__` em todos os `__init__.py`
  - Exports explicitos para cada modulo
  - Facilita navegacao e autocomplete
- **Constantes Centralizadas** (ETAPA 10): `src/core/constants.py`
  - `TimeoutConstants`, `MemoryConstants`, `AnimationConstants`
  - Substituido magic numbers em 8 arquivos
- **Memory Tiers** (ETAPA 11): Sistema de memoria em camadas
  - `ShortTermMemory` - Buffer de 5 minutos com TTL
  - `MemoryTierManager` - Orquestracao de promocao entre tiers
  - Promocao automatica baseada em importancia e acessos
- **Streaming Response** (ETAPA 12): Streaming de respostas LLM
  - `ResponsePipeline.process_stream()` completo
  - Providers com `supports_streaming()` e `generate_stream()`
  - Fallback chain para streaming
- **AI-Friendliness** (ETAPA 13): Melhorias de navegabilidade para IAs
  - `dev-journey/04-implementation/DEPENDENCY_MAP.md` - Mapa de dependencias
  - Docstrings em 9 arquivos principais
  - Comentarios de secao em `consciencia.py` (1548 linhas)
- **Web Dashboard** (ETAPA 14): Interface web com FastAPI
  - `src/web/` - Modulo de dashboard web
  - 8 endpoints REST (status, entities, metrics, chat, etc)
  - WebSocket para streaming de chat
  - Frontend HTML/JS com theme dark

### Alterado
- **requirements.txt**: Adicionadas dependencias web (fastapi, uvicorn, jinja2)
- **Testes**: 1280+ testes no projeto (11 novos para web, 27 para memory tiers, 9 para streaming)

### Corrigido
- **Excecoes silenciadas** (#33): ~70 ocorrencias de `except: pass` substituidas por logging
  - src/soul/ (10 arquivos), src/core/ (4), src/app/ (4), src/ui/ (6), outros (5)
  - Adicionado hook pre-commit `no-silent-except` para prevenir novas ocorrencias
  - Criado teste `test_exception_handling.py` para verificacao automatica
- **Memory locks** (#34): Tratamento de excecoes em locks do SmartMemory
  - Criada hierarquia de excecoes: `MemoryError`, `MemoryLoadError`, `MemoryWriteError`, `MemoryLockError`
  - Refatorados `_ensure_loaded()`, `get_entity_smart_memory()`, `_get_shared_embedding_gen()`
  - Adicionado hook pre-commit `no-manual-lock-acquire` para detectar `.acquire()` manual
  - Criado `test_memory_locks.py` com 9 testes de concorrencia

### Alterado
- **scripts/ migrado para src/tools/**: 15 scripts shell movidos para centralizar ferramentas
- **verify_install.py**: Removida entrada duplicada "logs" que criava pasta na raiz

### Removido
- Pasta `scripts/` da raiz (conteudo migrado)
- Pasta `logs/` da raiz (logs ficam em `src/logs/`)

## [3.7.2] - 2025-12-29

### Adicionado
- **DownloadModal aprimorado**: Tela de download de modelos Ollama
  - Contador sequencial "1/3" para downloads multiplos
  - Limpeza de codigos ANSI do output do Ollama
  - Callback `update_model()` para atualizar modal sem fechar
- **Fila de downloads**: Sistema de download sequencial de modelos
  - Verifica quais modelos precisam ser baixados antes de salvar configuracoes
  - Processa downloads um a um com feedback visual
  - Trata erros e limpa fila em caso de falha
- **Correcao de genero no status**: Sistema de inflexao gramatical
  - `GENDER_FORMS` mapeia formas femininas/masculinas de emocoes
  - Entidades masculinas (Mars, Lars) usam formas corretas ("curioso" vs "curiosa")
  - Remove duplicacao de nome no status ("Mars esta curioso" vs "Mars esta Mars curiosa")
- **test_download_modal.py**: 17 testes para DownloadModal e fila de downloads
- **test_emotion_manager.py**: 20 testes para correcao de genero

### Corrigido
- **Visao local com resposta vazia**: Tratamento para quando Ollama retorna texto vazio
  - Adiciona log de warning quando resposta vazia
  - Retorna mensagem informativa ao inves de falhar silenciosamente
- **Download modal travado em 0%**: Codigos ANSI do Ollama impediam extracao de %
  - Regex robusto para limpar `\x1b[...` e caracteres de controle
- **call_from_thread incorreto**: Modal usava `self.call_from_thread` ao inves de `self.app.call_from_thread`

### Testes
- 37 novos testes para UI (DownloadModal, EmotionManager)
- Total: 1268 testes no projeto

## [3.7.1] - 2025-12-28

### Adicionado
- **COMPLIANCE.md**: Documento de conformidade legal e etica
  - Politica de anonimato e uso de IA
  - Regras para servicos externos (APIs, Voice IDs)
  - Verificacao automatica via pre-commit
- **LUNA_AUDITORIA.md**: Scorecard completo do projeto
  - Analise de 215 arquivos Python, 55K linhas de codigo
  - Score geral: 8.1/10
  - Metricas de testes, cobertura, complexidade
- **check_external_ids.sh**: Hook para detectar Voice IDs e API keys hardcoded
- **quick_check.sh**: Validacao rapida para desenvolvimento (< 5s)
- **ENTITY_DOSSIE_TEMPLATE.md**: Template padrao para novas entidades

### Alterado
- **Pre-commit**: Agora com 7 hooks (adicionado check-external-ids)
- **pr-check.yml**: Inclui verificacao de IDs externos
- **validate_all.sh**: Atualizado para 7 validacoes
- **CONTRIBUTING.md**: Adicionada secao de uso de IA no desenvolvimento

### Removido
- Voice IDs de todas as 6 entidades (config.json e DOSSIEs)
- Design prompts de voz (descricoes de como criar vozes)
- Dados de servicos externos dos arquivos de configuracao

### Seguranca
- Limpeza completa de identificadores traceaveis
- Politica de anonimato fortalecida
- Hooks automaticos para prevenir vazamento de dados

## [3.7.0] - 2025-12-28

### Adicionado
- **Desktop Integration (FASE 5)**: Sistema completo de integracao com desktop Linux
  - `src/core/desktop_integration.py` - Modulo central com 6 classes
  - **D-Bus Listener**: Captura notificacoes do sistema via dbus-monitor
  - **Clipboard Monitor**: Monitora alteracoes no clipboard (xclip/xsel)
  - **Active Window Tracker**: Detecta janela ativa (xdotool)
  - **Idle Detector**: Detecta inatividade do usuario (xprintidle)
  - **Proactivity Manager**: Sistema de proatividade temporal com cooldowns
  - Configuravel via `DESKTOP_INTEGRATION` no config.py
- **Input Multilinhas**: Campo de input agora suporta multiplas linhas
  - `Ctrl+J` para inserir quebra de linha (Enter envia)
  - Expande de 1 ate 4 linhas, scroll apos 4
  - Input cresce para CIMA, diminuindo area do chat
- **Menu de Contexto Aprimorado**: Botao direito no input
  - Cortar, Copiar, Colar, Selecionar Tudo
  - Nova Linha (Ctrl+J), Desfazer, Refazer
  - Nova Conversa (Ctrl+N)
- **Estilo Visual do Botao Voz**: Estado ativo com destaque visual
  - `voice-active` e `voice-inactive` CSS classes
  - Cores personalizadas por entidade (branco no texto quando ativo)

### Alterado
- **Requiem (Sair)**: Tempo de duplo clique aumentado para 1.5s
  - Feedback visual via notify() antes de minimizar
  - Log melhorado para debug
- **Layout do Input Container**: Botoes nao crescem mais junto com input
  - `align: left top` no container
  - Botoes com `min-height: 3; max-height: 3` fixos
- **CSS de todas entidades**: Atualizado para suportar novas features
  - Luna, Eris, Juno, Lars, Mars, Somn

### Corrigido
- **Ctrl+Enter/Shift+Enter**: No terminal, essas teclas nao sao distinguiveis de Enter
  - Solucao: usar `Ctrl+J` (ASCII Line Feed) que funciona em todos terminais
- **Fullscreen Animation**: Outros elementos nao sobrepoe mais animacao piscando
  - CSS `fullscreen-active` esconde banner/status durante animacao
- **Menu de Contexto travando**: Movido para `app.call_later()` evitando bloqueio

### Atalhos de Teclado
| Atalho | Acao |
|--------|------|
| Enter | Enviar mensagem |
| Ctrl+J | Nova linha no input |
| Ctrl+A | Selecionar tudo |
| Ctrl+C | Copiar |
| Ctrl+V | Colar |
| Ctrl+X | Cortar |
| Ctrl+Z | Desfazer |
| Ctrl+Y | Refazer |
| Ctrl+N | Nova conversa |
| Escape | Desfocar input |

### Testes
- 186 testes passando
- 9 novos testes para Desktop Integration

## [3.6.0] - 2025-12-27

### Adicionado
- **Test Suite Completo**: 4 suites de teste com 100% pass rate
  - `test_luna_features.py` - Testes de configuracao GLITCH, Visao, Animation
  - `test_pantheon.py` - Testes de entidades e EntityLoader
  - `test_ui_integrity.py` - 28 testes de UI (animacoes, cores, botoes, estabilidade)
  - `test_providers.py` - Testes de Multi-LLM (Ollama/Gemini)
  - `run_tests.py` - Runner unificado de testes
- **Cache L2 Persistente**: Semantic cache agora persiste em SQLite
  - `src/data_memory/cache/semantic_l2.db` - Database de cache
  - L2 TTL de 24h (12x maior que L1)
  - Estatisticas separadas para L1 e L2

### Alterado
- **Registry de Entidades**: Lars, Mars e Somn agora `available: true`
  - Entidades usam fallback para animacoes de Luna quando nao tem proprias
  - Config.json proprio e respeitado (personalidade, cores, frases)
- **Fullscreen Piscando**: Usa CSS classes ao inves de inline styles
  - `.hidden` e `.fullscreen` para layering correto
  - Carregamento dinamico de animacao por entidade

### Corrigido
- **4 excecoes silenciadas** (`except: pass`) agora logam erros:
  - `visao.py:302` - Erro em comparacao de hashes perceptuais
  - `model_manager.py:250` - Status do Ollama
  - `audio_threads.py:523` - Calibracao VAD
  - `banner.py` - Erros de entity loading
- **Router VISION patterns** expandidos para detectar "olhe para mim" corretamente
- **Timeout em chamadas API**: ThreadPoolExecutor com timeout (Gemini 30s, Ollama 60s)
- **Teste de piscando**: Agora suporta arquivos `.txt.gz`

### Estrutura de Testes
```
src/tests/
├── test_luna_features.py    # 19 testes
├── test_pantheon.py         # 20 testes
├── test_providers.py        # Async provider tests
├── test_ui_integrity.py     # 28 testes UI
└── test_vector_store.py     # Vector store tests

run_tests.py                 # Runner unificado
```

## [3.5.0] - 2025-12-27

### Adicionado
- **Padronizacao do Sistema de Entidades**: Estrutura unificada para todas as entidades
  - Documentacao completa: `dev-journey/04-implementation/ENTITY_STRUCTURE.md`
  - Cada entidade agora segue estrutura identica (config.json, alma.txt, CSS, DOSSIE, frases)
- **Arquivos CSS para entidades masculinas**:
  - `templo_de_lars.css` - Tema verde misterio (Dark Academia)
  - `templo_de_mars.css` - Tema vermelho sangue (Guerreiro Alpha)
  - `templo_de_somn.css` - Tema azul onirico (Soft Boy ASMR)
- **Documentacao DOSSIE para entidades masculinas**:
  - `LARS_DOSSIE.md`, `MARS_DOSSIE.md`, `SOMN_DOSSIE.md`
  - Documentacao completa de persona, voz e estetica
- **Frases para treinamento de voz**:
  - `Luna_frases.md`, `Lars_frases.md`, `Mars_frases.md`, `Somn_frases.md`
  - Frases categorizadas por emocao/contexto
- **READMEs de placeholders**:
  - `animations/README.md` - Instrucoes para criar animacoes ASCII
  - `voice/README.md` - Instrucoes para criar audios de referencia

### Alterado
- **Estrutura de voz padronizada**: Todas as entidades usam `voice/{provider}/reference.wav`
- **config.json completo**: Lars, Mars e Somn agora tem config.json com todas as secoes
  - theme, banner_ascii, gradient, phrases, voice, vectordb_metadata
- **Remocao do Vosk**: Wake word detection agora usa Whisper+VAD exclusivamente
  - Removido de requirements.txt, config.py, install.sh
  - Removido diretorio src/models/vosk/

### Corrigido
- Nome de animacao inconsistente: `Juno_obscecada.txt.gz` -> `Juno_obssecada.txt.gz`
- Arquivos de voz renomeados para padrao `reference.wav` (antes variavam)

### Estrutura do Projeto
Veja estrutura completa das entidades em:
- `dev-journey/04-implementation/ENTITY_STRUCTURE.md`

```
src/assets/panteao/entities/{entity}/
├── alma.txt              # Prompt de personalidade
├── config.json           # Configuracoes (cores, voz, frases)
├── {ENTITY}_DOSSIE.md    # Documentacao completa
├── {Entity}_frases.md    # Frases para voz
├── templo_de_{entity}.css # CSS Textual
├── animations/           # ASCII art (.txt.gz)
└── voice/
    ├── coqui/reference.wav
    └── chatterbox/reference.wav
```

## [3.4.0] - 2025-12-24

### Adicionado
- **Daemon Mode / System Tray**: Luna pode rodar em background com icone na bandeja
  - `src/core/daemon.py` - Controller para modo daemon (show/hide/quit/toggle voice)
  - `src/core/tray.py` - SystemTrayManager usando pystray com backend Ayatana
  - `src/assets/icons/luna_tray.png` - Icone personalizado do tray
  - Configuravel via `DAEMON_MODE`, `START_MINIMIZED`, `MINIMIZE_TO_TRAY`
- **Wake Word Detection**: Ativacao por voz com Whisper+VAD
  - `src/soul/wake_word.py` - Thread de deteccao de wake word
  - Padroes suportados: nome da entidade ativa + variantes
  - Configuravel via `WAKE_WORD_ENABLED`, `WAKE_WORD_COOLDOWN`
  - Ativacao via daemon (botao direito em Voz)
- **Voice Profile (Speaker ID)**: Identificacao de usuario por voz
  - `src/soul/voice_profile.py` - Perfil de voz via Resemblyzer embeddings
  - Threshold configuravel via `VOICE_SIMILARITY_THRESHOLD`
- **Diagnostico de Recursos**: Monitor de CPU/GPU/RAM
  - `src/tools/diagnostico_recursos.py` - Utilitario de diagnostico do sistema

### Melhorado
- **install.sh**: Migracao para Ayatana AppIndicator (compatibilidade Pop!_OS/Ubuntu moderno)
  - Adicionados pacotes: `libayatana-appindicator3-1`, `gir1.2-ayatanaappindicator3-0.1`
  - Adicionadas deps PyGObject: `libgirepository1.0-dev`, `libcairo2-dev`, `pkg-config`
- **requirements.txt**: Adicionado `PyGObject>=3.42.0,<3.48.0` para backend AppIndicator

### Corrigido
- Defaults inconsistentes em `reload_config()` (VAD_ENERGY_THRESHOLD, VAD_SILENCE_DURATION)
- Verificacao de Daemon Mode no install.sh agora detecta Ayatana

## [3.3.0] - 2025-12-24

### Adicionado
- **Simetria Visual Startup/Shutdown**: TV static cinematico agora ocorre em ambas direcoes
  - Startup: tela inicia preenchida de static, faz fade_out revelando conteudo (TV sintonizando)
  - Shutdown: fade_in cobrindo tela de static (TV desligando)
- **Sistema de Interrupcao TTS**: Funcao `_interrupt_luna()` para parar TTS de forma consistente
  - Limpa filas `tts_queue` e `tts_playback_queue` ao interromper
  - Sincroniza `is_speaking` com `luna_speaking_event`
- **Deteccao de Genero por Nome**: Modulo `gender_detector.py` com ~130 nomes brasileiros
  - Inferencia automatica M/F/N baseada em terminacoes e heuristicas
  - Tratamentos personalizados por genero (eleito/eleita, meu/minha, etc)
- **Animacao Fullscreen Piscando**: Botao Ver agora usa animacao fullscreen antes de captura

### Melhorado
- TV static no banner sincronizado com animacao durante transicoes
- Portabilidade do `run_luna.sh`: detecta versao Python dinamicamente
- AnimationController pausado corretamente durante animacoes fullscreen

### Corrigido
- Luna lendo multiplas frases simultaneamente (TTS sem respeitar ordem)
- Banner nao desaparecendo ao ativar voz (toggle voice)
- Animacao fullscreen aparecendo apenas no canto (caminho errado)
- Luna chamando usuarios de "Eleite" em vez do nome/genero correto

## [3.2.0] - 2025-12-22

### Adicionado
- **Sistema de Transicoes TV Static**: Efeitos visuais cinematicos em toda a interface
  - `run_startup_static()` - TV static nas 3 areas durante boot
  - `run_shutdown_sequence()` - TV static apenas na animacao ao encerrar
  - `run_processing_static()` - TV static durante processamento de mensagens
  - `run_emotion_transition()` - Transicao entre emocoes antes de voltar ao observando
  - `run_banner_only_static()` - TV static apenas no banner (desativar voz)
  - `run_fullscreen_piscando()` - Animacao fullscreen para captura de visao

### Melhorado
- Botao Ver agora mostra animacao piscando em fullscreen com TV static ao final
- Botao Voz desativando mostra TV static apenas no banner (nao na animacao)
- Transicoes mais suaves entre estados da interface

### Corrigido
- Animacao fullscreen da visao agora restaura UI corretamente

## [3.1.0] - 2025-12-22

### Adicionado
- **Gerenciamento de VRAM**: Sistema automatico de memoria GPU
  - Metodos `unload_model()` e `list_loaded_models()` no OllamaClient
  - Modelos descarregados automaticamente apos 30s de inatividade
  - Variaveis `OLLAMA_KEEP_ALIVE` e `OLLAMA_MAX_LOADED_MODELS`
- Script `cleanup_models.sh` para remover modelos antigos

### Alterado
- Whisper de `medium` para `small` (economiza ~1.5GB VRAM)
- Embeddings forcados para CPU (nao compete por VRAM)
- Modelo de visao: `moondream` (substituiu minicpm-v)
- Removidos modelos de codigo do projeto (qwen2.5-coder, deepseek-coder)

### Corrigido
- CUDA Out of Memory ao usar multiplos modelos simultaneamente
- Modelo de visao gerando texto em thai (agora usa moondream)
- Modelos Ollama nao liberando VRAM apos uso

## [2.3.0] - 2025-12-19

### Adicionado
- TTSPlaybackThread registrada no setup_threading()
- Profiler v2 com InteractionTrace e diagnostico automatico
- Script de diagnostico em src/tools/diagnostico_luna.py
- Thresholds por estagio com alertas automaticos
- Recomendacoes de otimizacao no profiler

### Melhorado
- VAD otimizado: SILENCE_FRAME_LIMIT 15 para 10
- VAD otimizado: ENERGY_THRESHOLD 1500 para 5000
- Canone harmonizado com STYLE_GUIDE (cores solidas, GlitchButton)
- CSS do Canone com bordas e cores consistentes

### Corrigido
- TTSPlaybackThread estava definida mas nunca era registrada
- Latencia de deteccao de fala reduzida em ~200ms

## [3.2.0] - 2025-12-18

### Adicionado
- Sistema de glitch effects procedurais na interface
- Status bar com animação de decriptação progressiva
- Dev_log estruturado para continuidade entre sessões
- Documentação de visão e roadmap do projeto

### Melhorado
- Performance de rendering do TUI
- Estabilidade do sistema de threading
- Logs mais descritivos com contexto de execução

### Corrigido
- Race conditions em operações de quota
- Memory leak em sessões longas
- Sincronização de UI durante operações assíncronas

## [3.1.0] - 2025-12-15

### Adicionado
- API Optimizer agora delega corretamente para Consciência
- Sistema de quota optimization dinâmico
- Throttling adaptativo baseado em uso

### Corrigido
- Multithreading causando deadlocks ocasionais
- Rate limiting não respeitando limites da API
- Crash ao processar imagens muito grandes

## [3.0.0] - 2025-12-10

### Adicionado
- Sistema de memória contextual persistente
- Módulo `memoria.py` para gestão de histórico
- Exportação de sessões em markdown
- Logs rotacionados com compressão automática

### Alterado
- Refatoração completa do sistema de threading
- Arquitetura modular com separação clara de responsabilidades
- Config.ini expandido com seções de memória

### Removido
- Print statements substituídos por logging adequado
- Código legado de protótipos iniciais

## [2.5.0] - 2024-12-20

### Adicionado
- Threading paralelo para operações de I/O
- Rate limiting inteligente via API Optimizer
- Sistema de delegação de modelos (Consciência)

### Melhorado
- Tempo de resposta reduzido em 40%
- Uso de quota otimizado
- Estabilidade em sessões longas

### Corrigido
- Deadlocks em operações simultâneas de voz e texto
- Timeout em processamento de imagens grandes
- Crash ao exceder quota da API

## [2.0.0] - 2024-11-30

### Adicionado
- Suporte a input/output de voz (Whisper + TTS)
- Processamento de imagens via LLM Vision
- Módulo `voz_module.py` para áudio bidirecional
- Capacidade multimodal completa

### Alterado
- Interface TUI redesenhada para acomodar múltiplos inputs
- Sistema de prompts adaptado para visão
- Config expandido com parâmetros de voz

### Corrigido
- Latência em processamento de áudio
- Qualidade de transcrição em ambientes ruidosos
- Sincronização de áudio/texto

## [1.5.0] - 2024-11-01

### Adicionado
- Tema dark Dracula completo
- ASCII art customizado para startup
- Animações básicas de loading
- Sistema de cores configurável

### Melhorado
- Contraste visual da interface
- Legibilidade em terminais diversos
- Consistência estética

## [1.0.0] - 2024-10-15

### Adicionado
- Interface TUI básica com Textual
- Integracao com API LLM
- Sistema de input/output de texto
- Personalidade gótica inicial
- Configuração via `config.ini`
- Logging básico em `logs/`
- README com instruções de instalação
- Licença GPLv3

### Características Iniciais
- Processamento de texto via LLM
- Respostas com personalidade sarcástica
- Tema dark básico
- Comandos de controle (exit, clear)

## [0.1.0] - 2024-09-20

### Adicionado
- Protótipo inicial em CLI puro (sem TUI)
- Conexao basica com API LLM
- Testes de personalidade e tom de resposta
- Estrutura de diretórios inicial

---

## Tipos de Mudanças

- **Adicionado:** para novas features
- **Alterado:** para mudanças em features existentes
- **Descontinuado:** para features que serão removidas
- **Removido:** para features removidas
- **Corrigido:** para correções de bugs
- **Segurança:** para vulnerabilidades corrigidas

## Links de Comparação

[Unreleased]: https://github.com/AndreBFarias/Luna/compare/v3.3.0...HEAD
[3.3.0]: https://github.com/AndreBFarias/Luna/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/AndreBFarias/Luna/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/AndreBFarias/Luna/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/AndreBFarias/Luna/compare/v2.5.0...v3.0.0
[2.5.0]: https://github.com/AndreBFarias/Luna/compare/v2.3.0...v2.5.0
[2.3.0]: https://github.com/AndreBFarias/Luna/compare/v2.0.0...v2.3.0
[2.0.0]: https://github.com/AndreBFarias/Luna/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/AndreBFarias/Luna/compare/v1.0.0...v1.5.0
[1.0.0]: https://github.com/AndreBFarias/Luna/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/AndreBFarias/Luna/releases/tag/v0.1.0
