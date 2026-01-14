# Mapa do Projeto (Extase em 4R73 v2.3.0)

Este arquivo serve como guia de navegacao rapida para a estrutura do projeto.

## Documentacao Principal

| Arquivo | Descricao |
|---------|-----------|
| [README.md](README.md) | Visao geral, instalacao e uso basico |
| [docs/INDEX.md](docs/INDEX.md) | Indice Tecnico Detalhado |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Historico de versoes |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | Manual do Usuario |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Roadmap de Sprints |

## Estrutura de Diretorios

```
/
├── main.py                 # Entry point
├── config.ini              # Configuracoes
├── install.sh              # Instalacao automatizada
├── uninstall.sh            # Remocao limpa
├── requirements.txt        # Dependencias Python
├── pytest.ini              # Configuracao de testes
├── .coveragerc             # Configuracao de cobertura
│
├── src/
│   ├── app/                # Logica GTK principal
│   │   ├── app.py          # Classe GTKApplication
│   │   ├── constants.py    # Constantes globais
│   │   └── actions/        # Handlers de acoes
│   │
│   ├── core/               # Modulos de processamento
│   │   ├── converter.py        # Conversor base CPU
│   │   ├── gpu_converter.py    # Conversor GPU CUDA
│   │   ├── async_gpu_converter.py # Async CUDA Streams
│   │   ├── gtk_calibrator.py   # Calibrador GTK
│   │   ├── post_fx_gpu.py      # PostFX (Bloom, Glitch, etc)
│   │   ├── style_transfer.py   # Style presets (DoG/XDoG)
│   │   ├── optical_flow.py     # Motion Blur
│   │   ├── audio_analyzer.py   # Audio Reactive
│   │   ├── matrix_rain_gpu.py  # Particle System
│   │   └── utils/              # Helpers
│   │
│   ├── gui/                # Interfaces Glade
│   │   ├── main.glade
│   │   └── calibrator.glade
│   │
│   └── utils/              # Utilitarios globais
│       ├── logger.py       # Logging rotacionado
│       └── lazy_loader.py  # Lazy imports
│
├── tests/                  # Suite pytest (43 testes)
│   ├── conftest.py
│   ├── test_color.py
│   ├── test_image.py
│   ├── test_ascii_converter.py
│   └── test_logger.py
│
├── docs/                   # Documentacao
├── debian/                 # Packaging .deb
├── packaging/              # Scripts de build
├── assets/                 # Icones e modelos
└── examples/               # Exemplos de uso
```

## Scripts Importantes

| Script | Descricao |
|--------|-----------|
| `main.py` | Ponto de entrada |
| `install.sh` | Instalacao (Ubuntu/Debian) |
| `uninstall.sh` | Remocao limpa |
| `packaging/build-deb.sh` | Gera pacote .deb |
| `packaging/build-appimage.sh` | Gera AppImage |
| `packaging/build-flatpak.sh` | Gera Flatpak |

## Modulos Core (v2.3.0)

### Conversao
- `converter.py` - ASCII basico CPU
- `gpu_converter.py` - ASCII GPU CUDA
- `async_gpu_converter.py` - Async CUDA Streams
- `pixel_art_converter.py` - Modo Pixel Art

### Efeitos Visuais
- `post_fx_gpu.py` - Bloom, Glitch, Chromatic, Scanlines, Brightness, Color Shift
- `style_transfer.py` - Sketch, Ink, Comic, Neon, Emboss
- `optical_flow.py` - Motion Blur baseado em Farneback
- `matrix_rain_gpu.py` - Particle System estilo Matrix

### Audio
- `audio_analyzer.py` - FFT em tempo real, 3 bandas (Bass/Mids/Treble)

### Segmentacao
- `auto_segmenter.py` - MediaPipe Selfie Segmentation

## Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov --cov-report=term-missing
```

Cobertura atual: 97% (modulos testaveis)

---
*Ultima atualizacao: 2026-01-14 (v2.3.0)*
