# Changelog

Todas as mudanças notaveis neste projeto serao documentadas neste arquivo.

## [2.3.0] - 2026-01-14

### Sprint 15: Impacto Visual Real

#### PostFX - Valores Ajustados
- Bloom threshold: 150 -> 80 (mais pixels qualificam)
- Bloom intensity: 0.6 -> 1.2 (efeito mais visivel)
- Chromatic shift: 5 -> 12 (aberracao perceptivel)
- Glitch intensity: 0.3 -> 0.6 (dispara mais frequente)
- Scanlines spacing: 3 -> 2 (linhas mais densas)

#### Audio Reactive - Modulacoes Completas
- Brightness modulation conectada (bass -> brightness)
- Color shift conectada (bandas -> RGB shift)
- Multiplicadores aumentados para impacto visual

#### Style Transfer - Presets Intensificados
- Sketch: edge_strength 1.5 -> 3.0
- Ink: edge_strength 2.0 -> 4.0, inversao de edges
- Neon: blend 0.5/0.5 -> 0.3/0.7 (mais colorido)
- Emboss: edge_strength 1.8 -> 3.5
- Cyberpunk: novo preset com neon magenta/ciano e bordas brilhantes

#### Novas Features PostFX
- `brightness_enabled` / `brightness_multiplier`
- `color_shift_enabled` / `color_shift_r/g/b`

#### Motion Blur (Optical Flow)
- `apply_motion_blur()` - efeito de rastro de movimento
- Baseado em Farneback Optical Flow
- Parametros: intensity (0.3-1.0), samples (3-8)
- Integrado no pipeline do calibrador

### Documentacao
- User Manual completo (docs/USER_MANUAL.md)
- Testes mantidos em 97% cobertura

---

## [2.2.0] - 2026-01-14

### Sprints 7A-13: Features Avancadas

#### Sprint 7A: Unicode Braille + Temporal Coherence
- Modo Braille com Unicode (4x resolucao efetiva)
- Sistema anti-flicker com temporal coherence
- Threshold configuravel para estabilidade visual

#### Sprint 7B: Async CUDA Streams
- `async_gpu_converter.py` com CuPy Streams
- Ganho de +15-20% FPS em conversoes GPU
- Pipeline assíncrono para frames

#### Sprint 9: Matrix Rain (Particle System GPU)
- `matrix_rain_gpu.py` com sistema de particulas
- Suporte a 5000+ particulas simultaneas
- Charsets: Katakana, Binary, ASCII, Mixed
- Velocidade e densidade configuraveis

#### Sprint 10: Pos-Processamento Cyberpunk
- `post_fx_gpu.py` com efeitos visuais
- Bloom (brilho neon com Gaussian blur)
- Chromatic Aberration (RGB shift)
- Scanlines CRT
- Glitch effect (distorcao aleatoria)

#### Sprint 11: Neural ASCII (Style Transfer)
- `style_transfer.py` com estilizacao pre-conversao
- DoG/XDoG edge detection
- 6 presets: None, Sketch, Comic, Ink, Neon, Emboss

#### Sprint 12: Optical Flow (Interpolacao)
- `optical_flow.py` com interpolacao de frames
- Farneback Optical Flow (CPU e GPU)
- Target FPS: 30, 60, 120
- Frame warping bidirecional

#### Sprint 13: Audio-Reactive ASCII
- `audio_analyzer.py` com FFT em tempo real
- 3 bandas: Bass, Mids, Treble
- Modulacao de efeitos PostFX via audio
- Captura via PyAudio (loopback/mic)

### Sprint 8: Infraestrutura

#### Profissionalizacao
- Pacote .deb funcional com postinst robusto
- Lazy loader para modulos pesados
- Documentacao Sphinx configurada

#### Anonimato
- Remocao de referencias a ferramentas de desenvolvimento
- TESTING_GUIDE.md generalizado

#### Testes
- Suite pytest com 43 testes unitarios
- Cobertura de 97% nos modulos testaveis
- Configuracao .coveragerc para exclusao de GUI/GPU

