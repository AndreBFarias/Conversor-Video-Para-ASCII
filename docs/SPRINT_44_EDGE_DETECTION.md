# Sprint 44: Edge Detection - Correcao de Edge Boost e Edge Chars

**Prioridade:** ALTA
**Resolve:** Edge Boost inverte qualidade, Edge Chars perde luminancia, nada funciona para Pixel Art
**Dependencia:** Nenhuma (independente das Sprints 42 e 43)

## Objetivo

Corrigir o Edge Boost para que bordas fiquem MAIS densas (caracteres pesados como `$@#`), corrigir o Edge Chars para preservar informacao de luminancia, e aplicar edge detection tambem ao modo Pixel Art.

## Contexto

### Bug do Edge Boost

O Edge Boost ADICIONA brilho nas bordas (`brightness + edge_boost_amount`). Isso empurra o indice da rampa para o FIM (caracteres leves como `. ` ou espaco), tornando as bordas INVISIVEIS ao inves de mais definidas.

A rampa padrao vai de denso (indice 0 = `$`) a leve (indice N = ` `):
- Pixel com brilho 50, rampa de 5 chars: indice = (50/255)*4 = 0.78 -> `=`
- Com boost +100: indice = (150/255)*4 = 2.35 -> `.`
- A borda ficou MENOS visivel

**Correcao:** SUBTRAIR brilho para empurrar para caracteres MAIS DENSOS. Usar intensidade RELATIVA ao comprimento da rampa.

### Bug do Edge Chars

O Edge Chars substitui TODO pixel de borda por `/|\-` baseado no angulo do gradiente. Isso:
1. Perde TODA informacao de luminancia
2. Cria um mapa de contorno puro que destroi a arte ASCII subjacente
3. Nao respeita a intensidade da borda (edges fracos e fortes ficam iguais)

**Correcao:** Usar edge chars APENAS para bordas fortes (magnitude > 2x threshold), e escolher o caractere de borda com a cor do pixel original preservada (ja faz isso). Para bordas medias, manter o caractere da rampa.

### Pixel Art sem Edge Detection

O modo Pixel Art ignora completamente edge detection. Cores quantizadas perdem definicao nas bordas (bordas borradas).

**Correcao:** Aplicar edge-aware sharpening ANTES da quantizacao de cores. Usar Sobel para detectar bordas e aumentar contraste local nesses pontos.

## Arquivos a Modificar

### Grupo 1: Funcao central (afeta TODOS os converters)
- `src/core/utils/ascii_converter.py` -- funcao `converter_frame_para_ascii`

### Grupo 2: Calibrador (rendering em tempo real)
- `src/core/gtk_calibrator.py` -- metodos `_render_ascii_to_image` e `_render_pixelart_to_image`

### Grupo 3: Converters de producao
- `src/core/converter.py`
- `src/core/mp4_converter.py`
- `src/core/gif_converter.py`
- `src/core/html_converter.py`
- `src/core/png_converter.py`
- `src/core/realtime_ascii.py`
- `src/core/gtk_fullscreen_player.py`
- `src/app/actions/preview_actions.py`

### Grupo 4: Pixel Art
- `src/core/gtk_calibrator.py` -- metodo `_render_pixelart_to_image`
- `src/core/pixel_art_converter.py` -- funcao `converter_frame_para_pixelart`

## Tarefas

### 44.1 - Corrigir Edge Boost em ascii_converter.py (funcao central)

**Arquivo:** `src/core/utils/ascii_converter.py`

Localizar o bloco (linhas 27-31):
```python
if edge_boost_enabled:
    brightness = gray_frame.astype(np.int32)
    edge_boost = is_edge.astype(np.int32) * edge_boost_amount
    brightness = np.clip(brightness + edge_boost, 0, 255)
    lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
```

Substituir por:
```python
if edge_boost_enabled:
    brightness = gray_frame.astype(np.int32)
    boost_normalized = int(edge_boost_amount * ramp_len / 70)
    pixel_boost = boost_normalized * 255 // ramp_len
    edge_darkening = is_edge.astype(np.int32) * pixel_boost
    brightness = np.clip(brightness - edge_darkening, 0, 255)
    lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
```

**Explicacao da logica:**
- `boost_normalized`: normaliza o amount relativo a uma rampa de 70 chars (a padrao). Uma rampa de 5 chars precisa de muito menos shift que uma de 70
- `pixel_boost`: converte o shift de indices em shift de brilho
- `brightness - edge_darkening`: SUBTRAI para escurecer bordas = caracteres mais densos

### 44.2 - Corrigir Edge Chars em ascii_converter.py

**Arquivo:** `src/core/utils/ascii_converter.py`

Localizar o bloco (linhas 37-53):
```python
if use_edge_chars:
    angle_degrees = angle_frame * (180 / np.pi)
    angle_degrees = (angle_degrees + 180) % 180

    slash_mask = is_edge & (...)
    pipe_mask = is_edge & (...)
    backslash_mask = is_edge & (...)
    dash_mask = is_edge & ~(...)

    chars[slash_mask] = '/'
    chars[pipe_mask] = '|'
    chars[backslash_mask] = '\\'
    chars[dash_mask] = '-'
```

