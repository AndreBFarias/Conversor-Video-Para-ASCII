# Sprint 32: Qualidade e Integracao de Pipeline

**Status:** CONCLUIDA
**Prioridade:** CRITICA
**Dependencias:** Nenhuma (pode ser executado em paralelo com Sprint 31)
**Estimativa de Complexidade:** Media

---

## 1. PROBLEMA

A qualidade das conversoes ASCII caiu significativamente em relacao a versoes anteriores. Varios bugs e inconsistencias entre os pipelines de conversao foram identificados.

**Sintomas:**
- ASCII art com pouco detalhe e contraste insuficiente
- Features do calibrador (PostFX, Matrix Rain, render_mode) nao se refletem na conversao final
- Resultado visual diferente entre calibrador, realtime e conversao offline

---

## 2. BUGS IDENTIFICADOS

### Bug 2.1: Inversao de Rampa no Real-Time (CRITICO)

**Arquivo:** `src/core/realtime_ascii.py` linha 286
**Codigo com bug:**
```python
luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')[::-1]
```

**Problema:** O `[::-1]` INVERTE a rampa de luminancia. A rampa padrao vai de denso (`$@B8`) para leve (`. `). Invertida, pixels escuros recebem caracteres leves e vice-versa.

**Comparacao:**
- `converter.py:42` - `luminance_ramp.rstrip('|')` - SEM inversao (CORRETO)
- `gtk_calibrator.py:271` - `self.config.get(...).rstrip('|')` - SEM inversao (CORRETO)
- `realtime_ascii.py:286` - `.rstrip('|')[::-1]` - COM inversao (BUG)

**Correcao:**
```python
luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
```
Remover `[::-1]`.

---

### Bug 2.2: Dupla Mascara no Converter (MEDIO)

**Arquivo:** `src/core/converter.py` linhas 216-220 e depois linhas 239-245

**Problema:** O converter aplica render_mode zerando pixels no frame de cor:
```python
# Linha 216-219: Zera pixels na imagem de cor
if render_mode == 'user':
    resized_color[resized_mask > 127] = 0
elif render_mode == 'background':
    resized_color[resized_mask < 128] = 0
```

E DEPOIS passa `resized_mask` para `converter_frame_para_ascii()`:
```python
# Linha 239-245: converter_frame_para_ascii TAMBEM mascara
frame_ascii = converter_frame_para_ascii(
    resized_gray, resized_color, resized_mask, magnitude_norm, angle, ...
)
```

Dentro de `converter_frame_para_ascii()` (ascii_converter.py:56-58):
```python
is_masked = mask > 127
chars[is_masked] = ' '
ansi_codes[is_masked] = 232
```

**Resultado:** Dupla mascara. Os pixels ja zerados sao tambem substituidos por espaco. Isso nao eh necessariamente errado para `render_mode='both'`, mas para `user` e `background`, a mascara deveria ser ajustada para nao duplicar o efeito.

**Correcao:** Quando `render_mode` ja filtrou os pixels na cor, passar uma mascara vazia (ou ajustada) para `converter_frame_para_ascii`:

```python
# ANTES de chamar converter_frame_para_ascii:
if render_mode == 'user':
    resized_color[resized_mask > 127] = 0
    mask_for_ascii = resized_mask  # Mascara mantem: espaco onde chroma
elif render_mode == 'background':
    resized_color[resized_mask < 128] = 0
    mask_for_ascii = 255 - resized_mask  # Inverte: espaco onde user
else:
    mask_for_ascii = np.zeros_like(resized_mask)  # Sem mascara

frame_ascii = converter_frame_para_ascii(
    resized_gray, resized_color, mask_for_ascii, ...
)
```

---

### Bug 2.3: PostFX em Ordem Diferente (MEDIO)

**No calibrador** (`gtk_calibrator.py:1125-1177`):
```
1. Resize frame
2. Sobel (edge detection)
3. _render_ascii_to_image() -> imagem ASCII
4. Matrix Rain (na imagem renderizada)
5. PostFX (na imagem renderizada)
```
PostFX eh aplicado na IMAGEM ASCII final.

**No converter** (`converter.py:221-225`):
```
1. Resize frame
2. Aplicar render_mode nos pixels
3. PostFX nos PIXELS do frame (ANTES do Sobel!)
4. Temporal Coherence
5. Sobel
6. converter_frame_para_ascii() -> texto ASCII
```
PostFX eh aplicado nos PIXELS antes da conversao ASCII.

**Resultado:** PostFX no calibrador afeta a imagem visual (bloom, glitch na renderizacao). No converter, afeta os dados de entrada (muda os pixels antes da conversao). Bloom num pixel nao eh o mesmo que bloom no caractere ASCII.

