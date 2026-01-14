# INDEX - Extase em 4R73

Mapeamento completo do projeto para referencia rapida de desenvolvimento.

**Objetivo:** Permitir que qualquer desenvolvedor (ou IA) entenda o projeto sem ler todos os arquivos.

---

## Arquitetura de Alto Nivel

```
main.py (Entry Point)
    ↓
src/app/app.py (Core GTK App)
    ├─→ src/gui/main.glade (Interface)
    ├─→ src/app/actions/*.py (Logica de acoes)
    └─→ config.ini (Persistencia)
        ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
src/core/gtk_calibrator.py    src/core/*_converter.py
(Calibracao HSV)              (Conversao ASCII/PixelArt)
```

---

## Ciclo de Sincronizacao (REGRA PRINCIPAL)

**Fontes de Verdade:**
1. config.ini - Persistencia em disco
2. Settings GUI - Interface de configuracao (aba Opcoes)
3. Calibrador GTK - Ajuste em tempo real

**Regra:**
O mais recente sobrescreve os outros. Timestamp determina prioridade.

**Fluxo:**
```
Usuario ajusta calibrador
  → Calibrador salva em config.ini (timestamp T1)
  → Settings GUI detecta mudanca (timestamp > ultimo_load)
  → Settings recarrega automaticamente

Usuario ajusta settings GUI
  → Settings salva em config.ini (timestamp T2)
  → Calibrador (se aberto depois) le valores atualizados

Conversao em lote
  → Cada video pode ter HSV proprio (memoria temporaria)
  → Nao sobrescreve config.ini global
```

**Implementacao:**
- config.ini tem timestamp de modificacao (mtime)
- Cada componente armazena ultimo_load_time
- Antes de usar valores: `if config_mtime > ultimo_load_time: reload()`

---

## Estrutura de Diretorios

```
/home/andrefarias/Desenvolvimento/Conversor-Video-Para-ASCII/
├── main.py                     # Entry point
├── config.ini                  # Configuracoes (FONTE DE VERDADE)
├── install.sh                  # Instalacao automatizada
├── uninstall.sh                # Desinstalacao
├── requirements.txt            # Dependencias Python
├── LICENSE                     # GPLv3
├── README.md                   # Documentacao publica
├── CONTRIBUTING.md             # Guia de contribuicao
├── CODE_OF_CONDUCT.md          # Codigo de conduta
├── SECURITY.md                 # Politica de seguranca
├── ROADMAP.md                  # Roadmap de sprints futuras
├── CLAUDE.md                   # Protocolo Luna (AI, ignorado git)
├── INDEX.md                    # Este arquivo
├── .gitignore                  # venv, logs, Dev_log, data_*
├── extase-em-4r73.desktop      # Desktop entry (menu aplicativos)
├── assets/
│   ├── icon.png                # Logo 120x120
│   └── background.png          # Screenshot
├── logs/                       # Logs rotacionados (ignorado git)
├── Dev_log/                    # Memoria de sprints (ignorado git)
│   ├── 2026-01-13_Sprint3_Terminal_Font.md
│   ├── 2026-01-13_Sprint4_ChromaKey_Per_Video.md
│   ├── 2026-01-13_Sprint5_Legacy_Cleanup.md
│   ├── 2026-01-13_Sprint8_Infraestrutura.md
│   └── 2026-01-13_Roadmap_Sprints_8-14.md
├── tools/                      # Ferramentas e benchmarks
│   └── benchmark_gpu.py        # Benchmark de performance GPU
├── tests/                      # Suite de testes (pytest)
│   ├── __init__.py
│   └── test_sprint7a.py        # Testes Sprint 7A (Braille + Temporal)
├── examples/                   # Exemplos de uso
│   ├── simple_convert.py       # Conversao basica
│   ├── webcam_ascii.py         # Webcam em tempo real
│   └── batch_processing.py     # Processamento em lote
├── scripts/                    # Scripts de build/release
│   └── build_deb.sh            # Build pacote .deb
├── docs/                       # Documentacao Sphinx
│   ├── Makefile                # Build docs (make html)
│   ├── source/
│   │   ├── conf.py             # Config Sphinx
│   │   ├── index.rst           # Homepage docs
│   │   ├── installation.rst    # Guia instalacao
│   │   ├── quickstart.rst      # Inicio rapido
│   │   └── faq.rst             # FAQ
│   └── build/                  # HTML gerado (ignorado git)
├── debian/                     # Metadados pacote .deb
│   ├── control                 # Dependencias, descricao
│   ├── postinst                # Script pos-instalacao
│   ├── prerm                   # Script pre-remocao
│   └── changelog               # Historico de versoes
├── .github/                    # Configuracoes GitHub
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md       # Template bug
│       ├── feature_request.md  # Template feature
│       └── question.md         # Template pergunta
├── data_input/                 # Entrada (ignorado git)
├── data_output/                # Saida (ignorado git)
├── docs/
│   └── (documentacao tecnica)
├── src/
│   ├── main.py                 # Inicializa GTK App
│   ├── cli_player.py           # Player standalone
│   ├── app/
│   │   ├── app.py              # Classe principal (mixins)
│   │   ├── constants.py        # Constantes globais
│   │   └── actions/
│   │       ├── file_actions.py
│   │       ├── conversion_actions.py
│   │       ├── calibration_actions.py
│   │       ├── playback_actions.py
│   │       └── options_actions.py
│   ├── core/
│   │   ├── converter.py        # CPU converter
│   │   ├── gpu_converter.py    # GPU converter (CUDA)
│   │   ├── mp4_converter.py    # ASCII → MP4
│   │   ├── gif_converter.py    # ASCII → GIF
│   │   ├── html_converter.py   # ASCII → HTML
│   │   ├── image_converter.py  # Imagem → ASCII
│   │   ├── pixel_art_converter.py
│   │   ├── gtk_calibrator.py   # Calibrador GTK (PRINCIPAL)
│   │   ├── realtime_ascii.py   # Preview terminal externo
│   │   ├── player.py           # Player CLI
│   │   ├── gtk_player.py       # Player GTK
│   │   └── utils/
│   │       ├── ascii_converter.py
│   │       ├── color.py
│   │       └── image.py
│   ├── gui/
│   │   ├── main.glade          # Interface principal
│   │   └── calibrator.glade    # Interface calibrador
│   └── utils/
│       ├── logger.py
│       └── terminal_font_detector.py  # Sprint 3
└── venv/                       # Ambiente virtual (ignorado git)
```

