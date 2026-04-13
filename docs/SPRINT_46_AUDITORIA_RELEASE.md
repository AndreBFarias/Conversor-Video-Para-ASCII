# Sprint 46: Auditoria Final e Release v2.7.0

**Prioridade:** CRITICA
**Resolve:** Validacao completa, release em todos os formatos, publicacao no GitHub
**Dependencia:** Sprints 42, 43, 44 e 45 (executar POR ULTIMO)

## Objetivo

Auditoria completa de todas as mudancas, validacao end-to-end, build dos pacotes de release e publicacao no GitHub.

## Tarefas

### 46.1 - Auditoria de Codigo: Sincronizacao N-para-N

Verificar que TODAS as instancias de edge boost/chars foram atualizadas consistentemente.

**Verificacao obrigatoria:**

```bash
grep -rn "brightness + edge" src/ --include="*.py"
grep -rn "brightness \+ edge" src/ --include="*.py"
```

**Resultado esperado:** ZERO matches. Se algum `+ edge` ainda existir, e uma regressao.

```bash
grep -rn "is_edge" src/ --include="*.py" | grep -v "strong_edge" | grep -v "__pycache__"
```

**Resultado esperado:** Nenhum `is_edge` usado em edge_chars (todos devem usar `strong_edge` ou `magnitude > 2x threshold`).

### 46.2 - Auditoria de Codigo: Rampas

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from src.app.constants import LUMINANCE_RAMPS
errors = []
for name, data in LUMINANCE_RAMPS.items():
    ramp = data['ramp']
    if len(ramp) < 4:
        errors.append(f'{name}: muito curta ({len(ramp)} chars)')
    if ramp[-1] != ' ':
        errors.append(f'{name}: nao termina com espaco')
    if name == 'detailed':
        errors.append(f'{name}: deveria ter sido removida')
if errors:
    for e in errors: print(f'ERRO: {e}')
    sys.exit(1)
else:
    for name, data in LUMINANCE_RAMPS.items():
        print(f'OK: {name} ({len(data[\"ramp\"])} chars)')
    print('Todas as rampas validadas')
"
```

### 46.3 - Auditoria de UI: Glade

```bash
grep -c "ORIGINAL\|RESULTADO\|MÁSCARA" src/gui/calibrator.glade
```
**Resultado esperado:** 0 (todos renomeados para ORIGEM/PROCESSAMENTO/DESTINO)

```bash
grep -c "btn_preset_studio\|btn_preset_natural\|btn_preset_bright\|btn_auto_detect\|btn_reset" src/gui/calibrator.glade
```
**Resultado esperado:** 0 (todos removidos)

```bash
grep -c "detailed" src/gui/calibrator.glade
```
**Resultado esperado:** 0 (rampa detalhado removida do combo)

### 46.4 - Auditoria de Docs

Verificar que NENHUM doc referencia features removidas:

```bash
grep -rn "Studio\|Natural\|Bright" docs/CONFIG_REFERENCE.md docs/USER_MANUAL.md docs/PRESETS_REFERENCE.md
grep -rn "Detalhado" docs/PRESETS_REFERENCE.md
```
**Resultado esperado:** 0 matches (exceto em contexto historico como CHANGELOG)

### 46.5 - Teste Funcional: Calibrador

```bash
python src/core/gtk_calibrator.py --config config.ini --video data_input/Luna_flertando.mp4
```

**Checklist manual:**
- [ ] Janelas na ordem: Origem | Processamento | Destino
- [ ] Presets Studio/Natural/Bright NAO aparecem
- [ ] Botoes Auto/Reset NAO aparecem
- [ ] Atalhos S, T, Q funcionam
- [ ] Cada rampa no combo funciona e produz resultado visual diferente
- [ ] Blocos Unicode renderizam como blocos solidos
- [ ] Setas/Simbolos renderizam com formas geometricas
- [ ] Edge Boost ativado: bordas ficam MAIS DENSAS (caracteres pesados)
- [ ] Edge Boost com rampa Minimalista: resultado visivelmente melhor
- [ ] Edge Chars ativado: contornos SUTIS preservando luminancia
- [ ] Modo Pixel Art: funciona normalmente
- [ ] Pixel Art + Edge Boost: bordas mais definidas
- [ ] Auto Seg funciona normalmente
- [ ] Duplo clique no resultado abre fullscreen
- [ ] Fullscreen tem overlay de controles
- [ ] Fechar fullscreen VOLTA ao calibrador (nao fecha tudo)

### 46.6 - Teste Funcional: Conversao

```bash
python cli.py validate --video data_input/Luna_flertando.mp4
python cli.py convert --video data_input/Luna_flertando.mp4 --format mp4 --no-gpu
```

- [ ] Validate passa sem erros
- [ ] Conversao MP4 completa
- [ ] Video resultante tem bordas definidas (se edge boost ativado)

### 46.7 - Teste de Regressao: Pre-commit Hook

```bash
git diff --cached -- src/core/ | head -50
```

Verificar que o pre-commit hook nao bloqueia o commit (encoding, tune animation, etc.)

### 46.8 - Verificacao de Versao

```bash
grep -r "2.7.0" pyproject.toml README.md docs/CHANGELOG.md CHANGELOG.md
```
**Resultado esperado:** Versao 2.7.0 presente em todos os arquivos

### 46.9 - Build de Release

```bash
cd packaging
./build-deb.sh
./build-appimage.sh
```

Verificar que os pacotes foram gerados sem erros.

### 46.10 - Commit e Tag

```bash
git add -A
git commit -m "release: v2.7.0 - calibrador UI, rampas e edge detection corrigidos"
git tag v2.7.0
```

### 46.11 - Publicacao no GitHub

```bash
gh release create v2.7.0 \
  --title "v2.7.0 - Calibrador UI, Rampas e Edge Detection" \
  --notes-file docs/CHANGELOG.md \
  packaging/extase-em-4r73_2.7.0_all.deb \
  packaging/Extase_em_4R73-2.7.0-x86_64.AppImage
```

### 46.12 - Fechar Issues

```bash
gh issue close 3 --comment "Implementado na Sprint 42"
gh issue close 4 --comment "Implementado na Sprint 43"
gh issue close 5 --comment "Implementado na Sprint 44"
gh issue close 6 --comment "Implementado na Sprint 45"
gh issue close 7 --comment "Auditoria e release v2.7.0 completos"
```

## Checklist Pre-Release

- [ ] Zero `brightness + edge` no codigo
- [ ] Zero rampas com menos de 4 chars
- [ ] Zero referencias a ORIGINAL/RESULTADO/MASCARA no glade
- [ ] Zero referencias a Studio/Natural/Bright nos docs ativos
- [ ] Testes visuais passando (calibrador)
- [ ] Conversao MP4 funcional
- [ ] Validate passando
- [ ] Versao 2.7.0 em todos os lugares
- [ ] CHANGELOG sincronizado em todos os formatos
- [ ] Pacotes DEB e AppImage gerados
- [ ] Tag v2.7.0 criada
- [ ] Release publicado no GitHub
- [ ] Issues fechadas
