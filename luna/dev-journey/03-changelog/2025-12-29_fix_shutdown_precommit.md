# 2025-12-29: Fix Shutdown + Pre-commit Quality Gates

## Parte 1: Correcao de Erros de Shutdown

### Problema
Erros de runtime durante o shutdown da aplicacao:
- `MountError: Can't mount widget(s) before VerticalScroll is mounted`
- `RuntimeError: cannot schedule new futures after interpreter shutdown`
- Ollama timeouts continuando apos shutdown

### Causa Raiz
Race conditions entre threads de processamento e o ciclo de vida da UI:
1. `ThreadPoolExecutor.submit()` chamado apos executor fechado
2. `call_from_thread()` chamado apos UI desmontada
3. Sessoes aiohttp ativas durante fechamento do interpreter

### Correcoes Implementadas

#### processing_threads.py
- Adicionado `_executor_shutdown` flag em ProcessingThread
- Verificacao de shutdown antes de `executor.submit()`
- Try/except para capturar RuntimeError de executor fechado
- Metodo `_safe_call_from_thread()` em CoordinatorThread
- Flag `_app_mounted` para evitar chamadas apos desmontagem

#### consciencia.py
- Verificacao de `shutdown_event.is_set()` antes de chamadas LLM
- Try/except ao redor de ThreadPoolExecutor para chamadas Gemini/Ollama

#### ollama_client.py
- Flag `_closed` em OllamaClient para rastrear estado
- Flag `_shutdown` em OllamaSyncClient
- Tratamento graceful de fechamento de sessao aiohttp

### Testes Adicionados
- `test_shutdown_guards.py`: 14 testes cobrindo todos os guards de shutdown

---

## Parte 2: Pre-commit Quality Gates

### Novos Hooks

#### [08/12] God Mode Prevention (max 500 linhas)
Script: `src/tools/check_file_size.sh`
- Bloqueia novos arquivos com mais de 500 linhas
- Arquivos legados permitidos mas com aviso se crescerem >50 linhas
- Forca modularizacao desde o inicio

#### [09/12] Novos scripts documentados
Script: `src/tools/check_new_script_docs.sh`
- Verifica se novos scripts tem teste correspondente (obrigatorio)
- Avisa se nao tem issue referenciada no commit
- Avisa se changelog nao foi atualizado

### Arquivos Legados (>500 linhas permitidos)
- consciencia.py, screens.py, banner.py, audio_threads.py
- desktop_integration.py, onboarding.py, boca.py, metricas.py
- live_session.py, visao.py, user_profiler.py, smart_memory.py
- ollama_client.py, threading_manager.py, profiler.py
- dashboard.py, theme_manager.py, processing_threads.py

### CI Atualizado
Job `quality-gates` adicionado antes de lint:
1. Check file sizes (God Mode Prevention)
2. Check for unused imports (warning only)

---

## Resumo

| Item | Status |
|------|--------|
| Shutdown guards | Implementado |
| 14 testes de shutdown | Passando |
| Hook God Mode | Implementado |
| Hook Novos Scripts | Implementado |
| CI Atualizado | Implementado |
| Pre-commit 12/12 hooks | Passando |