---

## Arquivos Criticos - Descricao Detalhada

### main.py (raiz)
**Linhas:** ~50
**Funcao:** Entry point. Valida ambiente, ajusta sys.path, chama src/main.py.
**Modificar quando:** Mudar estrutura de pastas ou adicionar validacoes de ambiente.

### src/main.py
**Linhas:** ~100
**Funcao:** Inicializa logger, cria instancia de App, inicia loop GTK.
**Modificar quando:** Alterar configuracao de logging ou adicionar inicializacoes globais.

### src/app/app.py
**Linhas:** ~600
**Funcao:** Classe principal App. Herda mixins (FileActions, ConversionActions, etc). Gerencia estado global.
**Estado:**
- self.config (ConfigParser)
- self.selected_file_path
- self.selected_folder_path
- self.conversion_lock (threading.Lock)
**Widgets:**
- main_window
- convert_button, convert_all_button
- calibrate_button
- options_dialog (5 abas)
**Modificar quando:** Adicionar novos widgets globais ou mudar estrutura de mixins.

### src/app/constants.py
**Linhas:** ~150
**Funcao:** Constantes globais.
**Conteudo:**
- VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', ...)
- IMAGE_EXTENSIONS = ('.png', '.jpg', ...)
- LUMINANCE_RAMPS = {'standard': 'ABC...', 'blocks': '█▓▒░', ...}
- FIXED_PALETTES = {'gameboy': [...], 'nes': [...], ...}
**Modificar quando:** Adicionar novo preset ou paleta.

### src/app/actions/file_actions.py
**Linhas:** ~100
**Funcao:** Selecao de arquivos/pastas via FileChooserDialog.
**Metodos:**
- on_open_video_button_clicked()
- on_open_folder_button_clicked()
- on_select_ascii_button_clicked()
**Modificar quando:** Adicionar novos tipos de arquivo ou validacoes.

### src/app/actions/conversion_actions.py
**Linhas:** ~400
**Funcao:** Conversao de videos/imagens para ASCII.
**Metodos:**
- on_convert_button_clicked() - Converter arquivo unico
- on_convert_all_button_clicked() - Batch conversion
  - Popup: "Config Atual (Rapido)" vs "Ajustar Video a Video"
  - Modo interativo: abre calibrador para cada video
