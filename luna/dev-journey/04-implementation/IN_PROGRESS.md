# Features em Desenvolvimento

**Data:** 2025-12-29
**Branch:** main

---

## TL;DR

Nenhuma feature em desenvolvimento ativo. Projeto em estado estavel na v3.8.0 apos ETAPAs 01-15 de refatoracao (excecoes, memory locks, interfaces, logging, providers, streaming, AI-friendliness, web dashboard).

---

## Contexto

Este documento registra features que estao sendo implementadas mas ainda nao foram concluidas. Inclui checklists de progresso e arquivos afetados.

---

## Features Ativas

### Nenhuma

Todas as features planejadas para v3.8.0 foram concluidas em 2025-12-29.

---

## ETAPAs Concluidas (2025-12-29)

### ETAPA 01-06: Refatoracao Base
- [x] Silent exceptions corrigidas (~70 ocorrencias)
- [x] Memory locks com hierarquia de excecoes
- [x] Interface abstrata para memoria
- [x] Logging centralizado
- [x] Separacao de Consciencia (response_parser, context_builder)
- [x] Personality anchor system

### ETAPA 07-12: Provider System
- [x] UniversalLLM com fallback automatico
- [x] Type hints em 23 arquivos criticos
- [x] __all__ em todos os __init__.py
- [x] Constantes centralizadas
- [x] Memory tiers (short-term, promotion)
- [x] Streaming response completo

### ETAPA 13-15: AI-Friendliness e Finalizacao
- [x] DEPENDENCY_MAP.md criado
- [x] Docstrings em 9 arquivos principais
- [x] Web Dashboard com FastAPI
- [x] Documentacao final atualizada

---

## Proximas Iteracoes (Aguardando Priorizacao)

### 1. Sistema de Plugins
- [ ] Arquitetura base de plugins
- [ ] Loader dinamico
- [ ] API para extensoes
- [ ] Documentacao de desenvolvimento

### 2. CLI Interativo (Rich CLI)
- [ ] Argumentos de linha de comando
- [ ] Modo headless
- [ ] Output JSON
- [ ] Pipe support

### 3. Busca em Historico
- [ ] Indexacao de sessoes
- [ ] Search API
- [ ] UI de busca

---

## Refatoracoes Pendentes

### 1. Testes de Integracao
- [ ] Integration tests para audio pipeline
- [ ] E2E tests com mock de APIs
- [ ] CI/CD com GitHub Actions melhorado

### 2. Documentacao Tecnica
- [ ] API reference auto-gerada (Sphinx/MkDocs)
- [ ] Guia de contribuicao

---

## Bloqueios

Nenhum bloqueio ativo no momento.

---

## Links Relacionados

- [CURRENT_STATUS.md](./CURRENT_STATUS.md)
- [COMPLETED_FEATURES.md](./COMPLETED_FEATURES.md)
- [PLANNED_FEATURES.md](../05-future/PLANNED_FEATURES.md)
- [TECHNICAL_DEBT.md](../05-future/TECHNICAL_DEBT.md)
