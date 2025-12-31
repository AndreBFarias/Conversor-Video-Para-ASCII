# Features Planejadas

**Data:** 2025-12-18
**Branch:** main

---

## TL;DR

Roadmap de features futuras para Luna, organizadas por prioridade. Inclui estimativas de complexidade, dependencias e arquivos afetados.

---

## Contexto

Este documento define o roadmap tecnico de longo prazo. Features sao priorizadas considerando impacto, complexidade e dependencias. Atualizado conforme demanda do usuario e evolucao do projeto.

---

## Prioridade Alta

### 1. Sistema de Plugins
**Prioridade:** Alta
**Complexidade:** Media
**Estimativa:** 2-3 semanas

**Descricao:**
Arquitetura extensivel que permite adicionar funcionalidades via plugins. Loader dinamico com hot-reload.

**Casos de uso:**
- Integracao com APIs externas (Notion, Todoist, Spotify)
- Ferramentas customizadas (web scraping, data analysis)
- Extensoes de UI

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/core/plugin_loader.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/core/plugin_api.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/core/plugin_registry.py`
- `/home/andrefarias/Desenvolvimento/Luna/plugins/` (diretorio)

**Dependencias:**
- Nenhuma

**Requisitos tecnicos:**
- importlib para dynamic loading
- API padronizada com classes abstratas
- Sandboxing basico

---

### 2. Testes Automatizados
**Prioridade:** Alta
**Complexidade:** Media
**Estimativa:** 1-2 semanas

**Descricao:**
Suite completa de testes (unit, integration, e2e). CI/CD com GitHub Actions.

**Casos de uso:**
- Prevenir regressoes
- Validar PRs automaticamente
- Cobertura de codigo >80%

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/tests/unit/test_consciencia.py`
- `/home/andrefarias/Desenvolvimento/Luna/tests/integration/test_audio_pipeline.py`
- `/home/andrefarias/Desenvolvimento/Luna/tests/e2e/test_full_conversation.py`
- `/home/andrefarias/Desenvolvimento/Luna/.github/workflows/ci.yml`

**Dependencias:**
- Nenhuma

**Requisitos tecnicos:**
- pytest
- pytest-asyncio
- pytest-mock
- Coverage.py

---

### 3. Web Interface (FastAPI + WebSockets)
**Prioridade:** Alta
**Complexidade:** Alta
**Estimativa:** 3-4 semanas

**Descricao:**
Interface web moderna com streaming de audio/video. Backend FastAPI, frontend React/Vue.

**Casos de uso:**
- Acesso remoto
- Uso em mobile
- Deploy em servidor

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/web/server.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/web/websocket_handler.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/web/static/` (frontend)
- `/home/andrefarias/Desenvolvimento/Luna/docker-compose.yml`

**Dependencias:**
- Nenhuma

**Requisitos tecnicos:**
- FastAPI
- WebSockets
- React/Vue.js
- Docker

---

## Prioridade Media

### 4. CLI Interativo (Rich CLI)
**Prioridade:** Media
**Complexidade:** Baixa
**Estimativa:** 1 semana

**Descricao:**
Modo CLI headless com argumentos de linha de comando. Suporte a piping e output JSON.

**Casos de uso:**
- Scripts automatizados
- Integracao com outras ferramentas
- Uso em servidores sem GUI

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/cli/cli_handler.py`
- `/home/andrefarias/Desenvolvimento/Luna/cli.py`

**Dependencias:**
- Nenhuma

**Requisitos tecnicos:**
- argparse ou typer
- Rich para formatacao

**Exemplo de uso:**
```bash
luna --query "Qual o clima hoje?" --output json
luna --file input.txt --mode summarize
echo "Ola Luna" | luna --pipe
```

---

### 5. Sistema de Ferramentas (Function Calling)
**Prioridade:** Media
**Complexidade:** Media
**Estimativa:** 2 semanas

**Descricao:**
Integracao com Gemini Function Calling. Luna pode executar funcoes Python durante conversas.

**Casos de uso:**
- Consultar APIs (clima, noticias)
- Executar comandos do sistema
- Manipular arquivos

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/tools/tool_registry.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/tools/builtin_tools.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/soul/function_calling.py`

**Dependencias:**
- Sistema de Plugins (recomendado)

**Requisitos tecnicos:**
- Gemini Function Calling API
- Schema de tools em JSON
- Validacao de parametros

---

### 6. Multi-Usuario com SQLite
**Prioridade:** Media
**Complexidade:** Media
**Estimativa:** 1-2 semanas

**Descricao:**
Suporte a multiplos usuarios com historicos isolados. Banco de dados SQLite.

**Casos de uso:**
- Familias compartilhando Luna
- Ambientes multi-tenant
- Backup de conversas

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/database/db_manager.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/database/models.py`
- `/home/andrefarias/Desenvolvimento/Luna/data/luna.db`