- run_conversion() - Thread de conversao
  - Suporta TXT, MP4, GIF, HTML
  - Progress bar + thumbnail preview
**Modificar quando:** Adicionar novo formato de saida ou modo de conversao.

### src/app/actions/calibration_actions.py
**Linhas:** ~50
**Funcao:** Abre calibrador GTK.
**Metodos:**
- on_calibrate_button_clicked()
**Modificar quando:** Alterar forma de lancar calibrador ou adicionar validacoes.

### src/app/actions/playback_actions.py
**Linhas:** ~100
**Funcao:** Reproducao de arquivos ASCII (.txt).
**Metodos:**
- on_play_button_clicked()
**Modificar quando:** Adicionar novos modos de playback.

### src/app/actions/options_actions.py
**Linhas:** ~600
**Funcao:** Dialog de configuracoes (5 abas).
**Abas:**
1. Player - Loop, clear screen, show FPS, velocidade
2. Conversor - Largura, altura, sobel, aspect ratio, luminance ramp
3. Chroma Key - HSV sliders, erode, dilate, presets
4. Preferencias - Input/output folders, engine, formato, GPU, Braille, Temporal
5. Terminal - Deteccao de fonte, ComboBox de fontes, tamanho
**Metodos:**
- on_options_button_clicked() - Abre dialog, carrega config.ini
- on_options_save_clicked() - Salva config.ini
- on_options_restore_clicked() - Restaura defaults
**Sincronizacao:** Le config.ini ao abrir, escreve ao salvar.
**Modificar quando:** Adicionar nova aba ou widget de configuracao.

### src/core/converter.py
**Linhas:** ~300
**Funcao:** Conversor CPU (fallback quando GPU indisponivel).
**Pipeline:**
1. Le video frame a frame (OpenCV)
2. Aplica chroma key (HSV mask)
3. Resize para target_width x target_height
4. Sobel edge detection
5. Mapeia pixels → caracteres ASCII (luminance ramp)
6. Adiciona cores ANSI 256
7. Escreve frames em arquivo TXT
**Metodos:**
- convert_video_to_ascii()
- apply_chroma_key()
- frame_para_ascii()
**Modificar quando:** Alterar algoritmo de conversao CPU.

### src/core/gpu_converter.py
**Linhas:** ~700
**Funcao:** Conversor GPU usando CUDA (CuPy).
**Kernels CUDA:**
- SOBEL_KERNEL - Edge detection em GPU
- BRAILLE_KERNEL - Conversao Unicode Braille (2x4 pixels → 1 char)
- TEMPORAL_COHERENCE_KERNEL - Anti-flicker (compara frames consecutivos)
**Render Modes:**
- fast - Apenas luminancia
- high_fidelity - Luminancia + edges + cores
**Pipeline:**
1. Frame para GPU (CuPy array)
2. Chroma key em GPU
3. Conversao ASCII ou Braille
4. Temporal coherence (opcional)
5. Render para PIL Image
**Metodos:**
- convert_video_to_ascii_gpu()
- process_frame()
- convert_to_braille()
- apply_temporal_coherence()
- render_ascii_to_image()
**Atlas:**
- generate_atlas_cpu() - Atlas de caracteres ASCII
- generate_braille_atlas_cpu() - Atlas Braille (256 chars U+2800-U+28FF)
- Cache em `.cache/gpu_atlas.pkl` ou `.cache/gpu_braille_atlas.pkl`
**Modificar quando:** Adicionar novo kernel CUDA ou modo de render.

### src/core/mp4_converter.py
**Linhas:** ~200
**Funcao:** Converte ASCII TXT → MP4.
**Metodos:**
- convert_ascii_to_mp4()
**Modificar quando:** Alterar codec ou qualidade de video.

### src/core/gif_converter.py
**Linhas:** ~150
**Funcao:** Converte ASCII TXT → GIF animado.
**Metodos:**
- convert_ascii_to_gif()
**Modificar quando:** Alterar otimizacao de GIF.

### src/core/html_converter.py
**Linhas:** ~200
**Funcao:** Gera player HTML interativo com JavaScript.
**Metodos:**
- convert_ascii_to_html()
**Modificar quando:** Alterar template HTML ou adicionar controles.

