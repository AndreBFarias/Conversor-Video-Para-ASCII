# Sprint 43: Rampas de Luminancia - Correcao e Expansao

**Prioridade:** MEDIA
**Resolve:** Rampas unicode quebradas, rampas curtas demais, redundancias
**Dependencia:** Nenhuma (independente da Sprint 42)

## Objetivo

Restaurar rampas unicode que perderam caracteres no commit 622739c, expandir rampas muito curtas para melhor qualidade visual, e eliminar redundancias.

## Contexto

As rampas de luminancia mapeiam brilho (0-255) para caracteres ASCII. Uma rampa curta (2-3 chars) gera imagens com pouquissima variacao visual. O commit 622739c apagou os caracteres unicode de `blocks` e `arrows`, transformando-as em strings de espacos.

Valores atuais vs originais (runtime verificado):
- `blocks`: `" "` (1 char: espaco) -- original era `"█▓▒░ "` (5 chars)
- `arrows`: `"  "` (2 chars: espacos) -- original era `"■□·  "` (11 chars)
- `dots`: `". "` (2 chars) -- muito curta
- `binary`: `"10 "` (3 chars) -- funcional mas limitada
- `letters`: `"MWNXK0Okxdolc:;,'...  "` (22 chars) -- tem 3 pontos repetidos e 2 espacos no fim
- `detailed`: quase identica a `standard` (so adicionou `%` antes do `8`)

## Tarefas

### 43.1 - Restaurar rampas unicode quebradas

**Arquivo:** `src/app/constants.py`

Substituir as rampas `blocks` e `arrows` pelos valores originais:

```python
'blocks': {
    'name': 'Blocos Unicode',
    'ramp': "\u2588\u2593\u2592\u2591 "
},
```

```python
'arrows': {
    'name': 'Setas/Simbolos',
    'ramp': "\u25bc\u25b2\u25ba\u25c4\u25a0\u25a1\u25cf\u25cb\u00b7  "
},
```

**IMPORTANTE:** Usar escapes unicode (`\uXXXX`) ao inves de caracteres literais para evitar que o mesmo problema de encoding aconteca novamente. Os caracteres sao:
- `\u2588` = `█` (FULL BLOCK)
- `\u2593` = `▓` (DARK SHADE)
- `\u2592` = `▒` (MEDIUM SHADE)
- `\u2591` = `░` (LIGHT SHADE)
- `\u25bc` = `` (BLACK DOWN-POINTING TRIANGLE)
- `\u25b2` = `` (BLACK UP-POINTING TRIANGLE)
- `\u25ba` = `` (BLACK RIGHT-POINTING POINTER)
- `\u25c4` = `` (BLACK LEFT-POINTING POINTER)
- `\u25a0` = `■` (BLACK SQUARE)
- `\u25a1` = `□` (WHITE SQUARE)
- `\u25cf` = `` (BLACK CIRCLE)
- `\u25cb` = `` (WHITE CIRCLE)
- `\u00b7` = `·` (MIDDLE DOT)

### 43.2 - Expandir rampa dots

**Arquivo:** `src/app/constants.py`

A rampa `dots` tem so 2 chars (`. `). Expandir com variacao de pontos unicode para gradientes mais ricos:

```python
'dots': {
    'name': 'Pontos',
    'ramp': "\u2022\u25cf\u25c9\u25ce\u25c6\u00b7\u2219\u00b0. "
},
```

Caracteres:
- `\u2022` = `•` (BULLET) -- mais denso
- `\u25cf` = `` (BLACK CIRCLE)
- `\u25c9` = `` (FISHEYE)
- `\u25ce` = `` (BULLSEYE)
- `\u25c6` = `` (BLACK DIAMOND)
- `\u00b7` = `·` (MIDDLE DOT)
- `\u2219` = `∙` (BULLET OPERATOR)
- `\u00b0` = `°` (DEGREE SIGN) -- mais leve

### 43.3 - Expandir rampa binary

**Arquivo:** `src/app/constants.py`

A rampa `binary` tem so 3 chars (`10 `). Expandir mantendo a estetica binaria:

```python
'binary': {
    'name': 'Binario (Matrix)',
    'ramp': "10!|:. "
},
```

### 43.4 - Corrigir rampa letters

**Arquivo:** `src/app/constants.py`

A rampa `letters` tem caracteres repetidos (`...  `). Corrigir para gradiente limpo de letras por peso visual:

```python
'letters': {
    'name': 'Letras',
    'ramp': "MWNXKOkxdolc;:,. "
},
```

Remover: `0` (numero, nao letra), duplicatas de `.` e espaco extra.

### 43.5 - Remover rampa detailed (redundante)

**Arquivo:** `src/app/constants.py`

A rampa `detailed` e quase identica a `standard`:
- standard: `$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'. `
- detailed: `$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'. `

Unica diferenca: `%` adicionado antes do `8`. Nao justifica uma rampa separada.

**Acao:** Remover a entrada `'detailed'` do dicionario `LUMINANCE_RAMPS`.

**Arquivo:** `src/gui/calibrator.glade`

Remover o item `Detalhado` do combo `combo_ramp_preset` (linha 357 aproximadamente):
```xml
<item id="detailed">Detalhado</item>
```

### 43.6 - Atualizar nomes das rampas no combo do Glade

**Arquivo:** `src/gui/calibrator.glade`

Atualizar os nomes exibidos no combo para refletir as mudancas:
- `dots`: De `Pontos` para `Pontos (10)` (refletindo novo tamanho)
- `binary`: De `Binario (Matrix)` para manter como esta (ou `Binario (7)`)

O combo completo deve ficar (linha 357, dentro de `combo_ramp_preset`):
```xml
<items>
  <item id="standard">Padrao (70)</item>
  <item id="simple">Simples (10)</item>
  <item id="blocks">Blocos</item>
  <item id="minimal">Minimalista</item>
  <item id="binary">Binario</item>
  <item id="dots">Pontos</item>
  <item id="letters">Letras</item>
  <item id="numbers">Numeros</item>
  <item id="arrows">Setas</item>
</items>
```

## Verificacao

1. Executar teste de sanidade:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, '.')
   from src.app.constants import LUMINANCE_RAMPS
   for name, data in LUMINANCE_RAMPS.items():
       ramp = data['ramp']
       print(f'{name}: len={len(ramp)}, chars={repr(ramp)}')
       assert len(ramp) >= 4, f'Rampa {name} muito curta: {len(ramp)} chars'
       assert ramp[-1] == ' ', f'Rampa {name} nao termina com espaco'
   print('Todas as rampas OK')
   "
   ```

2. Abrir o calibrador e testar cada rampa no combo:
   ```bash
   python src/core/gtk_calibrator.py --config config.ini --video data_input/Luna_flertando.mp4
   ```
   - Selecionar cada rampa e verificar que o resultado ASCII muda visualmente
   - Blocos Unicode devem renderizar como blocos solidos de gradiente
   - Setas devem renderizar com simbolos geometricos variados

3. Verificar que `detailed` nao aparece mais no combo