**Correcao para converter.py:** Mover PostFX para DEPOIS da conversao (no formato file, isso significa aplicar ao reproduzir, nao ao converter). Mas como o formato .txt nao suporta PostFX embutido, a alternativa eh:

1. Para formato **txt**: NAO aplicar PostFX (sera aplicado no player ao reproduzir)
2. Para formato **MP4/GIF/HTML**: Aplicar PostFX na imagem renderizada (como o calibrador faz)

Para o converter.py (txt), remover PostFX do pipeline:
```python
# REMOVER estas linhas do converter.py (221-225):
# if postfx_processor is not None:
#     try:
#         resized_color = postfx_processor.process(resized_color)
#     except Exception:
#         pass
```

Para mp4_converter.py e gif_converter.py, PostFX deve ser aplicado DEPOIS de `render_ascii_as_image()`, na imagem final.

---

### Bug 2.4: Config Padrao Inadequado (BAIXO)

**Arquivo:** `config.ini`

**Problemas no config atual:**
```ini
luminance_ramp = MWNXK0Okxdolc:;,'...|    # 'letters' - apenas 20 chars
render_mode = background                    # So renderiza fundo!
edge_boost_enabled = false                  # Sem destaque de bordas
sobel_threshold = 10                        # Muito sensivel
```

**Config recomendado para qualidade superior:**
```ini
luminance_ramp = $@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'. |
render_mode = both
edge_boost_enabled = true
edge_boost_amount = 80
sobel_threshold = 30
```

**NOTA:** NAO alterar config.ini automaticamente. Documentar como restaurar qualidade. O usuario decide.

---

## 3. SOLUCAO DETALHADA

### 3.1 Corrigir Inversao de Rampa em realtime_ascii.py

**Arquivo:** `src/core/realtime_ascii.py`
**Linha:** 286
**Antes:**
```python
luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')[::-1]
```
**Depois:**
```python
luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
```

---

### 3.2 Corrigir Dupla Mascara em converter.py

**Arquivo:** `src/core/converter.py`
**Linhas:** 216-245

**Substituir bloco atual por:**
```python
        # Aplicar render_mode: filtrar pixels + ajustar mascara para ASCII
        if render_mode == 'user':
            resized_color[resized_mask > 127] = 0
            mask_for_ascii = resized_mask
        elif render_mode == 'background':
            resized_color[resized_mask < 128] = 0
            mask_for_ascii = 255 - resized_mask
        else:
            mask_for_ascii = np.zeros_like(resized_mask)

        if temporal_enabled and prev_gray_frame is not None:
            diff = np.abs(resized_gray.astype(np.int32) - prev_gray_frame.astype(np.int32))
            temporal_mask = diff < temporal_threshold
            resized_gray = np.where(temporal_mask, prev_gray_frame, resized_gray).astype(np.uint8)

        prev_gray_frame = resized_gray.copy()
        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        frame_ascii = converter_frame_para_ascii(
            resized_gray, resized_color, mask_for_ascii, magnitude_norm, angle, sobel_threshold, luminance_ramp,
            output_format="file",
            edge_boost_enabled=edge_boost_enabled,
            edge_boost_amount=edge_boost_amount,
            use_edge_chars=use_edge_chars
        )
        frames_ascii.append(frame_ascii)
```

**Remover PostFX do converter.py (txt):** Deletar linhas 221-225 (bloco `if postfx_processor`). PostFX no formato txt nao faz sentido pois modifica pixels de entrada, nao a saida visual.

---

### 3.3 Unificar Ordem de PostFX nos Conversores de Video (MP4/GIF/HTML)

Para `mp4_converter.py`, `gif_converter.py` e `html_converter.py`, verificar e garantir que PostFX seja aplicado na IMAGEM RENDERIZADA (apos converter frame para ASCII image), nao nos pixels de entrada.

**Padrao correto (igual ao calibrador):**
```
Frame -> Sharpen -> Resize -> Sobel -> render_ascii_to_image() -> Matrix Rain -> PostFX -> output
```

Abrir cada arquivo e verificar a ordem. Se PostFX estiver antes de `render_ascii_as_image()`, mover para depois.

---

### 3.4 Garantir que TODAS as Features do Calibrador Sao Aplicadas na Conversao

Criar checklist de features e verificar presenca em cada conversor:

| Feature | Calibrador | converter.py | realtime_ascii.py | mp4_converter | gpu_converter |
|---------|-----------|-------------|-------------------|---------------|--------------|
| Sharpen | Sim (L1076) | Sim (L212) | Sim (L348) | Verificar | Verificar |
| Sobel + Edge Chars | Sim (L1137) | Sim (L233) | Sim (L413) | Verificar | Verificar |
| Edge Boost | Sim (L938) | Sim (L239) | Sim (L291) | Verificar | Verificar |
| Render Mode | Sim (L952) | Sim (L216) | Sim (L370) | Verificar | Verificar |
| Auto Seg | Sim (L1088) | Sim (L189) | Sim (L353) | Verificar | Verificar |
| Temporal | Sim (L1149) | Sim (L227) | Sim (L406) | Verificar | Verificar |
| Matrix Rain | Sim (L1168) | NAO | Sim (L381) | Verificar | Verificar |
| PostFX | Sim (L1174) | REMOVER | Sim (L397) | Mover pos-render | Verificar |