### src/core/image_converter.py
**Linhas:** ~150
**Funcao:** Converte imagem estatica para ASCII.
**Metodos:**
- convert_image_to_ascii()
**Modificar quando:** Adicionar novos filtros de imagem.

### src/core/pixel_art_converter.py
**Linhas:** ~250
**Funcao:** Conversao alternativa para pixel art (paletas retro).
**Metodos:**
- convert_video_to_pixelart()
- quantize_colors()
**Modificar quando:** Adicionar novas paletas ou algoritmos de quantizacao.

### src/core/gtk_calibrator.py (ARQUIVO MAIS CRITICO)
**Linhas:** ~1300
**Funcao:** Calibrador visual de chroma key usando GTK.
**Interface:**
- Preview video/webcam em tempo real
- Sliders HSV (H, S, V min/max)
- Sliders erode/dilate
- Presets (studio, natural, bright)
- Botoes: Salvar, Testar ASCII, Gravar MP4/ASCII
- Preview ASCII em terminal externo (duplo clique)
**Modos:**
- Webcam (source 0) ou video (arquivo especifico)
**Render Modes:**
- RENDER_MODE_USER - Video original
- RENDER_MODE_BACKGROUND - Fundo (masked)
- RENDER_MODE_BOTH - Split screen
**Conversion Modes:**
- MODE_ASCII - ASCII tradicional
- MODE_PIXELART - Pixel art
**Gravacao:**
- MP4: Captura area ASCII via ffmpeg, salva em ~/Videos
- ASCII: Processa frames e salva TXT
**Braille e Temporal:**
- Suporta Unicode Braille (resolucao 4x)
- Suporta Temporal Coherence (anti-flicker)
- Controles na interface (row 4)
**Metodos Principais:**
- __init__() - Inicializa captura, carrega config
- _load_config() - Le config.ini
- _update_frame() - Loop de atualizacao (30 FPS)
- _apply_chroma_key() - Aplica mascara HSV
- _on_slider_changed() - Atualiza valores ao mover sliders
- on_save_button_clicked() - Salva HSV em config.ini
- _open_terminal_preview() - Abre preview ASCII em terminal externo
- _start_mp4_recording() / _stop_mp4_recording()
- _start_ascii_recording() / _stop_ascii_recording()
**Sincronizacao:**
- Ao abrir: le config.ini
- Ao salvar: escreve config.ini (timestamp atualizado)
- Settings GUI recarrega apos fechar calibrador
**Modificar quando:** Adicionar novos controles, alterar gravacao, ajustar renderizacao.

### src/core/realtime_ascii.py
**Linhas:** ~250
**Funcao:** Preview ASCII em terminal externo (usado pelo calibrador).
**Metodos:**
- run_realtime_ascii()
**Modificar quando:** Alterar comportamento do preview ou adicionar controles de teclado.

### src/core/player.py
**Linhas:** ~200
**Funcao:** Player CLI de arquivos TXT ASCII.
**Metodos:**
- play_ascii_file()
**Modificar quando:** Adicionar suporte a novos terminais.

### src/core/gtk_player.py
**Linhas:** ~300
**Funcao:** Player GTK (GUI) de arquivos TXT ASCII.
**Interface:** Play, Pause, Stop, slider de velocidade.
**Modificar quando:** Alterar interface do player.

### src/core/utils/ascii_converter.py
**Linhas:** ~200
**Funcao:** Funcoes de conversao frame → ASCII.
**Metodos:**
- converter_frame_para_ascii()
- frame_para_ascii_rt() - Versao otimizada para tempo real
**Constantes:**
- LUMINANCE_RAMP_DEFAULT - Caracteres ASCII ordenados por luminancia
- COLOR_SEPARATOR - Separador para codigo ANSI
**Modificar quando:** Alterar algoritmo de conversao.

### src/core/utils/color.py
**Linhas:** ~50
**Funcao:** Conversao RGB → ANSI 256.
**Metodos:**
- rgb_to_ansi256()
**Modificar quando:** Adicionar suporte a True Color (24-bit).

### src/core/utils/image.py
**Linhas:** ~100
**Funcao:** Processamento de imagem.
**Metodos:**
- sharpen_frame()
- apply_morphological_refinement()
**Modificar quando:** Adicionar novos filtros.

