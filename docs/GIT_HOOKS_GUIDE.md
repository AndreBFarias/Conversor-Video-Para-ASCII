# Guia de Git Hooks - Extase em 4R73

## Visão Geral

Este projeto utiliza 3 git hooks para automatizar validações e linkagem de commits:

1. **pre-commit** - Valida código Python antes do commit
2. **commit-msg** - Valida formato da mensagem de commit
3. **post-commit** - Registra commit nas issues e atualiza documentação

---

## Hook 1: pre-commit [OK]

### Localização
`.git/hooks/pre-commit`

### Função
Valida sintaxe e qualidade do código Python antes de permitir commit.

### O Que Ele Faz

1. **Validação de Sintaxe Python**
   - Roda `python3 -m py_compile` em todos os arquivos `.py` staged
   - Se algum arquivo tiver erro de sintaxe, commit é BLOQUEADO

2. **Verificação de Imports**
   - Tenta importar `src.app.app.App`
   - Se falhar, mostra AVISO (não bloqueia)

3. **Verificação de Tamanho**
   - Avisa se algum arquivo `.py` tiver mais de 100KB
   - Não bloqueia commit

### Quando É Executado
Automaticamente antes de CADA commit.

### Como Desabilitar (não recomendado)
```bash
git commit --no-verify -m "mensagem"
```

### Output Exemplo

```
=== Pre-commit Hook: Extase em 4R73 ===
[1/3] Verificando sintaxe Python...
[OK] Sintaxe valida
[2/3] Verificando imports...
[OK] Imports verificados
[3/3] Verificando arquivos grandes...
[AVISO] Arquivo grande: src/core/gtk_calibrator.py (120000 bytes)
[OK] Tamanhos verificados
=== Pre-commit concluido ===
```

### Modificar Hook

Para adicionar novas validações:

```bash
vim .git/hooks/pre-commit
```

Exemplo: adicionar flake8

```bash
echo "[4/4] Rodando flake8..."
flake8 src/ --max-line-length=120
if [ $? -ne 0 ]; then
    echo "[ERRO] flake8 encontrou problemas"
    exit 1
fi
```

### Faz Sentido?
[OK] **SIM** - Essencial para evitar commits com código quebrado.

---

## Hook 2: commit-msg [OK]

### Localização
`.git/hooks/commit-msg`

### Função
Valida formato da mensagem de commit seguindo Conventional Commits e linkagem com issues/sprints.

### O Que Ele Faz

1. **Valida Conventional Commits**
   - Verifica se primeira linha segue padrão: `tipo: descrição`
   - Tipos válidos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`
   - Se não seguir, mostra AVISO (não bloqueia)

2. **Valida Linkagem com Issue**
   - Verifica se commit tem linha: `Resolves: Issue #X`
   - Se não tiver, mostra AVISO

3. **Valida Linkagem com Sprint**
   - Verifica se commit tem linha: `Sprint: X`
   - Se não tiver, mostra AVISO

4. **Verifica INDEX.md**
   - Avisa se INDEX.md não existir

### Quando É Executado
Automaticamente APÓS escrever mensagem de commit, ANTES de criar commit.

### Output Exemplo

**Commit Bom:**
```
=== Commit Message Hook: Extase em 4R73 ===
[OK] Mensagem de commit validada
```

**Commit Ruim:**
```
=== Commit Message Hook: Extase em 4R73 ===
[AVISO] Commit não segue Conventional Commits (feat|fix|refactor|docs|test|chore|style|perf)
Primeira linha: corrigir bug
[AVISO] Commit não referencia Issue (use 'Resolves: Issue #X')
[AVISO] Commit não referencia Sprint (use 'Sprint: X')
[OK] Mensagem de commit validada
```

### Template de Commit Message

```
feat: Implementar captura de área ASCII na gravação

- Adiciona função _get_ascii_area_geometry()
- Modifica comando ffmpeg para capturar apenas área do preview
- Otimiza FPS com preset veryfast e thread_queue_size
- Melhora qualidade de áudio (192k bitrate)

Resolves: Issue #2
Sprint: 2
```

### Faz Sentido?
[OK] **SIM** - Garante rastreabilidade e padronização de commits.

---

## Hook 3: post-commit [OK] (NOVO)

### Localização
`.git/hooks/post-commit`

### Função
Registra commit automaticamente nas issues e marca INDEX.md para atualização.

### O Que Ele Faz

1. **Extrai Metadados do Commit**
   - Hash do commit
   - Branch
   - Sprint (se presente)
   - Issue (se presente)

2. **Atualiza Arquivo de Issue**
   - Se commit tiver `Resolves: Issue #X`
   - Busca arquivo `Dev_log/Issue_00X_*.md`
   - Adiciona registro do commit no final do arquivo:
     ```markdown
     **Commit:** a1b2c3d
     **Branch:** dev
     **Data:** 2026-01-12 14:30:00
     ```

3. **Marca INDEX.md para Atualização**
   - Cria arquivo `.INDEX_NEEDS_UPDATE`
   - Lembra de revisar INDEX.md após commits

### Quando É Executado
Automaticamente APÓS criar commit.

### Output Exemplo

```
=== Post-Commit Hook: Extase em 4R73 ===
[INFO] Commit: a1b2c3d
[INFO] Branch: dev
[INFO] Sprint: 2
[INFO] Issue: #2
[INFO] Atualizando Dev_log/Issue_002_Sistema_Gravacao.md
[OK] Commit registrado em Dev_log/Issue_002_Sistema_Gravacao.md
[AVISO] INDEX.md pode estar desatualizado. Considere revisá-lo.
=== Post-commit concluído ===
```

