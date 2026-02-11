# Referencia de Configuracao (config.ini)

Documentacao completa de todas as opcoes do arquivo `config.ini`.

## [Conversor]

Configuracoes do motor de conversao ASCII.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `luminance_ramp` | string | (70 chars) | Caracteres usados para representar luminosidade |
| `luminance_preset` | string | standard | ID do preset de rampa (standard, simple, blocks, etc.) |
| `target_width` | int | 120 | Largura em caracteres (40-400) |
| `target_height` | int | 0 | Altura em caracteres (0 = automatico) |
| `sobel_threshold` | int | 100 | Sensibilidade de deteccao de bordas (0-255) |
| `char_aspect_ratio` | float | 0.48 | Proporcao altura/largura do caractere (0.01-2.0) |
| `sharpen_enabled` | bool | true | Ativar filtro de nitidez |
| `sharpen_amount` | float | 0.5 | Intensidade da nitidez (0.0-1.0) |

## [Quality]

Presets de qualidade pre-definidos.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `preset` | string | custom | Nome do preset (custom, mobile, low, medium, high, veryhigh) |
| `player_zoom` | float | 0.7 | Zoom do terminal no player (0.5-1.0) |

### Valores dos Presets

| Preset | Width | Height | Aspect | Zoom |
|--------|-------|--------|--------|------|
| mobile | 100 | 25 | 0.50 | 1.0 |
| low | 120 | 30 | 0.50 | 0.9 |
| medium | 180 | 45 | 0.48 | 0.7 |
| high | 240 | 60 | 0.45 | 0.6 |
| veryhigh | 300 | 75 | 0.42 | 0.5 |

## [Pastas]

Diretorios de entrada e saida.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `input_dir` | path | data_input | Pasta para videos/imagens de entrada |
| `output_dir` | path | data_output | Pasta para arquivos ASCII gerados |

## [Player]

Configuracoes do player de terminal.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `arquivo` | path | - | Ultimo arquivo reproduzido |
| `loop` | string | nao | Repetir animacao (sim/nao) |
| `clear_screen` | bool | true | Limpar tela antes de reproduzir |
| `show_fps` | bool | false | Mostrar contador de FPS |
| `speed` | string | 1.0 | Velocidade de reproducao (0.5, 0.75, 1.0, 1.25, 1.5, 2.0) |

## [Geral]

Configuracoes gerais da aplicacao.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `display_mode` | string | window | Modo de exibicao (terminal, window, both) |

## [ChromaKey]

Configuracoes do filtro de fundo verde.

| Opcao | Tipo | Range | Descricao |
|-------|------|-------|-----------|
| `h_min` | int | 0-179 | Matiz minimo (verde tipico: 35) |
| `h_max` | int | 0-179 | Matiz maximo (verde tipico: 85) |
| `s_min` | int | 0-255 | Saturacao minima |
| `s_max` | int | 0-255 | Saturacao maxima |
| `v_min` | int | 0-255 | Valor/brilho minimo |
| `v_max` | int | 0-255 | Valor/brilho maximo |
| `erode` | int | 0-10 | Iteracoes de erosao (remove ruido) |
| `dilate` | int | 0-10 | Iteracoes de dilatacao (fecha buracos) |

### Presets de Chroma Key

| Preset | H Min | H Max | S Min | V Min | Uso |
|--------|-------|-------|-------|-------|-----|
| Studio | 35 | 85 | 50 | 50 | Estudio profissional |
| Natural | 35 | 90 | 30 | 30 | Ambientes externos |
| Bright | 40 | 80 | 80 | 80 | Verde saturado |

## [Mode]

Configuracao do motor grafico.

| Opcao | Tipo | Valores | Descricao |
|-------|------|---------|-----------|
| `conversion_mode` | string | ascii, pixelart | Motor de conversao |

## [PixelArt]

Configuracoes especificas do modo Pixel Art.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `pixel_size` | int | 2 | Tamanho do pixel em pixels reais (1-16) |
| `color_palette_size` | int | 16 | Numero de cores na paleta (2-256) |
| `use_fixed_palette` | bool | false | Usar paleta fixa retro |
| `fixed_palette_name` | string | gameboy | Nome da paleta fixa |
| `pixel_scale` | float | 1.0 | Escala adicional do pixel |

### Presets de Bits

| Preset | Pixel Size | Palette Size | Estetica |
|--------|------------|--------------|----------|
| 8bit_low | 6 | 16 | Atari |
| 8bit_high | 5 | 16 | NES |
| 16bit_low | 3 | 128 | SNES |
| 16bit_high | 2 | 128 | Genesis |
| 32bit | 2 | 256 | PS1 |
| 64bit | 1 | 256 | N64 |

## [Output]

Configuracoes de saida.

| Opcao | Tipo | Valores | Descricao |
|-------|------|---------|-----------|
| `format` | string | txt, mp4, gif, html, png, png_all | Formato do arquivo de saida |
| `mp4_target_fps` | int | 1-60 | FPS alvo para conversao MP4 (padrao: 15) |

## [Preview]

Configuracoes de preview durante conversao.

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `preview_during_conversion` | bool | true | Mostrar thumbnail durante conversao |

---

## Exemplo Completo

```ini
[Conversor]
luminance_ramp = $@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'.
luminance_preset = standard
target_width = 180
target_height = 0
sobel_threshold = 100
char_aspect_ratio = 0.48
sharpen_enabled = true
sharpen_amount = 0.5

[Quality]
preset = medium
player_zoom = 0.7

[Pastas]
input_dir = data_input
output_dir = data_output

[Player]
loop = nao
clear_screen = true
show_fps = false
speed = 1.0

[Geral]
display_mode = window

[ChromaKey]
h_min = 35
h_max = 85
s_min = 40
s_max = 255
v_min = 40
v_max = 255
erode = 2
dilate = 2

[Mode]
conversion_mode = ascii

[PixelArt]
pixel_size = 2
color_palette_size = 16
use_fixed_palette = false
fixed_palette_name = gameboy

[Output]
format = txt
```

---

## Localizacao do Arquivo

O arquivo `config.ini` fica na raiz do projeto:
```
Conversor-Video-Para-ASCII/
  config.ini    <-- aqui
  main.py
  src/
  ...
```

Alteracoes feitas pela interface sao salvas automaticamente.