### src/gui/main.glade
**Linhas:** ~1800 (XML)
**Funcao:** Definicao da interface GTK.
**Janelas:**
- main_window - Janela principal
- options_dialog - Dialog de configuracoes (5 abas)
**Abas do Options Dialog:**
1. Player
2. Conversor
3. Chroma Key
4. Preferencias (GPU, Braille, Temporal)
5. Terminal (Fonte) - Sprint 3
**Widgets de Config:**
- Spinners: width, height, sobel, aspect, font_size
- Sliders: h_min/max, s_min/max, v_min/max, erode, dilate, braille_threshold, temporal_threshold
- Switches: gpu_enabled, braille_enabled, temporal_enabled, font_detection_enabled
- Combos: luminance_preset, engine, quality, format, render_mode, font_family
- Entries: luminance_ramp
- File choosers: input_folder, output_folder
**Modificar quando:** Adicionar novos botoes, alterar layout, criar novos dialogos.

### src/gui/calibrator.glade
**Linhas:** ~800 (XML)
**Funcao:** Interface do calibrador GTK.
**Componentes:**
- Preview video/webcam
- Sliders HSV
- Botoes: Salvar, Testar, Gravar
- Status bar
- Controles Braille/Temporal (row 4)
**Modificar quando:** Adicionar novos controles ao calibrador.

### src/utils/logger.py
**Linhas:** ~100
**Funcao:** Sistema de logging rotacionado.
**Features:**
- Logs em logs/
- Rotacao automatica (10 MB, 5 backups)
- Formato: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
**Modificar quando:** Alterar formato de log ou rotacao.

### src/utils/terminal_font_detector.py (Sprint 3)
**Linhas:** ~185
**Funcao:** Detecta fonte do terminal automaticamente.
**Metodos:**
- detect_current_terminal() - Identifica terminal (KITTY, GNOME_TERMINAL, XTERM)
- detect_terminal_font() - Retorna {'family': str, 'size': int, 'terminal': str}
- read_kitty_font() - Le ~/.config/kitty/kitty.conf
- read_gnome_terminal_font() - Le via gsettings
- read_xterm_font() - Le ~/.Xresources
- list_monospace_fonts() - Lista fontes monospace (fc-list :spacing=100)
**Uso:**
- Calibrador usa para abrir preview com fonte correta
- Settings GUI oferece ComboBox com lista de fontes
**Modificar quando:** Adicionar suporte a novos terminais.

### config.ini (FONTE DE VERDADE)
**Funcao:** Persistencia de todas as configuracoes.
**Secoes:**
- [Conversor] - target_width, target_height, sobel_threshold, char_aspect_ratio, luminance_ramp, luminance_preset, sharpen_enabled, sharpen_amount, gpu_enabled, gpu_render_mode, braille_enabled, braille_threshold, temporal_coherence_enabled, temporal_threshold
- [ChromaKey] - h_min, h_max, s_min, s_max, v_min, v_max, erode, dilate
- [Player] - loop, clear_screen, show_fps, speed
- [Preview] - font_family, font_size, font_detection_enabled (Sprint 3)
- [Mode] - conversion_mode (ascii ou pixelart)
- [PixelArt] - pixel_size, color_palette_size, use_fixed_palette, fixed_palette_name
- [Output] - format (txt, mp4, gif, html)
- [Pastas] - input_dir, output_dir
- [Quality] - preset, player_zoom
**Sincronizacao:**
- Calibrador le ao abrir, escreve ao salvar
- Settings le ao abrir, escreve ao salvar
- Timestamp (mtime) determina prioridade
**Modificar quando:** Adicionar nova configuracao.

---

## Fluxos Principais

### Fluxo 1: Conversao Simples
```
Usuario seleciona video → Clica "Converter"
→ conversion_actions.on_convert_button_clicked()
→ run_conversion() (thread)
→ Le config.ini
→ Escolhe conversor (CPU/GPU conforme config)
→ converter.convert_video_to_ascii() ou gpu_converter.convert_video_to_ascii_gpu()
→ Progress callback atualiza UI
→ Salva output em output_dir
→ Dialog de finalizacao
```

