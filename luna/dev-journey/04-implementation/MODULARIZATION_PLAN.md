# Plano de Modularizacao - God Mode Prevention

**Data:** 2025-12-30
**Meta:** Reduzir todos os arquivos para <300 linhas
**Total de Arquivos:** 38
**Total de Linhas Legadas:** ~20.000

---

## Prioridades

| Prioridade | Criterio | Arquivos | Linhas |
|------------|----------|----------|--------|
| **P0** | >700 linhas | 10 | ~9.200 |
| **P1** | 500-700 linhas | 10 | ~5.600 |
| **P2** | 300-500 linhas | 18 | ~6.400 |

---

## P0 - Criticos (>700 linhas)

| # | Arquivo | Linhas | Estrategia |
|---|---------|--------|------------|
| 1 | `src/ui/screens.py` | 1354 | Extrair cada Screen para arquivo proprio |
| 2 | `src/ui/banner.py` | 1243 | Separar ASCII art, efeitos, animacoes |
| 3 | `src/soul/audio_threads.py` | 1046 | Dividir por tipo de thread |
| 4 | `src/soul/consciencia.py` | 790 | Extrair providers, cache, routing |
| 5 | `src/soul/boca.py` | 755 | Separar TTS engines (coqui, chatterbox) |
| 6 | `src/core/desktop_integration.py` | 747 | Dividir: notifications, autostart, tray |
| 7 | `src/soul/onboarding.py` | 742 | Extrair steps, validacao, UI |
| 8 | `src/core/metricas.py` | 727 | Separar collectors, reporters, storage |
| 9 | `src/soul/live_session.py` | 704 | Dividir: state, handlers, persistence |

---

## P1 - Alto (500-700 linhas)

| # | Arquivo | Linhas | Estrategia |
|---|---------|--------|------------|
| 10 | `src/soul/visao.py` | 685 | Extrair providers, image processing |
| 11 | `src/soul/user_profiler.py` | 621 | Separar analysis, storage, inference |
| 12 | `src/data_memory/smart_memory.py` | 615 | Dividir: index, retrieval, persistence |
| 13 | `src/core/ollama_client.py` | 560 | Extrair retry logic, streaming, parsing |
| 14 | `src/soul/threading_manager.py` | 538 | Separar por tipo de thread |
| 15 | `src/core/profiler.py` | 528 | Dividir: cpu, memory, gpu profilers |
| 16 | `src/ui/dashboard.py` | 521 | Extrair widgets, charts, state |
| 17 | `src/ui/theme_manager.py` | 516 | Separar themes, colors, fonts |
| 18 | `src/core/animation.py` | 505 | Dividir: loader, cache, renderer |

---

## P2 - Medio (300-500 linhas)

| # | Arquivo | Linhas | Estrategia |
|---|---------|--------|------------|
| 19 | `src/soul/processing_threads.py` | 485 | Agrupar por funcionalidade |
| 20 | `src/soul/personalidade.py` | 463 | Extrair traits, moods, responses |
| 21 | `src/soul/response_parser.py` | 460 | Separar parsers por formato |
| 22 | `src/soul/voice_system.py` | 429 | Dividir: detection, synthesis |
| 23 | `src/tools/qa_automated.py` | 425 | Extrair test runners |
| 24 | `src/tools/web_search.py` | 415 | Separar providers |
| 25 | `src/core/entity_loader.py` | 378 | Dividir: config, assets, cache |
| 26 | `src/soul/wake_word.py` | 366 | Extrair detector, patterns |
| 27 | `src/tools/diagnostico_luna.py` | 361 | Separar checks por categoria |
| 28 | `src/app/luna_app.py` | 356 | Extrair mais mixins |
| 29 | `src/core/terminal_executor.py` | 355 | Dividir: parser, executor, sandbox |
| 30 | `src/tools/tts_daemon.py` | 354 | Separar daemon, queue, worker |
| 31 | `src/ui/status_decrypt.py` | 344 | Extrair effects |
| 32 | `src/ui/entity_selector.py` | 343 | Dividir: selector, preview |
| 33 | `src/soul/voice_profile.py` | 338 | Separar profile, cloning |
| 34 | `src/soul/reminders.py` | 329 | Dividir: scheduler, storage |
| 35 | `src/ui/intro_animation.py` | 322 | Extrair frames, renderer |
| 36 | `src/core/session.py` | 322 | Separar: state, persistence |
| 37 | `src/data_memory/vector_store_optimized.py` | 308 | Dividir: index, search |
| 38 | `src/core/terminal_sandbox.py` | 308 | Extrair validators |

---

## Estrategias de Modularizacao

### 1. Extracao por Responsabilidade

```
ANTES:
src/ui/screens.py (1354 linhas)
  - HomeScreen
  - SettingsScreen
  - ChatScreen
  - ...

DEPOIS:
src/ui/screens/
  __init__.py (exports)
  home.py (~200 linhas)
  settings.py (~200 linhas)
  chat.py (~200 linhas)
  base.py (~100 linhas)
```

### 2. Extracao de Componentes

```
ANTES:
src/soul/boca.py (755 linhas)
  - CoquiTTS
  - ChatterboxTTS
  - VoiceManager

DEPOIS:
src/soul/tts/
  __init__.py (exports)
  coqui.py (~200 linhas)
  chatterbox.py (~200 linhas)
  manager.py (~150 linhas)
```

### 3. Separacao de Concerns

```
ANTES:
src/core/metricas.py (727 linhas)
  - MetricsCollector
  - MetricsReporter
  - MetricsStorage
  - Helpers

DEPOIS:
src/core/metrics/
  __init__.py
  collector.py
  reporter.py
  storage.py
```

---

## Processo de Refatoracao

1. **Criar Issue** com label `type:refactor` e `god-mode-fix`
2. **Criar Branch** `refactor/split-{filename}`
3. **Extrair Modulo** mantendo interface publica
4. **Atualizar Imports** em arquivos dependentes
5. **Rodar Testes** `pytest src/tests/ -v`
6. **Verificar Linhas** `wc -l arquivo.py`
7. **Remover do legacy_files.txt** quando <300
8. **Merge PR** com closes #ISSUE

---

## Metricas de Sucesso

- [ ] 0 arquivos em P0 (>700 linhas)
- [ ] 0 arquivos em P1 (500-700 linhas)
- [ ] 0 arquivos em P2 (300-500 linhas)
- [ ] legacy_files.txt vazio
- [ ] Todos testes passando
- [ ] Coverage >= 60%

---

## Timeline Sugerida

| Semana | Foco | Arquivos |
|--------|------|----------|
| 1 | P0 Criticos | screens.py, banner.py |
| 2 | P0 Soul | audio_threads.py, consciencia.py, boca.py |
| 3 | P0 Core | desktop_integration.py, metricas.py |
| 4 | P0 Finais + P1 Inicio | onboarding.py, live_session.py, visao.py |
| 5-6 | P1 | Restante P1 |
| 7-8 | P2 | Todos P2 |

---

## Labels GitHub

```bash
gh label create "god-mode-fix" --color "FF6B6B" --description "Arquivo >300 linhas para modularizar"
gh label create "size:P0" --color "B60205" --description ">700 linhas - Critico"
gh label create "size:P1" --color "D93F0B" --description "500-700 linhas - Alto"
gh label create "size:P2" --color "FBCA04" --description "300-500 linhas - Medio"
```