Para cada "Verificar", abrir o arquivo e conferir. Se ausente, adicionar seguindo o padrao do converter.py.

---

## 4. ARQUIVOS A MODIFICAR

| Arquivo | Acao | O Que Fazer |
|---------|------|-------------|
| `src/core/realtime_ascii.py` | MODIFICAR | Remover `[::-1]` da rampa (linha 286) |
| `src/core/converter.py` | MODIFICAR | Corrigir dupla mascara (linhas 216-245), remover PostFX (linhas 221-225) |
| `src/core/mp4_converter.py` | VERIFICAR/MODIFICAR | Mover PostFX para pos-render se necessario |
| `src/core/gif_converter.py` | VERIFICAR/MODIFICAR | Mover PostFX para pos-render se necessario |
| `src/core/html_converter.py` | VERIFICAR/MODIFICAR | Mover PostFX para pos-render se necessario |
| `src/core/gpu_converter.py` | VERIFICAR/MODIFICAR | Verificar mesma ordem de pipeline |

---

## 5. CRITERIOS DE ACEITACAO

- [ ] realtime_ascii.py NAO inverte a rampa de luminancia (remover `[::-1]`)
- [ ] converter.py nao aplica dupla mascara (render_mode + mascara no ascii_converter)
- [ ] converter.py (formato txt) NAO aplica PostFX nos pixels de entrada
- [ ] mp4/gif/html converters aplicam PostFX na IMAGEM RENDERIZADA (pos-render)
- [ ] Todas as features do calibrador (Sharpen, Sobel, Edge Boost, Edge Chars, Render Mode, Auto Seg, Temporal) sao aplicadas em TODOS os conversores
- [ ] Pipeline do calibrador e dos conversores produzem resultado visual equivalente para mesmos parametros
- [ ] Converter video com rampa 'standard' (70 chars) produz resultado com alto detalhe
- [ ] Converter video com render_mode='both' mostra toda a cena (nao so fundo)

---

## 6. RISCOS E MITIGACOES

| Risco | Mitigacao |
|-------|-----------|
| Remover inversao de rampa pode mudar resultado para usuarios que se adaptaram | A inversao eh claramente um bug (discordante dos outros pipelines) |
| Remover PostFX do converter txt pode frustrar quem esperava PostFX embutido | PostFX visual nao tem como ser salvo em formato texto. Documentar |
| Mudar mascara pode afetar conversoes existentes | Testar com videos de chroma key antes/depois |
| Config atual do usuario tem render_mode=background | NAO alterar config automaticamente. Documentar como restaurar qualidade |

---

## 7. VERIFICACAO

```bash
# 1. Testar que rampa nao eh invertida no realtime
python3 src/core/realtime_ascii.py --config config.ini
# -> Verificar que areas escuras da cena usam caracteres densos ($@B8)
# -> Verificar que areas claras usam caracteres leves (:. )

# 2. Testar conversao com render_mode='both'
# Editar config.ini: render_mode = both
python3 src/core/converter.py --video /path/to/video.mp4 --config config.ini
# -> Abrir arquivo .txt gerado e verificar que toda a cena esta presente

# 3. Comparar calibrador vs conversao
# No calibrador, ajustar parametros e verificar preview
# Converter o mesmo video e comparar resultado visual

# 4. Testar cada conversor
python3 -c "
from src.core.converter import iniciar_conversao
import configparser
c = configparser.ConfigParser(interpolation=None)
c.read('config.ini')
iniciar_conversao('video.mp4', 'data_output', c)
"

# 5. Verificar que PostFX NAO esta aplicado no converter.py (txt)
# Ativar bloom no config.ini, converter para txt, verificar que o .txt
# nao tem bloom (bloom so aparece no player/preview)
```

---

## 8. REFERENCIA DE QUALIDADE

Para restaurar qualidade maxima, usar estes parametros no config.ini:

```ini
[Conversor]
luminance_ramp = $@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'. |
target_width = 120
target_height = 60
sobel_threshold = 30
char_aspect_ratio = 0.48
sharpen_enabled = true
sharpen_amount = 0.8
edge_boost_enabled = true
edge_boost_amount = 80
use_edge_chars = true
render_mode = both
```

A rampa 'standard' tem 70 caracteres (vs 20 da 'letters'), produzindo ASCII com muito mais detalhe e graduacao de tons.