### Fluxo 2: Calibracao de Chroma Key
```
Usuario clica "Calibrar Chroma Key"
→ calibration_actions.on_calibrate_button_clicked()
→ Abre gtk_calibrator.GTKCalibrator
→ Usuario ajusta sliders HSV
→ Preview atualiza em tempo real (30 FPS)
→ Usuario clica "Salvar"
→ gtk_calibrator salva valores em config.ini (timestamp T1)
→ Fecha calibrador
→ Settings GUI (se aberto) detecta mudanca (config_mtime > ultimo_load)
→ Settings recarrega automaticamente
```

### Fluxo 3: Conversao em Lote (Interativa)
```
Usuario seleciona pasta → Clica "Converter Pasta"
→ conversion_actions.on_convert_all_button_clicked()
→ Popup: "Config Atual (Rapido)" vs "Ajustar Video a Video"
→ Usuario escolhe "Ajustar Video a Video"
→ Para cada video:
  → Abre calibrador para video X
  → Usuario ajusta HSV
  → Salva em config.ini (timestamp T2)
  → Fecha calibrador
  → Converte video X com HSV atual
  → Proximo video (le config.ini atualizado)
→ Dialog de finalizacao
```

### Fluxo 4: Sincronizacao de Config (Sprint 4 - A Implementar)
```
Fonte de Verdade: config.ini (timestamp de modificacao)

Cenario A: Usuario ajusta calibrador
→ Calibrador salva em config.ini (timestamp T1)
→ Settings GUI detecta mudanca: config_mtime > self.config_last_load
→ Settings recarrega automaticamente

Cenario B: Usuario ajusta settings GUI
→ Settings salva em config.ini (timestamp T2)
→ Calibrador (se abrir depois) le valores atualizados

Cenario C: Conversao em lote (Sprint 4)
→ Cada video tem HSV proprio em memoria (dict temporario)
→ Nao sobrescreve config.ini global durante conversao
→ Apos finalizacao: restaura config.ini original ou pergunta ao usuario
```

---

## Pontos de Integracao

### Chroma Key

**Leitura:**
- gtk_calibrator.py:_load_config() - Le HSV de config.ini
- converter.py:convert_video_to_ascii() - Le HSV de config.ini
- gpu_converter.py:convert_video_to_ascii_gpu() - Le HSV de config.ini

**Escrita:**
- gtk_calibrator.py:on_save_button_clicked() - Escreve HSV em config.ini
- options_actions.py:on_options_save_clicked() - Escreve HSV em config.ini

**Sincronizacao (A Implementar - Sprint 4):**
- Adicionar self.config_last_load em gtk_calibrator.py e options_actions.py
- Antes de usar valores: verificar if config_mtime > self.config_last_load: reload()
- Adicionar parametro chroma_override: dict opcional em conversores
- Se fornecido, usar override ao inves de config.ini

### Preview ASCII

**Entrada:**
- gtk_calibrator.py:_open_terminal_preview() - Detecta fonte do terminal
- terminal_font_detector.py:detect_terminal_font() - Retorna fonte

**Saida:**
- Abre realtime_ascii.py em terminal externo (kitty/gnome-terminal/xterm)
- Passa parametros de fonte via command line

### GPU Acceleration

**Deteccao:**
- gpu_converter.py:__init__() - Verifica CuPy disponivel
- Se GPU indisponivel, fallback para CPU

**Uso:**
- conversion_actions.py:run_conversion() - Le config.ini [Conversor] gpu_enabled
- Se true: usa gpu_converter.py
- Se false: usa converter.py

---

## Sprints Concluidas

### Sprint 1: Preview Automatico
- Preview so abre com duplo clique (nao automatico)

### Sprint 2: Sistema de Gravacao
- Gravacao MP4 da area ASCII
- Gravacao ASCII (TXT)
- FPS otimizado (30 fps)
- Popup com opcoes pos-gravacao

### Sprint 3: Fonte do Terminal
- Deteccao automatica de fonte (kitty, gnome-terminal, xterm)
- Interface GUI com ComboBox de fontes (lista fontes monospace via fc-list)
- Persistencia em config.ini [Preview]
- Sincronizacao calibrador-settings-config (via timestamp)

### Sprint 4: Chroma Key por Video
- Popup de escolha: "Mesmos valores" vs "Calibrar individualmente"
- Fluxo iterativo de calibracao (video a video)
- HSV por video em memoria (dict temporario)
- Sincronizacao timestamp-based entre calibrador/settings/config.ini

