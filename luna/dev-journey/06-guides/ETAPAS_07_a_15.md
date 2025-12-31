# ETAPAS 07-15 - MELHORIAS ADICIONAIS

---

# ETAPA 07 - UNIVERSAL LLM INTERFACE

## Prioridade: P1-ALTA
## Branch: `feat/etapa-07-universal-llm`

### Objetivo
Criar abstraction layer para providers LLM com fallback automatico.

### Arquivos para Criar
- `src/soul/llm_interface.py` - Interface abstrata
- `src/soul/providers/__init__.py`
- `src/soul/providers/gemini_provider.py`
- `src/soul/providers/ollama_provider.py`

### Tarefas
1. Criar interface LLMProvider ABC com metodos generate(), is_available(), health_check()
2. Criar UniversalLLM com fallback chain
3. Integrar em consciencia.py
4. Testes: `src/tests/test_universal_llm.py`

### Issue
```bash
gh issue create --title "[P1] Criar Universal LLM Interface" --label "enhancement,priority:high"
```

### Validacao GUI
- [ ] Rodar com Ollama -> funciona
- [ ] Matar Ollama -> fallback pra Gemini automatico
- [ ] Log mostra "fallback para gemini"

---

# ETAPA 08 - TYPE HINTS EM FUNCOES PUBLICAS

## Prioridade: P2-MEDIA
## Branch: `refactor/etapa-08-type-hints`

### Objetivo
Adicionar type hints em funcoes publicas dos modulos principais.

### Arquivos para Modificar (prioridade)
1. `src/soul/consciencia.py`
2. `src/data_memory/smart_memory.py`
3. `src/core/entity_loader.py`
4. `src/ui/screens.py`
5. `src/soul/boca.py`

### Tarefas
1. Instalar mypy: `pip install mypy types-requests`
2. Adicionar config em pyproject.toml
3. Adicionar types em funcoes publicas (sem _ no inicio)
4. Atualizar pre-commit com mypy hook

### pyproject.toml
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
ignore_missing_imports = true
check_untyped_defs = true
```

### Issue
```bash
gh issue create --title "[P2] Adicionar type hints em funcoes publicas" --label "enhancement,priority:medium"
```

### Validacao
- [ ] `mypy src/soul/consciencia.py` sem erros
- [ ] Pre-commit passa

---

# ETAPA 09 - CRIAR INDEX.MD PARA IAs

## Prioridade: P2-MEDIA
## Branch: `docs/etapa-09-index-md`

### Objetivo
Criar arquivo de referencia rapida para IAs trabalhando no projeto.

### Arquivo para Criar
`INDEX.md` na raiz do projeto com:
- Navegacao rapida (tabela de arquivos importantes)
- Fluxo de dados principal (diagrama ASCII)
- Comandos uteis
- Convencoes do projeto
- Estrutura de entidades

### Conteudo Sugerido
```markdown
# Luna - Indice Rapido

## Navegacao
| Objetivo | Arquivo |
|----------|---------|
| Arquitetura | dev-journey/01-getting-started/ARCHITECTURE.md |
| Regras | IMPORTANT.md |
| Cerebro | src/soul/consciencia.py |

## Fluxo
Usuario -> voice_system -> audio_threads -> consciencia -> boca -> audio_threads