**Dependencias:**
- Nenhuma

**Requisitos tecnicos:**
- SQLAlchemy
- SQLite3
- Migracao de historico atual

---

## Prioridade Baixa

### 7. Mobile App (Flutter/React Native)
**Prioridade:** Baixa
**Complexidade:** Alta
**Estimativa:** 6-8 semanas

**Descricao:**
App nativo para Android/iOS com sincronizacao com backend.

**Casos de uso:**
- Luna on-the-go
- Push notifications
- Sincronizacao cross-device

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/mobile/` (diretorio separado)

**Dependencias:**
- Web Interface (FastAPI backend)

**Requisitos tecnicos:**
- Flutter ou React Native
- Backend API REST
- Firebase para notificacoes

---

### 8. Suporte a RAG (Retrieval Augmented Generation)
**Prioridade:** Baixa
**Complexidade:** Media
**Estimativa:** 2-3 semanas

**Descricao:**
Sistema RAG para consultar documentos locais. Upload de PDFs, TXTs, Markdown.

**Casos de uso:**
- Consultar manuais
- Responder sobre documentos
- Knowledge base personalizada

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/rag/document_loader.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/rag/chunker.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/rag/retriever.py`

**Dependencias:**
- Memoria Vetorial (ja existe)

**Requisitos tecnicos:**
- LangChain ou LlamaIndex
- PDF parser (PyPDF2, pdfplumber)
- Chunking estrategico

---

### 9. Custom Wake Word
**Prioridade:** Baixa
**Complexidade:** Media
**Estimativa:** 1-2 semanas

**Descricao:**
Deteccao de wake word customizada ("Hey Luna"). Modelo leve rodando em background.

**Casos de uso:**
- Ativacao por voz hands-free
- Melhor UX para modo voz

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/soul/wake_word.py`

**Dependencias:**
- Sistema de Voz (ja existe)

**Requisitos tecnicos:**
- Porcupine ou Snowboy
- Threading para deteccao continua
- Configuracao de sensibilidade

---

### 10. Suporte a Gemini Pro Vision
**Prioridade:** Baixa
**Complexidade:** Baixa
**Estimativa:** 3 dias

**Descricao:**
Upgrade para Gemini Pro Vision com streaming de video.

**Casos de uso:**
- Analise de video em tempo real
- Reconhecimento de objetos/faces
- Descricoes mais ricas

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/soul/visao.py` (update)

**Dependencias:**
- Visao Computacional (ja existe)

**Requisitos tecnicos:**
- Gemini Pro Vision API
- Streaming de frames

---

## Experimentos

### 11. Modo Agente Autonomo
**Prioridade:** Experimental
**Complexidade:** Alta
**Estimativa:** 4-6 semanas

**Descricao:**
Luna executa tarefas complexas autonomamente (estilo AutoGPT/BabyAGI).

**Casos de uso:**
- Pesquisa profunda
- Planejamento multi-step
- Execucao de workflows

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/src/agent/planner.py`
- `/home/andrefarias/Desenvolvimento/Luna/src/agent/executor.py`

**Dependencias:**
- Sistema de Ferramentas
- Sistema de Plugins

**Requisitos tecnicos:**
- ReAct pattern
- Tree of thoughts
- Self-reflection

---

### 12. Fine-Tuning de Modelos
**Prioridade:** Experimental
**Complexidade:** Alta
**Estimativa:** 4-8 semanas

**Descricao:**
Fine-tuning de modelos open-source (Llama, Mistral) para personalidade de Luna.

**Casos de uso:**
- Luna 100% local
- Privacidade total
- Personalizacao profunda

**Arquivos estimados:**
- `/home/andrefarias/Desenvolvimento/Luna/fine_tune/` (diretorio)

**Dependencias:**
- Dataset de conversas
- GPU potente

**Requisitos tecnicos:**
- Unsloth ou Axolotl
- LoRA/QLoRA
- VRAM >12GB

---

## Links Relacionados

- [IN_PROGRESS.md](../04-implementation/IN_PROGRESS.md)
- [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md)
- [IDEAS_BACKLOG.md](./IDEAS_BACKLOG.md)
- [CURRENT_STATUS.md](../04-implementation/CURRENT_STATUS.md)