### Faz Sentido?
[OK] **SIM** - Automatiza linkagem entre commits e issues, reduz trabalho manual.

---

## Fluxo Completo de Commit

### Passo a Passo

1. **Fazer Mudanças**
   ```bash
   vim src/core/gtk_calibrator.py
   ```

2. **Staged Changes**
   ```bash
   git add src/core/gtk_calibrator.py
   ```

3. **Tentar Commit**
   ```bash
   git commit
   ```

4. **pre-commit Hook Executa**
   - Valida sintaxe Python
   - Verifica imports
   - Verifica tamanho de arquivos
   - Se tudo OK, permite continuar
   - Se falhar, commit é BLOQUEADO

5. **Escrever Mensagem**
   ```
   feat: Capturar área ASCII na gravação MP4

   - Adiciona _get_ascii_area_geometry()
   - Otimiza comando ffmpeg

   Resolves: Issue #2
   Sprint: 2
   ```

6. **commit-msg Hook Executa**
   - Valida Conventional Commits
   - Valida linkagem com Issue
   - Valida linkagem com Sprint
   - Mostra avisos se algo estiver faltando
   - Permite commit (mesmo com avisos)

7. **Commit Criado**
   - Git cria commit com hash `a1b2c3d`

8. **post-commit Hook Executa**
   - Extrai Issue #2 da mensagem
   - Busca `Dev_log/Issue_002_Sistema_Gravacao.md`
   - Adiciona registro do commit no arquivo
   - Marca INDEX.md para revisão

### Resultado

- Commit criado
- Issue atualizada automaticamente
- Dev_log mantém histórico completo
- INDEX.md marcado para atualização

---

## Análise: Hooks Fazem Sentido?

### pre-commit [OK]
**Faz Sentido:** SIM

**Motivos:**
- Previne commits com código quebrado
- Detecta erros de sintaxe antes de subir
- Avisa sobre arquivos grandes
- Economiza tempo de CI/CD

**Manter:** SIM

### commit-msg [OK]
**Faz Sentido:** SIM

**Motivos:**
- Garante padronização de mensagens
- Força linkagem com issues/sprints
- Facilita navegação no histórico
- Melhora rastreabilidade

**Manter:** SIM

**Melhorias Possíveis:**
- BLOQUEAR commit se não tiver Issue/Sprint (atualmente apenas avisa)
- Validar se Issue existe em Dev_log/

### post-commit [OK] (NOVO)
**Faz Sentido:** SIM

**Motivos:**
- Automatiza linkagem commit → issue
- Reduz trabalho manual
- Mantém Dev_log atualizado
- Histórico completo de implementação

**Manter:** SIM

**Melhorias Possíveis:**
- Atualizar SPRINTS_REPORT.md automaticamente
- Gerar estatísticas de commits por sprint
- Notificar quando INDEX.md está muito desatualizado

---

## Workflows do GitHub Actions

### Arquivo: `.github/workflows/release.yml`

### O Que Faz

1. **Job: validate**
   - Roda em Ubuntu 22.04
   - Instala Python 3.10
   - Instala ruff (linter)
   - Valida código Python com ruff
   - Verifica sintaxe com py_compile

2. **Job: build-deb**
   - Depende de `validate`
   - Só roda em tags ou workflow_dispatch
   - Instala ImageMagick e dpkg-dev
   - Executa `packaging/build-deb.sh`
   - Faz upload do .deb como artifact

3. **Job: build-flatpak**
   - Depende de `validate`
   - Só roda em tags ou workflow_dispatch
   - Usa container GNOME 45
   - Prepara ícones com `prepare-icons.sh`
   - Builda Flatpak
   - Faz upload do .flatpak como artifact

4. **Job: release**
   - Depende de `build-deb` e `build-flatpak`
   - Só roda em tags
   - Baixa artifacts
   - Cria GitHub Release
   - Anexa .deb e .flatpak

### Triggers

- Push para `main` ou `dev`: só valida
- Push de tag `v*`: valida + build + release
- workflow_dispatch: permite rodar manualmente

### Faz Sentido?
[OK] **SIM** - Automatiza release e garante qualidade.

**Melhorias Possíveis:**
- Adicionar job de testes unitários
- Validar INDEX.md está atualizado
- Gerar changelog automaticamente

---

## Integração com CLAUDE.md

Os hooks se integram perfeitamente com o protocolo Luna:

1. **Commit Format**
   - Hook `commit-msg` valida
   - CLAUDE.md documenta formato esperado

2. **Linkagem Sprint-Issue**
   - Hook `post-commit` automatiza
   - CLAUDE.md explica fluxo

3. **Documentação**
   - Hook `post-commit` marca INDEX.md
   - CLAUDE.md exige atualização de docs

---

## Comandos Úteis

### Ver Hooks Instalados
```bash
ls -la .git/hooks/
```

### Testar Hook Manualmente
```bash
# pre-commit
.git/hooks/pre-commit

# commit-msg
echo "feat: teste" > .git/COMMIT_EDITMSG
.git/hooks/commit-msg .git/COMMIT_EDITMSG

# post-commit
.git/hooks/post-commit
```

### Desabilitar Todos os Hooks (temporário)
```bash
git commit --no-verify
```

### Reinstalar Hooks
```bash
# Tornar executáveis
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/post-commit
```

---

## Checklist de Hooks

- [x] pre-commit: Valida sintaxe Python
- [x] commit-msg: Valida formato de mensagem
- [x] post-commit: Registra commit em issues
- [ ] prepare-commit-msg: Template automático (futuro)
- [ ] pre-push: Valida testes antes de push (futuro)

---

**Última Atualização:** 2026-01-12