Substituir por:
```python
if use_edge_chars:
    strong_edge = magnitude_frame > (sobel_threshold * 2)

    angle_degrees = angle_frame * (180 / np.pi)
    angle_degrees = (angle_degrees + 180) % 180

    slash_mask = strong_edge & (((angle_degrees >= 22.5) & (angle_degrees < 67.5)) |
                                ((angle_degrees >= 157.5) & (angle_degrees < 202.5)))
    pipe_mask = strong_edge & (((angle_degrees >= 67.5) & (angle_degrees < 112.5)) |
                               ((angle_degrees >= 247.5) & (angle_degrees < 292.5)))
    backslash_mask = strong_edge & (((angle_degrees >= 112.5) & (angle_degrees < 157.5)) |
                                    ((angle_degrees >= 292.5) & (angle_degrees < 337.5)))
    dash_mask = strong_edge & ~(slash_mask | pipe_mask | backslash_mask)

    chars[slash_mask] = '/'
    chars[pipe_mask] = '|'
    chars[backslash_mask] = '\\'
    chars[dash_mask] = '-'
```

**Mudanca chave:** `is_edge` -> `strong_edge` (magnitude > 2x threshold). Isso faz com que APENAS bordas muito fortes recebam caracteres direcionais. Bordas medias mantem o caractere baseado em luminancia.

### 44.3 - Replicar correcoes no calibrador (render ASCII)

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `_render_ascii_to_image` (linha 894), aplicar as MESMAS correcoes:

**Edge Boost** (linhas 933-937):
```python
# DE:
if self.edge_boost_enabled:
    brightness = resized_gray.astype(np.int32)
    edge_boost = is_edge.astype(np.int32) * self.edge_boost_amount
    brightness = np.clip(brightness + edge_boost, 0, 255)
    lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)

# PARA:
if self.edge_boost_enabled:
    brightness = resized_gray.astype(np.int32)
    boost_normalized = int(self.edge_boost_amount * ramp_len / 70)
    pixel_boost = boost_normalized * 255 // ramp_len
    edge_darkening = is_edge.astype(np.int32) * pixel_boost
    brightness = np.clip(brightness - edge_darkening, 0, 255)
    lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
```

**Edge Chars** (linhas 957-965):
```python
# DE:
if self.use_edge_chars and mag > sobel_threshold:

# PARA:
if self.use_edge_chars and mag > (sobel_threshold * 2):
```

### 44.4 - Replicar correcoes nos converters de producao

Aplicar a MESMA logica de correcao do Edge Boost (subtrair ao inves de adicionar, normalizar por ramp_len) nos seguintes arquivos. Todos tem o mesmo padrao `brightness + edge_boost`:

1. **`src/core/realtime_ascii.py`** (linhas 57-60):
   ```python
   # Mesmo pattern: brightness - edge_darkening com normalizacao
   ```

2. **`src/core/gtk_fullscreen_player.py`** (linhas 351-355):
   ```python
   # Mesmo pattern
   ```

3. **`src/app/actions/preview_actions.py`** (linhas 150-154):
   ```python
   # Mesmo pattern
   ```

**NOTA:** Os converters `converter.py`, `mp4_converter.py`, `gif_converter.py`, `html_converter.py`, `png_converter.py` chamam a funcao central `converter_frame_para_ascii` de `ascii_converter.py`, entao a correcao da tarefa 44.1 ja os cobre automaticamente. NAO modificar esses arquivos.

**Verificar:** `realtime_ascii.py` e `gtk_fullscreen_player.py` tem implementacao INLINE do edge boost (nao usam a funcao central). Esses SIM precisam ser atualizados manualmente.

### 44.5 - Adicionar Edge Detection ao Pixel Art (calibrador)

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `_render_pixelart_to_image` (linha 980), adicionar edge-aware sharpening ANTES da quantizacao:

```python
def _render_pixelart_to_image(self, resized_color, resized_mask, frame_h, frame_w) -> np.ndarray:
    n_colors = self.pixel_art_config.get('color_palette_size', 16)
    use_fixed = self.pixel_art_config.get('use_fixed_palette', False)
    palette_name = self.pixel_art_config.get('fixed_palette_name', None)

    custom_palette = None
    if use_fixed and palette_name and palette_name in FIXED_PALETTES:
        custom_palette = FIXED_PALETTES[palette_name]['colors']

    height, width = resized_color.shape[:2]

    color_for_quant = resized_color.copy()

    if self.edge_boost_enabled:
        gray = cv2.cvtColor(resized_color, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        edge_mask = magnitude_norm > self.converter_config.get('sobel_threshold', 20)
        darken_factor = max(0.3, 1.0 - (self.edge_boost_amount / 255.0))
        color_for_quant[edge_mask] = (color_for_quant[edge_mask] * darken_factor).astype(np.uint8)

    try:
        quantized = quantize_colors(color_for_quant, n_colors, use_fixed_palette=use_fixed, custom_palette=custom_palette)
    except Exception:
        quantized = color_for_quant

    # ... resto do metodo permanece igual
```

