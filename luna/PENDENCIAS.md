# PENDENCIAS - Luna v3.8.2

```
ATUALIZADO: 2025-12-31
STATUS: EM PROGRESSO
```

---

## SUMARIO

| Categoria | Pendentes | Concluidos |
|-----------|-----------|------------|
| Auditoria P1 | 0 | 2 |
| Auditoria P2 | 1 | 4 |
| Auditoria P3 | 0 | 1 |
| Integracao | 2 | 2 |
| Duplicatas | 0 | 4 |
| Otimizacao | 4 | 0 |
| Qualidade | 3 | 0 |

---

## 1. AUDITORIA EXTERNA (P1-P3)

### P1 - CONCLUIDO
- [x] Voice Normalizer - Interface unificada TTS
- [x] Input Container CSS - Crescimento para cima

### P2 - QUASE COMPLETO
- [x] Script de Acentuacao - Detector de acentos faltantes
- [x] History Modal CSS - Estilos da Biblioteca
- [x] Canone/Biblioteca Layout - IDs reconciliados
- [ ] **Web Dashboard Completo** - Funcionalidades faltantes:
  - Animacoes ASCII no dashboard
  - Historico de conversas
  - Seletor de entidades funcional
  - Configuracoes rapidas (TTS, entidade)
  - Banner com efeito glitch
  - Visualizador de audio
  - Anexar arquivos

### P3 - CONCLUIDO
- [x] System Tray - Icone na bandeja do sistema

---

## 2. INTEGRACAO DE SCRIPTS

### 2.1 Verificar Integracao Completa
- [ ] Testar fluxo completo: `run_luna.sh` -> `main.py` -> TUI
- [ ] Testar `run_dashboard.py` com todas as rotas
- [ ] Testar `run_luna_onboarding.sh` em ambiente limpo
- [ ] Validar `run_interface_web.sh` com browser

### 2.2 Scripts de Manutencao
- [ ] Verificar `install.sh` em ambiente limpo (Ubuntu/Pop!_OS)
- [ ] Testar `uninstall.sh` remove tudo corretamente
- [ ] Validar `run_tests.py` executa todos os testes

### 2.3 Ferramentas - CONCLUIDO
- [x] Integrar `check_acentuacao.py` no pre-commit
- [x] Criar script de health check do sistema (`scripts/health_check.sh`)

---

## 3. DUPLICATA DE CODIGO - ANALISADO

### 3.1 Arquivos Suspeitos - RESOLVIDO
- [x] `src/soul/boca.py` vs `src/soul/boca/` - wrapper necessario (padrao arquitetural valido)
- [x] `src/soul/consciencia.py` vs `src/soul/consciencia/` - wrapper necessario (padrao arquitetural valido)
- [x] `src/soul/visao.py` vs `src/soul/visao/` - wrapper necessario (padrao arquitetural valido)
- [x] `src/core/animation.py` vs `src/core/animation/` - wrapper necessario (padrao arquitetural valido)

**Nota:** Os arquivos `.py` sao wrappers de compatibilidade que re-exportam classes das pastas correspondentes. Isso mantem imports simples e API estavel.

### 3.2 Funcoes Duplicadas - NAO HA DUPLICACAO
- [x] `read_json_safe` / `write_json_safe` - centralizadas em `src/core/file_lock.py`
- [x] `get_logger` - centralizado em `src/core/logging_config.py`
- [ ] Consolidar helpers de path em um unico modulo (backlog)

### 3.3 CSS Duplicado - DOCUMENTADO
- [x] CSS de entidades sao copias do universal com cores substituidas
- [ ] Extrair variaveis CSS comuns (refatoracao futura)
- [x] Removido `templo_de_lars.css` duplicado em `juno/`

**Recomendacao futura:** Usar apenas templo_universal.css como template e substituir cores em runtime.

---

## 4. OTIMIZACAO

### 4.1 Performance
- [ ] Profiling do startup time (meta: <3s)
- [ ] Lazy loading de modulos pesados (torch, transformers)
- [ ] Cache de animacoes pre-processadas
- [ ] Reduzir imports circulares

### 4.2 Memoria
- [ ] Revisar singletons que nunca sao liberados
- [ ] Implementar cleanup de cache apos X minutos
- [ ] Verificar memory leaks em sessoes longas

### 4.3 I/O
- [ ] Batch writes para logs
- [ ] Async file operations onde possivel
- [ ] Compressao de sessoes antigas

### 4.4 GPU
- [ ] Verificar se modelos sao descarregados quando nao usados
- [ ] Implementar fallback CPU quando GPU ocupada
- [ ] Monitorar VRAM usage

---

## 5. QUALIDADE DE CODIGO

### 5.1 Type Hints
- [ ] Completar type hints em `src/soul/`
- [ ] Completar type hints em `src/core/`
- [ ] Completar type hints em `src/ui/`
- [ ] Rodar mypy com strict mode

### 5.2 Docstrings
- [ ] Documentar funcoes publicas em `src/soul/`
- [ ] Documentar classes principais
- [ ] Gerar documentacao automatica (pdoc/sphinx)

### 5.3 Testes
- [ ] Aumentar cobertura para 70%+ (atual ~60%)
- [ ] Adicionar testes de integracao
- [ ] Testar fluxos de UI com textual-dev

---

## 6. MINUCIAS

### 6.1 UX
- [ ] Placeholder dinamico no input baseado em entidade
- [ ] Feedback visual durante carregamento de modelos
- [ ] Tooltips nos botoes do Canone

### 6.2 Acessibilidade
- [ ] Suporte a screen readers
- [ ] Contraste de cores WCAG AA
- [ ] Navegacao por teclado completa

### 6.3 Documentacao
- [ ] Tutorial de primeira execucao
- [ ] Guia de troubleshooting
- [ ] FAQ com problemas comuns

### 6.4 DevOps
- [ ] GitHub Actions para testes automaticos
- [ ] Release automatico com changelog
- [ ] Docker image publicada

---

## 7. ARQUIVOS OBSOLETOS REMOVIDOS

Lista de arquivos removidos nesta limpeza:
- `dev-journey/05-future/PENDENCIAS_AUDITORIA.md` -> consolidado aqui
- `src/soul/consciencia.py.backup` -> backup obsoleto
- `src/assets/panteao/entities/juno/templo_de_lars.css` -> arquivo duplicado no lugar errado

---

## COMO USAR ESTE DOCUMENTO

1. Marque `[x]` quando concluir uma tarefa
2. Atualize a data no topo
3. Mova itens concluidos para secao apropriada
4. Commit com: `docs: atualizar PENDENCIAS.md`

---

*Documento consolidado de pendencias do projeto Luna*
