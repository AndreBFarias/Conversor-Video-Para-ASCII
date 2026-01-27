# INDEX - Extase em 4R73

**Auditoria Completa:** 2026-01-26
**Versao:** 2.3.0
**Status:** Funcional - Problemas corrigidos

---

## PROBLEMAS CORRIGIDOS NESTA SESSAO

### 1. Sincronizacao Term/RESULTADO (CORRIGIDO)
- O botao "Term" do calibrador agora passa TODOS os parametros atuais via CLI
- Incluindo: HSV, AutoSeg, Matrix Rain, PostFX, Edge Boost, Temporal, Render Mode, etc.
- Arquivos modificados: `realtime_ascii.py`, `gtk_calibrator.py`

### 2. Conversao de Imagens (CORRIGIDO)
- Scripts de imagem agora aceitam `--output-dir` via CLI
- O `conversion_actions.py` passa o diretorio de saida da UI
- Arquivos modificados: `image_converter.py`, `pixel_art_image_converter.py`, `conversion_actions.py`

### 3. Arquivos Orfaos (DELETADOS)
- `src/core/calibrator.py` (versao OpenCV antiga, nao usada)
- `src-new-que-deu-problema/` (backup com codigo quebrado)
- `SESSION_CHANGES.md`, `tecnomago-github.txt`, `Juno_observando.txt`

---

## MAPA DE ARQUIVOS

### Entry Points

| Arquivo | Linhas | Funcao | Status |
|---------|--------|--------|--------|
| `main.py` | 71 | Entry point da raiz | OK |
| `src/main.py` | 146 | Entry point real (run_app) | OK |

### Aplicacao GTK (`src/app/`)

| Arquivo | Linhas | Funcao | Status |
|---------|--------|--------|--------|
| `app.py` | 574 | Classe App principal (mixins) | OK |
| `constants.py` | 222 | Constantes, caminhos, presets | OK |
| `actions/file_actions.py` | 132 | Selecao de arquivos/pastas | OK |
| `actions/conversion_actions.py` | 354 | Logica de conversao | OK (corrigido) |
| `actions/playback_actions.py` | 118 | Reproducao de ASCII | OK |
| `actions/calibration_actions.py` | 73 | Lanca calibradores | OK |
| `actions/options_actions.py` | 768 | Dialogo de opcoes | OK |
| `actions/postfx_actions.py` | 165 | Controle de efeitos | OK |

### Conversores (`src/core/`)

| Arquivo | Linhas | Funcao | Status |
|---------|--------|--------|--------|
| `converter.py` | 242 | Video -> TXT (ASCII) | OK |
| `image_converter.py` | 130 | Imagem -> TXT (ASCII) | OK (corrigido) |
| `mp4_converter.py` | 298 | Video -> MP4 ASCII | OK |
| `gif_converter.py` | 285 | Video -> GIF ASCII | OK |
| `html_converter.py` | 447 | Video -> HTML standalone | OK |
| `gpu_converter.py` | 1093 | Conversao GPU (CuPy) | OK |
| `async_gpu_converter.py` | 241 | GPU com async streams | OK |
| `pixel_art_converter.py` | 208 | Video -> Pixel Art TXT | OK |
| `pixel_art_image_converter.py` | 209 | Imagem -> Pixel Art TXT | OK (corrigido) |

### Calibradores (`src/core/`)

| Arquivo | Linhas | Funcao | Status |
|---------|--------|--------|--------|
| `gtk_calibrator.py` | 2593 | Calibrador GTK moderno | OK (grande mas funcional) |
| `realtime_ascii.py` | 540 | Preview terminal em tempo real | OK (corrigido) |

### Outros Core

| Arquivo | Linhas | Funcao | Status |
|---------|--------|--------|--------|
| `renderer.py` | 257 | Renderiza ASCII como imagem | OK |
| `player.py` | 231 | Player de TXT no terminal | OK |
| `gtk_player.py` | 150 | Player GTK | OK |
| `post_fx_gpu.py` | 377 | Efeitos PostFX (GPU) | OK |
| `matrix_rain_gpu.py` | 161 | Efeito Matrix Rain | OK |
| `optical_flow.py` | 231 | Interpolacao de frames | OK |
| `audio_analyzer.py` | 305 | Audio-reactive | OK |
| `style_transfer.py` | 182 | Presets de estilo | OK |
| `auto_segmenter.py` | 123 | MediaPipe segmentation | OK |

