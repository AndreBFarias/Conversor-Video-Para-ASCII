# Sprint 31: Fullscreen Unificado (GTK)

**Status:** CONCLUIDA
**Prioridade:** ALTA
**Dependencias:** Nenhuma

---

## 1. PROBLEMA

Ao clicar em qualquer acao de fullscreen (Reproduzir, Play ASCII, duplo-clique no RESULTADO do calibrador, ou Webcam Real-Time), o sistema abria um terminal externo (kitty/gnome-terminal) com renderizacao ANSI, visualmente incompativel com o painel RESULTADO do calibrador GTK.

**Resultado anterior:** Duas experiencias visuais incompativeis.
**Resultado obtido:** Mesma experiencia visual do calibrador em todas as situacoes de fullscreen, incluindo efeitos (Matrix Rain, PostFX).

---

## 2. SOLUCAO IMPLEMENTADA

### 2.1 Modulo: `src/core/gtk_fullscreen_player.py`

Janela GTK fullscreen que usa o mesmo pipeline de renderizacao do calibrador:

- `GtkFullscreenPlayer` - janela maximizada com AspectFrame e fundo preto
- `render_frame()` - pipeline completo: sharpen -> mask -> ASCII -> Matrix Rain -> PostFX
- `_apply_matrix_rain()` - portado do calibrador, respeita matrix_mode (user/background/overlay)
- `_init_effects()` - inicializa MatrixRainGPU com grid dimensions e PostFXProcessor com config completa
- `play_file_gtk()` - reproduz arquivos .txt ASCII com efeitos PostFX e Matrix Rain
- `play_realtime_gtk()` - webcam/video real-time com pipeline completo

### 2.2 Acoes: `src/app/actions/playback_actions.py`

- `_play_with_gtk()` lanca `gtk_fullscreen_player.py --file` via subprocess
- `_launch_player_gtk()` idem para Play ASCII
- Ambos passam `--config` e `--loop` quando habilitado

### 2.3 Acoes: `src/app/actions/calibration_actions.py`

- `_launch_webcam_gtk()` lanca `gtk_fullscreen_player.py` sem --file (usa webcam)
- `_launch_gtk_calibrator()` lanca calibrador GTK (inalterado)

### 2.4 Calibrador: `src/core/gtk_calibrator.py`

- Preview fullscreen (duplo-clique no RESULTADO) salva config temporaria completa com:
  - MatrixRain: enabled, mode, char_set, speed_multiplier, num_particles
  - PostFX: todos os booleans + intensidades, thresholds, spacings, etc
- Lanca `gtk_fullscreen_player.py --config <temp.ini> --video <video>`

### 2.5 Constantes: `src/app/constants.py`

- `GTK_FULLSCREEN_PLAYER_SCRIPT` aponta para o novo modulo

---

## 3. BUGS CORRIGIDOS (POS-IMPLEMENTACAO)

### 3.1 MatrixRainGPU - kwargs errados

`MatrixRainGPU(width=..., height=...)` causava TypeError silencioso porque o construtor espera `grid_w` e `grid_h` como posicionais.

**Correcao:** Usar argumentos posicionais `MatrixRainGPU(target_width, target_height, ...)`.

### 3.2 MatrixRainGPU - dimensoes erradas

Inicializava com dimensoes de pixel (1920x1080) em vez de dimensoes do grid ASCII (ex: 120x25).

**Correcao:** Usar `self.target_width` e `self.target_height`.

### 3.3 Matrix Rain render() - assinatura errada

Chamava `self._matrix_rain.render(result_image, mask)` mas render() espera `(canvas_char, canvas_color)` (arrays 2D de caracteres e cores).

**Correcao:** Implementar `_apply_matrix_rain()` completo: update() -> render em grids -> overlay com putText, respeitando matrix_mode.

### 3.4 play_file_gtk - sem efeitos

Usava `render_ascii_as_image()` direto sem aplicar PostFX ou Matrix Rain.

**Correcao:** Adicionar `_apply_file_effects()` que aplica Matrix Rain e PostFX apos o render.

### 3.5 Config temporaria incompleta

Calibrador nao passava `num_particles` nem parametros de intensidade do PostFX ao fullscreen.

**Correcao:** Salvar todos os parametros de MatrixRain e PostFX na config temporaria.

### 3.6 cleanup() - metodo inexistente

Chamava `self._matrix_rain.close()` mas MatrixRainGPU nao tem metodo `close()`.

**Correcao:** Substituir por `self._matrix_rain = None`.

---

## 4. ARQUIVOS MODIFICADOS

| Arquivo | Acao |
|---------|------|
| `src/core/gtk_fullscreen_player.py` | CRIADO - Player fullscreen GTK com pipeline completo |
| `src/app/actions/playback_actions.py` | MODIFICADO - Usa GTK em vez de terminal |
| `src/app/actions/calibration_actions.py` | MODIFICADO - Webcam usa GTK |
| `src/core/gtk_calibrator.py` | MODIFICADO - Preview passa config completa |
| `src/app/constants.py` | MODIFICADO - GTK_FULLSCREEN_PLAYER_SCRIPT |

---

## 5. CRITERIOS DE ACEITACAO

- [x] Botao "Reproduzir" abre janela GTK fullscreen (nao terminal)
- [x] Botao "Play ASCII" abre janela GTK fullscreen (nao terminal)
- [x] Duplo-clique no RESULTADO do calibrador abre janela GTK fullscreen
- [x] Botao "Webcam Real-Time" abre janela GTK fullscreen com webcam
- [x] Visual identico ao painel RESULTADO do calibrador
- [x] Fundo preto, caracteres coloridos, proporcao mantida (AspectFrame)
- [x] ESC ou 'q' fecha a janela fullscreen
- [x] Loop funciona na reproducao de arquivos
- [x] Imagens estaticas (fps=0) exibem e aguardam ESC
- [x] Matrix Rain funciona no fullscreen (modo user/background/overlay)
- [x] PostFX funciona no fullscreen (Bloom, Chromatic, Scanlines, Glitch)
- [x] Efeitos persistem durante toda a reproducao (nao desaparecem)

---

## 6. VERIFICACAO

```bash
python3 src/core/gtk_fullscreen_player.py --config config.ini --file data_output/sample.txt
python3 src/core/gtk_fullscreen_player.py --config config.ini
python3 src/core/gtk_fullscreen_player.py --config config.ini --video input.mp4
```