## Comandos
- `./scripts/quick_check.sh` - Validacao rapida
- `pytest src/tests/ -v` - Testes
```

### Issue
```bash
gh issue create --title "[P2] Criar INDEX.md para IAs" --label "documentation,priority:medium"
```

---

# ETAPA 10 - DOCUMENTAR CONSTANTES MAGICAS

## Prioridade: P2-MEDIA
## Branch: `refactor/etapa-10-constants`

### Objetivo
Centralizar magic numbers em arquivo documentado.

### Arquivo para Criar
`src/core/constants.py` com classes:
- MemoryConstants (thresholds, TTLs)
- CacheConstants (hit threshold, max size)
- AudioConstants (VAD, timeouts)
- PersonalityConstants (reinforcement interval)

### Tarefas
1. Criar constants.py com docstrings
2. Substituir magic numbers nos arquivos
3. Testes: `src/tests/test_constants.py`

### Issue
```bash
gh issue create --title "[P2] Documentar constantes magicas" --label "enhancement,priority:medium"
```

---

# ETAPA 11 - MEMORIA CURTO/MEDIO/LONGO PRAZO

## Prioridade: P2-MEDIA
## Branch: `feat/etapa-11-memory-tiers`

### Objetivo
Implementar sistema de memoria com tres horizontes temporais.

### Arquivos para Criar
- `src/data_memory/short_term_memory.py` - Buffer de 5 min
- `src/data_memory/memory_consolidator.py` - Promove memorias

### Tarefas
1. ShortTermMemory com deque e TTL
2. MemoryConsolidator para promover memorias importantes
3. Integrar com UnifiedMemory
4. Testes de promocao

### Issue
```bash
gh issue create --title "[P2] Implementar memoria curto/medio/longo prazo" --label "enhancement,priority:medium"
```

### Validacao GUI
- [ ] Dizer "meu nome e Andre" -> Luna lembra
- [ ] Reiniciar Luna -> ainda lembra (longo prazo)
- [ ] Info irrelevante esquecida apos 5 min

---

# ETAPA 12 - STREAMING RESPONSE

## Prioridade: P3-BAIXA
## Branch: `feat/etapa-12-streaming`

### Objetivo
Exibir resposta token-by-token para melhor UX.

### Arquivos para Criar
- `src/soul/streaming_handler.py`

### Tarefas
1. StreamingHandler com generator
2. Atualizar UI para receber chunks
3. Animacao de "pensando"

### Issue
```bash
gh issue create --title "[P3] Implementar streaming de respostas" --label "enhancement,priority:low"
```

### Validacao GUI
- [ ] Perguntar algo longo -> texto aparece gradualmente
- [ ] Nao trava esperando resposta completa

---

# ETAPA 13 - MELHORAR AI-FRIENDLINESS

## Prioridade: P3-BAIXA
## Branch: `docs/etapa-13-ai-friendly`

### Objetivo
Tornar codigo mais facil de navegar para IAs.

### Tarefas
1. Adicionar docstrings no topo de cada arquivo .py
2. Criar `__all__` em cada `__init__.py`
3. Adicionar comentarios de secao em arquivos grandes
4. Criar `dev-journey/04-implementation/DEPENDENCY_MAP.md`

### Issue
```bash
gh issue create --title "[P3] Melhorar AI-friendliness do codigo" --label "documentation,priority:low"
```

---

# ETAPA 14 - REFATORAR BANNER.PY

## Prioridade: P3-BAIXA
## Branch: `refactor/etapa-14-banner`

### Objetivo
Extrair AnimationRenderer de banner.py (1239 linhas).

### Arquivos para Criar
- `src/ui/animation_renderer.py`

### Tarefas
1. Mover logica de rendering de frames
2. BannerGlitchWidget usa AnimationRenderer
3. Manter retrocompatibilidade

### Issue
```bash
gh issue create --title "[P3] Refatorar banner.py - extrair AnimationRenderer" --label "enhancement,priority:low"
```

### Validacao GUI
- [ ] Banner anima normalmente
- [ ] Trocar emocao funciona
- [ ] `wc -l src/ui/banner.py` < 600

---

# ETAPA 15 - SEPARAR CANONE DE SCREENS.PY

## Prioridade: P3-BAIXA
## Branch: `refactor/etapa-15-canone`

### Objetivo
Extrair CanoneScreen para arquivo proprio.

### Arquivos para Criar
- `src/ui/canone_screen.py`

### Tarefas
1. Mover CanoneScreen e classes relacionadas
2. Atualizar imports em screens.py
3. Manter `from src.ui.screens import CanoneScreen` funcionando

### Issue
```bash
gh issue create --title "[P3] Separar CanoneScreen de screens.py" --label "enhancement,priority:low"
```

### Validacao GUI
- [ ] Abrir Canone (engrenagem)
- [ ] Todas as abas funcionam
- [ ] Salvar configuracoes persiste
- [ ] `wc -l src/ui/screens.py` < 600

---

# CHECKLIST FINAL POS-TODAS-ETAPAS

```bash
# Validacao completa
./scripts/validate_all.sh
pytest src/tests/ -v
ruff check src/
mypy src/soul/ src/data_memory/

# Verificar linhas de arquivos grandes
wc -l src/soul/consciencia.py  # < 800
wc -l src/ui/banner.py         # < 600
wc -l src/ui/screens.py        # < 600

# Verificar documentacao
ls dev-journey/03-changelog/2025-12-29_*.md

# Criar release
git checkout main
git merge --no-ff fix/etapa-01-silent-exceptions
# ... merge todas as branches
git tag v3.8.0
git push origin main --tags
```

---

# ORDEM DE EXECUCAO RECOMENDADA

| Ordem | Etapa | Prioridade | Tempo Est. |
|-------|-------|------------|------------|
| 1 | 01 - Silent Exceptions | P0 | 1h |
| 2 | 02 - Memory Locks | P0 | 1h |
| 3 | 03 - Memory Interface | P0 | 2h |
| 4 | 04 - Logging | P1 | 1h |
| 5 | 05 - Split Consciencia | P1 | 3h |
| 6 | 06 - Personality Anchor | P1 | 2h |
| 7 | 07 - Universal LLM | P1 | 2h |
| 8 | 08 - Type Hints | P2 | 2h |
| 9 | 09 - INDEX.md | P2 | 30min |
| 10 | 10 - Constants | P2 | 1h |
| 11 | 11 - Memory Tiers | P2 | 3h |
| 12 | 12 - Streaming | P3 | 2h |
| 13 | 13 - AI-Friendly | P3 | 1h |
| 14 | 14 - Banner Refactor | P3 | 2h |
| 15 | 15 - Canone Refactor | P3 | 1h |

**Total estimado: ~24h de trabalho**