### Utils

| Arquivo | Funcao | Status |
|---------|--------|--------|
| `src/core/utils/ascii_converter.py` | Conversao frame->ASCII | OK |
| `src/core/utils/color.py` | Cores ANSI | OK |
| `src/core/utils/image.py` | Sharpen, morphology | OK |
| `src/utils/logger.py` | Logging rotacionado | OK |
| `src/utils/lazy_loader.py` | Lazy import | OK |
| `src/utils/gpu_memory_manager.py` | Gerenciamento VRAM | OK |
| `src/utils/terminal_font_detector.py` | Detecta fonte terminal | OK |

---

## DEPENDENCIAS ENTRE MODULOS

```
main.py
  |
  +-> src/main.py::run_app()
       |
       +-> src/app/App (mixins)
            |
            +-> FileActionsMixin
            +-> ConversionActionsMixin
            |     |
            |     +-> converter.py (subprocess)
            |     +-> image_converter.py (subprocess, --output-dir)
            |     +-> pixel_art_image_converter.py (subprocess, --output-dir)
            |     +-> mp4_converter.py (import direto, callback)
            |     +-> gif_converter.py (import direto, callback)
            |     +-> html_converter.py (import direto, callback)
            |     +-> gpu_converter.py (import direto, callback)
            |
            +-> PlaybackActionsMixin
            |     |
            |     +-> cli_player.py
            |     +-> gtk_player.py
            |
            +-> CalibrationActionsMixin
            |     |
            |     +-> gtk_calibrator.py (subprocess)
            |     +-> realtime_ascii.py (subprocess em terminal, com overrides)
            |
            +-> OptionsActionsMixin
            +-> PostFXActionsMixin
```

---

## CONFIGURACAO

### Arquivos de Config

| Arquivo | Funcao |
|---------|--------|
| `config.ini` (raiz) | Config padrao do projeto |
| `~/.config/extase-em-4r73/config.ini` | Config do usuario (copia) |

### Secoes Criticas

```ini
[Conversor]      # Parametros de conversao
[ChromaKey]      # Valores HSV do chroma
[PixelArt]       # Paleta e pixel size
[PostFX]         # Efeitos visuais
[MatrixRain]     # Configuracao da chuva
[Pastas]         # input_dir, output_dir
[Output]         # format (txt/mp4/gif/html)
[Mode]           # conversion_mode (ascii/pixelart)
[Quality]        # player_zoom
```

---

## TESTES

```bash
# Rodar todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov --cov-report=term-missing
```

Cobertura atual: 97% (modulos testaveis)

---

## SCRIPTS IMPORTANTES

| Script | Descricao |
|--------|-----------|
| `main.py` | Ponto de entrada |
| `install.sh` | Instalacao (Ubuntu/Debian) |
| `uninstall.sh` | Remocao limpa |
| `packaging/build-deb.sh` | Gera pacote .deb |
| `packaging/build-appimage.sh` | Gera AppImage |
| `packaging/build-flatpak.sh` | Gera Flatpak |

---

## VALIDACAO

```bash
# Testar import de todos os modulos
python3 -c "from src.app import App; print('App: OK')"
python3 -c "from src.core.converter import iniciar_conversao; print('Converter: OK')"
python3 -c "from src.core.image_converter import iniciar_conversao_imagem; print('Image: OK')"
python3 -c "from src.core.auto_segmenter import AutoSegmenter, is_available; print(f'AutoSeg: {is_available()}')"

# Rodar a aplicacao
python3 main.py
```

---

*Ultima atualizacao: 2026-01-26 (Auditoria + Correcoes)*

*"A simplicidade e a sofisticacao final." - Leonardo da Vinci*
