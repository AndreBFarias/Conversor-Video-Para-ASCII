# CLI Unificado - Guia de Uso

CLI headless que espelha toda a funcionalidade da GUI GTK, sem dependencia de display.

## Ativacao

```bash
cd Conversor-Video-Para-ASCII
source venv/bin/activate
python cli.py <subcomando> [opcoes]
```

---

## Subcomandos

### `convert` - Conversao de video/imagem

```bash
python cli.py convert --video FILE [opcoes]
python cli.py convert --image FILE [opcoes]
```

| Flag | Tipo | Descricao |
|------|------|-----------|
| `--video FILE` | path | Video de entrada (mutuamente exclusivo com --image) |
| `--image FILE` | path | Imagem de entrada (mutuamente exclusivo com --video) |
| `--format` | txt/mp4/gif/html/png/png_all | Formato de saida |
| `--quality` | mobile/low/medium/high/veryhigh/custom | Preset de qualidade |
| `--mode` | ascii/pixelart | Modo de conversao |
| `--style` | clean/cyberpunk/retro/high_contrast | Preset de estilo |
| `--luminance` | standard/simple/blocks/minimal/binary/dots/detailed/letters/numbers/arrows | Rampa de luminancia |
| `--gpu / --no-gpu` | bool | Forcar GPU ou CPU |
| `--width N` | int | Largura em caracteres |
| `--height N` | int | Altura em caracteres |
| `--output DIR` | path | Diretorio de saida |
| `--config FILE` | path | Caminho do config.ini alternativo |

#### Exemplos

```bash
# Conversao basica para TXT
python cli.py convert --video data_input/video.mp4

# MP4 com qualidade baixa (rapido)
python cli.py convert --video data_input/video.mp4 --format mp4 --quality low

# HTML com audio embutido
python cli.py convert --video data_input/video.mp4 --format html

# GIF com estilo cyberpunk
python cli.py convert --video data_input/video.mp4 --format gif --style cyberpunk

# PNG do primeiro frame
python cli.py convert --video data_input/video.mp4 --format png

# Imagem para pixel art
python cli.py convert --image data_input/foto.png --mode pixelart

# Forcar CPU mesmo com GPU disponivel
python cli.py convert --video data_input/video.mp4 --format mp4 --no-gpu
```

#### Dispatch Table

| Format | Mode | Input | Funcao |
|--------|------|-------|--------|
| txt | ascii | video | `converter.iniciar_conversao()` |
| txt | pixelart | video | `pixel_art_converter.iniciar_conversao()` |
| txt | ascii | image | `image_converter.iniciar_conversao_imagem()` |
| txt | pixelart | image | `pixel_art_image_converter.iniciar_conversao_imagem()` |
| mp4 | * | video | GPU: `gpu_converter` / CPU: `mp4_converter` |
| gif | * | video | `gif_converter.converter_video_para_gif()` |
| html | * | video | `html_converter.converter_video_para_html()` |
| png | * | video | `png_converter.converter_video_para_png_primeiro()` |
| png | * | image | `png_converter.converter_imagem_para_png()` |
| png_all | * | video | `png_converter.converter_video_para_png_todos()` |

---

### `config` - Gerenciamento de configuracao

```bash
python cli.py config show              # Mostra todas as secoes
python cli.py config get SECAO CHAVE   # Retorna valor especifico
python cli.py config set SECAO CHAVE VALOR  # Modifica valor
python cli.py config reset             # Restaura defaults
python cli.py config presets           # Lista presets disponiveis
```

#### Exemplos

```bash
# Ver configuracao atual
python cli.py config show

# Ver largura atual
python cli.py config get Conversor target_width

# Mudar formato de saida
python cli.py config set Output format mp4

# Habilitar GPU
python cli.py config set Conversor gpu_enabled true

# Listar todos os presets
python cli.py config presets
```

---

### `validate` - Validacao de integridade

```bash
python cli.py validate                     # Checks basicos
python cli.py validate --video FILE        # Checks completos com video
```

#### Checks executados

| # | Check | Descricao |
|---|-------|-----------|
| 1 | Config Integrity | 16 secoes esperadas existem no config.ini |
| 2 | ffmpeg/ffprobe | Binarios encontrados + versao |
| 3 | GPU (cupy) | Import + nome do device |
| 4 | OpenCV | Import + versao |
| 5 | Converter Imports | 9 converters importaveis |
| 6 | audio_utils | Funcoes extract/mux existem |
| 7 | Output Dir | Diretorio existe e e gravavel |
| 8* | Audio Pipeline | Extracao AAC de video real |
| 9* | MP4 Pipeline | Conversao MP4 com mux de audio |
| 10* | HTML Audio | Conversao HTML + MP3 gerado |
| 11 | Settings Sync | Secoes MatrixRain, PostFX, OpticalFlow, Audio |

*Checks 8-10 requerem `--video`

---

### `info` - Diagnostico do sistema

```bash
python cli.py info
```

Mostra: config path, GPU, ffmpeg, OpenCV, Python, configuracao atual e converters disponiveis.

---

## Validacao pos-implementacao

Apos modificar qualquer converter ou componente core:

```bash
# 1. Diagnostico rapido
python cli.py info

# 2. Validacao de integridade
python cli.py validate

# 3. Validacao com video real (se disponivel)
python cli.py validate --video data_input/VIDEO.mp4

# 4. Teste de conversao especifica
python cli.py convert --video data_input/VIDEO.mp4 --format mp4 --quality low
python cli.py convert --video data_input/VIDEO.mp4 --format html --quality low

# 5. Verificar audio no MP4 gerado
ffprobe -i data_output/VIDEO_ascii.mp4 -show_streams -select_streams a -loglevel error
```