### Arquivos Adicionados
- `src/core/async_gpu_converter.py`
- `src/core/matrix_rain_gpu.py`
- `src/core/post_fx_gpu.py`
- `src/core/style_transfer.py`
- `src/core/optical_flow.py`
- `src/core/audio_analyzer.py`
- `tests/test_color.py`
- `tests/test_image.py`
- `tests/test_ascii_converter.py`
- `tests/test_logger.py`
- `tests/conftest.py`
- `pytest.ini`
- `.coveragerc`

---

## [2.1.0] - 2025-12-31

### Interface Renovada

#### Reorganizacao da Interface Principal
- Nova ordem de secoes seguindo jornada do usuario:
  1. Selecionar (Arquivo/Pasta/ASCII)
  2. Qualidade (Presets)
  3. Ferramentas (Calibrador/Webcam)
  4. Motor Grafico (ASCII/PixelArt)
  5. Conversao (Botoes)
  6. Progresso (Barra)
  7. Reproducao (Modo + Controles)
- Engrenagem de configuracoes movida para header
- Barra de progresso com altura aumentada (CSS override)
- Botoes de conversao com borda verde (#81c995)
- Label de selecao alinhado a direita com cor dinamica

#### Nova Aba: Preferencias
- Pasta de Entrada padrao (FileChooserButton)
- Pasta de Saida padrao (FileChooserButton)
- Motor Grafico padrao (ASCII/PixelArt)
- Qualidade padrao (Custom a Very High)
- Formato de Saida (txt/html/ansi)

#### Opcoes Expandidas do Player
- Limpar Tela Antes de Reproduzir
- Mostrar FPS Durante Reproducao
- Controle de Velocidade (0.5x a 2.0x)

### Sistema de Presets de Rampa de Luminancia

10 presets prontos para uso + modo manual:
- **Padrao** (70 chars) - Rampa completa classica
- **Simples** (10 chars) - `@%#*+=-:. `
- **Blocos Unicode** - Caracteres de bloco
- **Minimalista** (5 chars) - `#=:. `
- **Binario (Matrix)** - `10 `
- **Pontos** - Circulos graduados
- **Detalhado** - Versao densa
- **Letras** - Apenas caracteres alfabeticos
- **Numeros** - Apenas digitos
- **Setas/Simbolos** - Formas geometricas
- **Custom** - Edicao manual liberada

### Sistema de Paletas Fixas para Pixel Art

10 paletas retro/tematicas:
- **Game Boy** - 4 cores (verde classico)
- **CGA** - 16 cores (IBM PC)
- **NES** - 54 cores (Nintendo)
- **Commodore 64** - 16 cores
- **PICO-8** - 16 cores (fantasy console)
- **Escala de Cinza** - 8 tons
- **Sepia** - 8 tons (vintage)
- **Cyberpunk** - 12 cores neon
- **Dracula Theme** - 11 cores
- **Monitor Verde (CRT)** - 12 tons de verde

### Correcoes

- Corrigida acentuacao em toda a interface (Extase, Configuracoes, etc.)
- Botao "Converter Pasta" agora desativado quando sem selecao
- CSS Provider para override de estilos do tema GTK

### Arquivos Modificados
- `src/app/app.py` - CSS Provider, widgets, titulo
- `src/app/actions/file_actions.py` - Estados de botao, CSS dinamico
- `src/app/actions/options_actions.py` - Handlers de presets
- `src/app/constants.py` - LUMINANCE_RAMPS, FIXED_PALETTES
- `src/gui/main.glade` - Reorganizacao completa

---

## [2.0.0] - 2025-12-17

### 🛡️ Compliance & Estrutura
- **Reestruturação Completa de Diretórios:**
  - `src/ui` -> `src/gui`
  - `src/assets` -> `assets/` (Root)
  - Novos diretórios padronizados: `data_input/`, `data_output/`, `logs/`, `Dev_log/`
- **Protocolo de Logging:**
  - Substituição de `print` por `logger` rotacionado em `logs/system.log`
- **Documentação:**
  - README estritamente formatado conforme template visual
  - Scripts de lifecycle (`install.sh`, `uninstall.sh`) atualizados

### ✨ Novas Funcionalidades

#### Sistema de Presets de Qualidade
- Adicionado ComboBox com presets dinâmicos: Mobile (100x25), Low (120x30), Medium (180x45), High (240x60), Very High (300x75)
- Detecção automática de modo (ASCII vs Pixel Art) com labels apropriados
- Persistência de preset selecionado no `config.ini`

#### Modo Pixel Art Completo
- **6 níveis de qualidade baseados em profundidade de cor:**
  - 8-bit Low (100x25, 16 cores, pixel_size=6)
  - 8-bit High (120x30, 16 cores, pixel_size=5)
  - 16-bit Low (150x38, 64 cores, pixel_size=4)
  - 16-bit High (180x45, 64 cores, pixel_size=3)
  - 32-bit (240x60, 128 cores, pixel_size=2)
  - 64-bit (300x75, 256 cores, pixel_size=1)
- Controle automático de `pixel_size` e `palette_size` por preset
- Novos arquivos: `pixel_art_converter.py`, `pixel_art_image_converter.py`

#### Melhorias de Nitidez e Qualidade
- **Sharpen Filter** (Unsharp Mask) configurável via `config.ini`
  - Parâmetros: `sharpen_enabled` (bool), `sharpen_amount` (0.0-1.0)
  - Aplicado em todos os conversores (ASCII e Pixel Art)
- **Interpolação Lanczos** para redimensionamento (substitui INTER_AREA)
  - Maior preservação de detalhes e bordas

#### Calibrador Automático de Chroma Key
- **Auto-Detect** - Atalho `'a'` analisa frame e calcula ranges HSV automaticamente
- **3 Presets prontos:**
  - Studio (H:35-85, S:50+, V:50+) - Verde profissional de estúdio
  - Natural (H:35-90, S:30+, V:30+) - Verde natural/outdoor
  - Bright (H:40-80, S:80+, V:80+) - Verde vibrante/iluminado
- **Refinamento Morfológico de Bordas:**
  - Trackbar "Erode" (0-10) - Remove pixels isolados verdes
  - Trackbar "Dilate" (0-10) - Fecha buracos na máscara
- Atalho `'p'` para ciclar entre presets
- Função `auto_detect_green()` e `apply_morphological_refinement()`

#### Otimizações de Player e Interface
- **Zoom isolado no terminal do player:** `--zoom=0.6` (gnome-terminal) ou fonte `6x10` (xterm)
- Não afeta configurações de fonte de outros terminais do sistema
- Permite até ~400x100 caracteres na tela

#### Controle Expandido de Aspect Ratio
- Range do `char_aspect_ratio` expandido: **0.01 a 2.0** (antes: 0.1 a 2.0)
- Permite ajustes ultra-finos para resoluções altas

### 🔧 Modificações

#### Arquivos Modificados
- `src/main.py` - ComboBox de presets, detecção de modo, handlers
- `src/core/calibrator.py` - Auto-detect, presets, refinamento morfológico
- `src/core/converter.py` - Sharpen filter, Lanczos resize
- `src/core/image_converter.py` - Sharpen filter, Lanczos resize  
- `src/core/pixel_art_converter.py` - Sharpen filter, Lanczos resize
- `src/core/pixel_art_image_converter.py` - Sharpen filter, Lanczos resize
- `src/ui/main.glade` - Adjustment de aspect_ratio (mínimo 0.01)
- `config.ini` - Nova seção `[Quality]`, parâmetros sharpen

#### Novos Arquivos
- `src/core/pixel_art_converter.py` - Conversor Pixel Art para vídeo
- `src/core/pixel_art_image_converter.py` - Conversor Pixel Art para imagem

### 📊 Estatísticas
- **~500 linhas adicionadas** ao código
- **2 novos módulos** criados
- **6 presets de qualidade** para cada modo (ASCII e Pixel Art)
- **3 presets de chroma key** prontos para uso
- **Zoom mínimo:** 0.5 (testado com 0.6 como padrão)

### 👥 Contribuidores
- [@vitoriamaria](https://github.com/vitoriamaria) - Todas as funcionalidades desta versão

---

## [1.0.0] - Data Original

### Implementação Base
- Conversor ASCII básico
- Chroma Key manual
- Player de terminal
- Interface GTK
- Calibrador manual

**Desenvolvedor Original:** [AndreBFarias](https://github.com/AndreBFarias)
