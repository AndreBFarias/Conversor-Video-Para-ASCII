# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.0.0] - 2025-12-10

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