### Sprint 5: Remocao de Codigo Legacy
- Removido calibrador CLI antigo (calibrator.py) - 544 linhas
- Removido fallback OpenCV
- Limpeza de config.ini (pixel_scale removido)
- GTK calibrador como unica interface

### Sprint 6: Performance Extrema (GPU Base)
- gpu_converter.py criado com kernels CUDA
- Toggle "Aceleracao de Hardware" na interface (pref_gpu_switch)
- Calibrador GTK com suporte GPU
- Ganho: 10-30x performance (CPU vs GPU)

### Sprint 7A: High Fidelity + Braille + Temporal
- Modo "High Fidelity" (comparacao MSE textura vs luminancia)
- Unicode Braille (resolucao 4x, 2x4 pixels por char)
- Temporal Coherence (anti-flicker, threshold ajustavel)
- Controles live no calibrador GTK

### Sprint 8: Infraestrutura e Profissionalizacao
- Reorganizacao estrutura: tools/, tests/, examples/, scripts/, docs/, debian/
- Templates GitHub issues (bug_report, feature_request, question)
- Arquivos raiz: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, ROADMAP.md
- Script build_deb.sh e metadados DEBIAN
- Desktop entry (.desktop file)
- Documentacao Sphinx (docs/source/*.rst)
- Lazy imports otimizados (startup 650ms)
- Regra de anonimato (.gitignore atualizado)

### Sprint 7B: Async CUDA Streams
- AsyncGPUConverter com 4 streams paralelos
- Pipeline de batch processing (8 frames simultaneos)
- Overlapping de transferencias CPU↔GPU e processamento
- Toggle "Async Streams" na interface (Preferencias → GPU)
- Ganho esperado: +15-20% FPS (30 → 35-36 fps)

### Sprint 9: Matrix Rain (Particle System GPU)
- Sistema de particulas GPU com 2500+ particulas
- Modos: Katakana, Binary, Symbols
- Fisica: gravidade, velocidade configuravel
- Overlay sobre video ou standalone

### Sprint 10: Pos-Processamento Cyberpunk (PostFX)
- Bloom neon com threshold e radius ajustaveis
- Chromatic aberration (separacao RGB)
- Scanlines CRT com intensidade e espacamento
- Glitch digital com block size configuravel

### Sprint 11: Audio Reactive
- Analise FFT em tempo real (PyAudio)
- Modulacao por frequencia: Bass, Mids, Treble
- Sensibilidade ajustavel por banda
- Smoothing para transicoes suaves

### Sprint 12: Optical Flow
- Interpolacao de frames via OpenCV
- 15 FPS para 30/60 FPS
- Motion blur opcional
- Presets de qualidade (low, medium, high)

### Sprint 13: Sistema de Temas
- Tema Dark (Dracula-inspired) como padrao
- Tema Light disponivel
- Persistencia em config.ini [Interface]
- CSS customizado para GTK widgets

### Sprint 14: Deploy Multiplataforma
- AppImage funcional com dependencias bundled
- Flatpak com manifest completo
- Pacote .deb para Ubuntu/Debian
- Workflow GitHub Actions automatizado

---

## Sprints Futuras

### Sprint 15: Neural ASCII (Style Transfer)
- DoG/XDoG edge detection
- Presets: Sketch, Comic, Oil, Pencil
- Integracao com modelos pre-treinados

### Sprint 16: Polimento Final e Release 1.0.0
- Testes completos (pytest)
- Profiling e otimizacoes finais
- Documentacao completa
- Marketing: YouTube, Reddit, Hacker News

---

## Notas Finais

**Este INDEX deve ser atualizado a cada:**
- Novo arquivo criado
- Script modificado significativamente
- Nova feature implementada
- Sprint concluida

**Formato de Atualizacao:**
1. Adicionar entrada na secao "Arquivos Criticos"
2. Descrever funcao, linhas, metodos, responsabilidades
3. Atualizar fluxos se necessario
4. Documentar pontos de integracao

**Objetivo:**
Permitir que qualquer desenvolvedor (ou IA) entenda o projeto sem precisar ler todos os arquivos.

---

**Ultima Atualizacao:** 2026-01-14 (Sprint 14 concluida - Deploy Multiplataforma)