**Explicacao:** Em pixel art, nao ha caracteres ASCII para manipular. O edge boost escurece as bordas ANTES da quantizacao, criando linhas de definicao naturais que sobrevivem a reducao de cores.

### 44.6 - Adicionar Edge Detection ao pixel_art_converter.py

**Arquivo:** `src/core/pixel_art_converter.py`

Na funcao `converter_frame_para_pixelart` (linha 59), adicionar o mesmo edge-aware processing ANTES de `quantize_colors`:

```python
def converter_frame_para_pixelart(frame, mask, pixel_size, n_colors, use_fixed_palette,
                                   edge_boost_enabled=False, edge_boost_amount=100,
                                   sobel_threshold=20):
    h, w = frame.shape[:2]

    if pixel_size > 1:
        small_h = max(1, h // pixel_size)
        small_w = max(1, w // pixel_size)
        frame_small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
        mask_small = cv2.resize(mask, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
    else:
        frame_small = frame
        mask_small = mask

    color_for_quant = frame_small.copy()

    if edge_boost_enabled:
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        edge_mask = magnitude_norm > sobel_threshold
        darken_factor = max(0.3, 1.0 - (edge_boost_amount / 255.0))
        color_for_quant[edge_mask] = (color_for_quant[edge_mask] * darken_factor).astype(np.uint8)

    quantized = quantize_colors(color_for_quant, n_colors, use_fixed_palette)
    # ... resto continua igual
```

Na funcao `iniciar_conversao`, ler edge_boost_enabled/amount/sobel_threshold do config e passar para `converter_frame_para_pixelart`.

### 44.7 - Atualizar label de status do Edge Boost

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `on_edge_boost_changed` (linha 1805), atualizar o status para indicar a nova semantica:

```python
# DE:
status = "Edge Boost: Ativado" if self.edge_boost_enabled else "Edge Boost: Desativado"

# PARA:
status = "Edge Boost: Ativado (bordas densas)" if self.edge_boost_enabled else "Edge Boost: Desativado"
```

## Mapa de Propagacao

Para garantir consistencia, segue a lista COMPLETA de onde edge boost/chars e implementado e o que fazer:

| Arquivo | Tipo | Acao |
|---------|------|------|
| `src/core/utils/ascii_converter.py` | Funcao central | **CORRIGIR** (44.1 + 44.2) |
| `src/core/gtk_calibrator.py` (_render_ascii) | Inline | **CORRIGIR** (44.3) |
| `src/core/gtk_calibrator.py` (_render_pixelart) | Inline | **ADICIONAR** (44.5) |
| `src/core/realtime_ascii.py` | Inline | **CORRIGIR** (44.4) |
| `src/core/gtk_fullscreen_player.py` | Inline | **CORRIGIR** (44.4) |
| `src/app/actions/preview_actions.py` | Inline | **CORRIGIR** (44.4) |
| `src/core/converter.py` | Usa funcao central | Nenhuma (coberto por 44.1) |
| `src/core/mp4_converter.py` | Usa funcao central | Nenhuma |
| `src/core/gif_converter.py` | Usa funcao central | Nenhuma |
| `src/core/html_converter.py` | Usa funcao central | Nenhuma |
| `src/core/png_converter.py` | Usa funcao central | Nenhuma |
| `src/core/pixel_art_converter.py` | Sem edge | **ADICIONAR** (44.6) |
| `src/core/gpu_converter.py` | Sem edge | Nenhuma (path GPU separado) |
| `src/core/async_gpu_converter.py` | Sem edge | Nenhuma (path GPU separado) |

## Verificacao

### Teste Visual (Calibrador)

```bash
python src/core/gtk_calibrator.py --config config.ini --video data_input/Luna_flertando.mp4
```

1. **Sem Edge Boost/Chars:** Verificar que o resultado e identico ao atual
2. **Com Edge Boost ativado:**
   - Bordas devem ficar com caracteres MAIS DENSOS (como `$@#M`)
   - A imagem geral deve ficar MAIS DEFINIDA, nao lavada
   - Testar com rampa Minimalista (5 chars) -- deve funcionar bem
   - Testar com rampa Padrao (70 chars) -- boost sutil mas visivel
3. **Com Edge Chars ativado:**
   - APENAS bordas fortes devem ter caracteres direcionais `/|\-`
   - Areas de borda media devem manter caracteres de luminancia
   - O resultado deve parecer "ASCII art com contornos", nao "mapa de contornos"
4. **Modo Pixel Art com Edge Boost:**
   - Bordas entre regioes de cores diferentes devem ficar mais escuras/definidas
   - A quantizacao nao deve borrar as transicoes

### Teste de Conversao

```bash
python cli.py convert --video data_input/Luna_flertando.mp4 --format mp4 --no-gpu
python cli.py validate --video data_input/Luna_flertando.mp4
```
