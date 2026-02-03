# Sprint 31: Fullscreen Unificado (GTK)

**Status:** PENDENTE
**Prioridade:** ALTA
**Dependencias:** Nenhuma
**Estimativa de Complexidade:** Media-Alta

---

## 1. PROBLEMA

Ao clicar em qualquer acao de fullscreen (Reproduzir, Play ASCII, duplo-clique no RESULTADO do calibrador, ou Webcam Real-Time), o sistema abre um **terminal externo** (kitty/gnome-terminal/xterm) que renderiza ASCII com ANSI escape codes. Esse terminal tem visual completamente diferente da janela de RESULTADO do calibrador, que renderiza ASCII como imagem (cv2.putText em canvas NumPy exibido em widget GTK).

**Resultado atual:** Duas experiencias visuais incompativeis - uma bonita (calibrador GTK) e uma crua (terminal ANSI).

**Resultado desejado:** A mesma experiencia visual do RESULTADO do calibrador em todas as situacoes de fullscreen.

---

## 2. CAUSA RAIZ

Existem 2 pipelines de renderizacao distintos:

### Pipeline A: RESULTADO do Calibrador (o bom)
```
Frame RGB -> cv2.resize -> Sobel -> _render_ascii_to_image() -> cv2.putText no canvas -> Gtk.Image
```
- Arquivo: `src/core/gtk_calibrator.py` funcao `_render_ascii_to_image()` (linha 899)
- Renderiza cada caractere ASCII com cv2.putText em um canvas NumPy (imagem)
- Exibe como GdkPixbuf em Gtk.Image dentro de Gtk.AspectFrame
- Fundo preto, caracteres coloridos, proporcao mantida

### Pipeline B: Terminal Externo (o ruim)
```
Frame RGB -> cv2.resize -> Sobel -> frame_para_ascii_rt() -> ANSI codes -> stdout -> terminal
```
- Arquivo: `src/core/realtime_ascii.py` funcao `frame_para_ascii_rt()` (linha 68)
- Renderiza com sequencias ANSI escape `\033[38;5;{code}m{char}` diretamente no terminal
- Visual depende da fonte do terminal, tamanho, cores do emulador
- Completamente diferente do calibrador

### Onde cada fluxo eh chamado:

| Acao do Usuario | Codigo que Lanca | Pipeline |
|-----------------|------------------|----------|
| Botao "Reproduzir" | `playback_actions.py:18` `_play_with_terminal()` | B (terminal kitty + cli_player.py) |
| Botao "Play ASCII" | `playback_actions.py:68` `_launch_player_in_terminal()` | B (terminal kitty + cli_player.py) |
| Duplo-clique RESULTADO | `gtk_calibrator.py:525` `_save_and_open_preview()` | B (terminal kitty + realtime_ascii.py) |
| Botao "Webcam Real-Time" | `calibration_actions.py:26` `_launch_webcam_in_terminal()` | B (terminal kitty + realtime_ascii.py) |

---

## 3. SOLUCAO

Substituir TODOS os lancamentos de terminal externo por janelas GTK fullscreen que usam o mesmo renderer do calibrador (`_render_ascii_to_image()`).

### 3.1 Criar Novo Modulo: `src/core/gtk_fullscreen_player.py`

Este modulo centraliza a renderizacao GTK para TODAS as situacoes de fullscreen.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import cv2
import numpy as np
import time
import os
import sys
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR
from src.core.utils.image import sharpen_frame, apply_morphological_refinement

try:
    from src.core.auto_segmenter import AutoSegmenter, is_available as auto_seg_available
    AUTO_SEG_AVAILABLE = auto_seg_available()
except ImportError:
    AUTO_SEG_AVAILABLE = False
    AutoSegmenter = None

try:
    from src.core.matrix_rain_gpu import MatrixRainGPU
    MATRIX_RAIN_AVAILABLE = True
except Exception:
    MATRIX_RAIN_AVAILABLE = False

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except Exception:
    POSTFX_AVAILABLE = False


class GtkFullscreenPlayer(Gtk.Window):
    """
    Janela GTK fullscreen que renderiza ASCII art como imagem,
    usando o MESMO pipeline visual do calibrador.

    Substitui o terminal externo (kitty/gnome-terminal) em TODAS
    as situacoes de fullscreen: play, play ASCII, webcam realtime.
    """

    def __init__(self, config, title="Extase em 4R73 - Player", start_maximized=True):
        super().__init__(title=title)

        self.config = config
        self.should_close = False
        self._last_render_time = 0.0

        self.set_wmclass("extase-em-4r73", "Extase em 4R73")
        self.set_position(Gtk.WindowPosition.CENTER)

        if start_maximized:
            self.maximize()
        else:
            self.set_default_size(1280, 720)

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"window { background-color: #000000; }")
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.aspect_frame = Gtk.AspectFrame(
            xalign=0.5, yalign=0.5, ratio=16/9, obey_child=False
        )
        self.image_widget = Gtk.Image()
        self.aspect_frame.add(self.image_widget)
        self.add(self.aspect_frame)

        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", self._on_destroy)

        self._load_conversion_params()

    def _load_conversion_params(self):
        """Carrega parametros de conversao do config (mesmo que calibrador)."""
        c = self.config
        self.target_width = c.getint('Conversor', 'target_width', fallback=85)
        self.target_height = c.getint('Conversor', 'target_height', fallback=44)
        self.sobel_threshold = c.getint('Conversor', 'sobel_threshold', fallback=10)
        self.luminance_ramp = c.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
        self.sharpen_enabled = c.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        self.sharpen_amount = c.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        self.edge_boost_enabled = c.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
        self.edge_boost_amount = c.getint('Conversor', 'edge_boost_amount', fallback=100)
        self.use_edge_chars = c.getboolean('Conversor', 'use_edge_chars', fallback=True)
        self.char_aspect_ratio = c.getfloat('Conversor', 'char_aspect_ratio', fallback=1.0)

        render_mode_str = c.get('Conversor', 'render_mode', fallback='both').lower()
        self.render_mode = {'user': 0, 'background': 1, 'both': 2}.get(render_mode_str, 2)

        self.auto_seg_enabled = c.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
        self.temporal_enabled = c.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
        self.temporal_threshold = c.getint('Conversor', 'temporal_threshold', fallback=50)

        self.matrix_enabled = c.getboolean('MatrixRain', 'enabled', fallback=False)
        self.postfx_enabled = False

        if POSTFX_AVAILABLE:
            bloom = c.getboolean('PostFX', 'bloom_enabled', fallback=False)
            chromatic = c.getboolean('PostFX', 'chromatic_enabled', fallback=False)
            scanlines = c.getboolean('PostFX', 'scanlines_enabled', fallback=False)
            glitch = c.getboolean('PostFX', 'glitch_enabled', fallback=False)
            if bloom or chromatic or scanlines or glitch:
                self.postfx_enabled = True

        self._auto_segmenter = None
        self._matrix_rain = None
        self._postfx_processor = None
        self._prev_gray_frame = None

    def _init_effects(self):
        """Inicializa efeitos sob demanda (chamado no primeiro frame)."""
        c = self.config

        if self.auto_seg_enabled and AUTO_SEG_AVAILABLE and not self._auto_segmenter:
            try:
                self._auto_segmenter = AutoSegmenter(threshold=0.5, use_gpu=False)
            except Exception:
                self._auto_segmenter = None

        if self.matrix_enabled and MATRIX_RAIN_AVAILABLE and not self._matrix_rain:
            try:
                charset = c.get('MatrixRain', 'char_set', fallback='katakana')
                self._matrix_rain = MatrixRainGPU(width=1280, height=720, char_set=charset)
                self._matrix_rain.mode = c.get('MatrixRain', 'mode', fallback='user')
                self._matrix_rain.speed_multiplier = c.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)
            except Exception:
                self._matrix_rain = None

        if self.postfx_enabled and POSTFX_AVAILABLE and not self._postfx_processor:
            try:
                pconfig = PostFXConfig(
                    bloom_enabled=c.getboolean('PostFX', 'bloom_enabled', fallback=False),
                    bloom_intensity=c.getfloat('PostFX', 'bloom_intensity', fallback=1.2),
                    bloom_radius=c.getint('PostFX', 'bloom_radius', fallback=21),
                    bloom_threshold=c.getint('PostFX', 'bloom_threshold', fallback=80),
                    chromatic_enabled=c.getboolean('PostFX', 'chromatic_enabled', fallback=False),
                    chromatic_shift=c.getint('PostFX', 'chromatic_shift', fallback=12),
                    scanlines_enabled=c.getboolean('PostFX', 'scanlines_enabled', fallback=False),
                    scanlines_intensity=c.getfloat('PostFX', 'scanlines_intensity', fallback=0.7),
                    scanlines_spacing=c.getint('PostFX', 'scanlines_spacing', fallback=2),
                    glitch_enabled=c.getboolean('PostFX', 'glitch_enabled', fallback=False),
                    glitch_intensity=c.getfloat('PostFX', 'glitch_intensity', fallback=0.6),
                    glitch_block_size=c.getint('PostFX', 'glitch_block_size', fallback=8),
                )
                self._postfx_processor = PostFXProcessor(pconfig, use_gpu=False)
            except Exception:
                self._postfx_processor = None

    def render_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Processa um frame BGR e retorna imagem ASCII renderizada.
        USA O MESMO PIPELINE DO CALIBRADOR (gtk_calibrator.py:1125-1177).
        """
        self._init_effects()

        if self.sharpen_enabled:
            frame_bgr = sharpen_frame(frame_bgr, self.sharpen_amount)

        frame_h, frame_w = frame_bgr.shape[:2]

        # Segmentacao / ChromaKey
        mask = self._compute_mask(frame_bgr)

        # Redimensionar para resolucao ASCII
        target_dims = (self.target_width, self.target_height)
        grayscale = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        resized_gray = cv2.resize(grayscale, target_dims, interpolation=cv2.INTER_AREA)
        resized_color = cv2.resize(frame_bgr, target_dims, interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(mask, target_dims, interpolation=cv2.INTER_NEAREST)

        # Sobel
        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        # Temporal Coherence
        if self.temporal_enabled and self._prev_gray_frame is not None:
            diff = np.abs(resized_gray.astype(np.int32) - self._prev_gray_frame.astype(np.int32))
            temporal_mask = diff < self.temporal_threshold
            resized_gray = np.where(temporal_mask, self._prev_gray_frame, resized_gray).astype(np.uint8)
        self._prev_gray_frame = resized_gray.copy()

        # Renderizar ASCII como imagem (MESMO METODO DO CALIBRADOR)
        alloc = self.get_allocation()
        canvas_w = max(640, alloc.width)
        canvas_h = max(480, alloc.height)

        result_image = self._render_ascii_to_image(
            resized_gray, resized_color, resized_mask,
            magnitude_norm, angle, canvas_h, canvas_w
        )

        # Matrix Rain (pos-render, como no calibrador linha 1168-1169)
        if self._matrix_rain and self.matrix_enabled:
            user_mask_for_rain = cv2.bitwise_not(resized_mask) if mask is not None else None
            result_image = self._matrix_rain.render(result_image, user_mask_for_rain)

        # PostFX (pos-render, como no calibrador linha 1174-1175)
        if self._postfx_processor and self.postfx_enabled:
            result_image = self._postfx_processor.process(result_image)

        return result_image

    def _compute_mask(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Calcula mascara de segmentacao (Auto Seg ou ChromaKey)."""
        frame_h, frame_w = frame_bgr.shape[:2]

        if self._auto_segmenter:
            try:
                max_size = 320
                if max(frame_h, frame_w) > max_size:
                    scale = max_size / max(frame_h, frame_w)
                    small = cv2.resize(frame_bgr, (int(frame_w * scale), int(frame_h * scale)))
                    small_mask = self._auto_segmenter.process(small)
                    return cv2.resize(small_mask, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)
                return self._auto_segmenter.process(frame_bgr)
            except Exception:
                pass

        c = self.config
        h_min = c.getint('ChromaKey', 'h_min', fallback=35)
        h_max = c.getint('ChromaKey', 'h_max', fallback=85)
        s_min = c.getint('ChromaKey', 's_min', fallback=40)
        s_max = c.getint('ChromaKey', 's_max', fallback=255)
        v_min = c.getint('ChromaKey', 'v_min', fallback=40)
        v_max = c.getint('ChromaKey', 'v_max', fallback=255)
        erode = c.getint('ChromaKey', 'erode', fallback=2)
        dilate = c.getint('ChromaKey', 'dilate', fallback=2)

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max]))
        return apply_morphological_refinement(mask, erode, dilate)

    def _render_ascii_to_image(self, resized_gray, resized_color, resized_mask,
                                magnitude_norm, angle, canvas_h, canvas_w) -> np.ndarray:
        """
        COPIA EXATA de gtk_calibrator.py:_render_ascii_to_image() (linha 899-983).
        Renderiza ASCII art como imagem BGR usando cv2.putText.
        """
        height, width = resized_gray.shape

        if height <= 0 or width <= 0 or canvas_h <= 0 or canvas_w <= 0:
            return np.zeros((max(1, canvas_h), max(1, canvas_w), 3), dtype=np.uint8)

        ascii_image = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        char_w_base = 8
        char_h_base = 16

        scale_x = canvas_w / (width * char_w_base)
        scale_y = canvas_h / (height * char_h_base)
        scale = min(scale_x, scale_y)

        char_w = max(1, int(char_w_base * scale))
        char_h = max(1, int(char_h_base * scale))

        total_w = width * char_w
        total_h = height * char_h

        offset_x = (canvas_w - total_w) // 2
        offset_y = (canvas_h - total_h) // 2

        font_scale = max(0.25, 0.35 * scale)

        luminance_ramp = self.luminance_ramp
        ramp_len = len(luminance_ramp)
        sobel_threshold = self.sobel_threshold

        is_edge = magnitude_norm > sobel_threshold

        if self.edge_boost_enabled:
            brightness = resized_gray.astype(np.int32)
            edge_boost = is_edge.astype(np.int32) * self.edge_boost_amount
            brightness = np.clip(brightness + edge_boost, 0, 255)
            lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
        else:
            lum_indices = (resized_gray * (ramp_len - 1) / 255).astype(np.int32)

        RENDER_MODE_USER = 0
        RENDER_MODE_BACKGROUND = 1

        for y in range(height):
            py = offset_y + y * char_h + char_h - 3

            for x in range(width):
                is_chroma = resized_mask[y, x] > 127

                if self.render_mode == RENDER_MODE_USER:
                    if is_chroma:
                        continue
                elif self.render_mode == RENDER_MODE_BACKGROUND:
                    if not is_chroma:
                        continue

                mag = magnitude_norm[y, x]
                ang = angle[y, x]

                if self.use_edge_chars and mag > sobel_threshold:
                    if 22.5 <= ang < 67.5 or 157.5 <= ang < 202.5:
                        char = '/'
                    elif 67.5 <= ang < 112.5 or 247.5 <= ang < 292.5:
                        char = '|'
                    elif 112.5 <= ang < 157.5 or 292.5 <= ang < 337.5:
                        char = '\\'
                    else:
                        char = '-'
                else:
                    char = luminance_ramp[lum_indices[y, x]]

                b, g, r = resized_color[y, x]
                px = offset_x + x * char_w
                rect_y = offset_y + y * char_h

                if char.strip():
                    cv2.putText(ascii_image, char, (px, py),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                (int(b), int(g), int(r)), 1)
                else:
                    cv2.rectangle(ascii_image, (px, rect_y),
                                  (px + char_w, rect_y + char_h),
                                  (int(b), int(g), int(r)), -1)

        return ascii_image

    def display_frame(self, result_image: np.ndarray):
        """Exibe imagem renderizada no widget GTK."""
        if result_image is None or result_image.size == 0:
            return

        h, w = result_image.shape[:2]
        self.aspect_frame.set_property("ratio", w / h)

        rgb = result_image[:, :, ::-1].copy()
        if not rgb.flags['C_CONTIGUOUS']:
            rgb = np.ascontiguousarray(rgb)

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            rgb.tobytes(), GdkPixbuf.Colorspace.RGB,
            False, 8, w, h, w * 3, None, None
        )
        self.image_widget.set_from_pixbuf(pixbuf.copy())

    def process_events(self):
        """Processa eventos GTK pendentes."""
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ['q', 'Q', 'Escape']:
            self.should_close = True
            Gtk.main_quit()
            return True
        return False

    def _on_destroy(self, widget):
        self.should_close = True
        self.cleanup()
        Gtk.main_quit()

    def cleanup(self):
        """Libera recursos."""
        if self._auto_segmenter:
            try:
                self._auto_segmenter.close()
            except Exception:
                pass
        if self._matrix_rain:
            try:
                self._matrix_rain.close()
            except Exception:
                pass


def play_file_gtk(arquivo_path: str, config, loop: bool = False):
    """
    Reproduz arquivo .txt ASCII em janela GTK fullscreen.
    Substitui _play_with_terminal() de playback_actions.py.
    """
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' nao encontrado.")

    with open(arquivo_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('\n', 1)
    if len(parts) < 2:
        raise ValueError("Formato de arquivo invalido.")

    fps = float(parts[0].strip())
    frame_content = parts[1]
    if frame_content.startswith("[FRAME]\n"):
        frame_content = frame_content[len("[FRAME]\n"):]
    frames = frame_content.split("[FRAME]\n")

    if not frames or all(not f.strip() for f in frames):
        raise ValueError("Nenhum frame valido encontrado.")

    from src.core.renderer import render_ascii_as_image

    window = GtkFullscreenPlayer(config, title="Extase em 4R73 - Player")
    window.show_all()

    is_static = (fps == 0)
    delay = 1.0 / fps if fps > 0 else 0

    try:
        if is_static:
            img = render_ascii_as_image(frames[0])
            if img is not None:
                window.display_frame(img)
            Gtk.main()
        else:
            while not window.should_close:
                for frame_data in frames:
                    if window.should_close or not frame_data.strip():
                        break

                    img = render_ascii_as_image(frame_data)
                    if img is not None:
                        window.display_frame(img)

                    window.process_events()
                    if window.should_close:
                        break

                    time.sleep(delay)

                if not loop:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        window.cleanup()


def play_realtime_gtk(config, video_path: str = None):
    """
    Executa conversao real-time (webcam ou video) em janela GTK fullscreen.
    Substitui _launch_webcam_in_terminal() de calibration_actions.py.
    """
    capture_source = video_path if video_path else 0
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        raise IOError(f"Nao foi possivel abrir: {capture_source}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    is_video = video_path is not None

    window = GtkFullscreenPlayer(config, title="Extase em 4R73 - Real-Time")
    window.show_all()

    try:
        while not window.should_close:
            ret, frame = cap.read()
            if not ret:
                if is_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            if not is_video:
                frame = cv2.flip(frame, 1)

            result = window.render_frame(frame)
            window.display_frame(result)
            window.process_events()

            if window.should_close:
                break

            time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        window.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GTK Fullscreen ASCII Player")
    parser.add_argument("--config", required=True, help="Caminho para config.ini")
    parser.add_argument("--file", default=None, help="Arquivo .txt ASCII para reproduzir")
    parser.add_argument("--video", default=None, help="Arquivo de video para real-time")
    parser.add_argument("--loop", action="store_true", help="Loop na reproducao")
    args = parser.parse_args()

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    if args.file:
        play_file_gtk(args.file, config, args.loop)
    else:
        play_realtime_gtk(config, args.video)
```

---

### 3.2 Modificar: `src/app/actions/playback_actions.py`

**O que mudar:** Substituir `_play_with_terminal()` e `_launch_player_in_terminal()` para usar GTK ao inves de terminal.

**Codigo atual (linha 18-60):** Lanca `kitty` com `cli_player.py` como subprocesso.

**Codigo novo:**
```python
def _play_with_terminal(self):
    if not self.selected_file_path:
        return

    media_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
    file_path = os.path.join(self.output_dir, media_name)
    if not os.path.exists(file_path):
        self.show_error_dialog("Erro", f"Arquivo ASCII '{os.path.basename(file_path)}' nao encontrado.\nConverta o arquivo primeiro.")
        return

    loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']

    python_executable = self._get_python_executable()
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          '..', 'core', 'gtk_fullscreen_player.py')
    script = os.path.normpath(script)

    cmd = [python_executable, script,
           '--config', self.config_path,
           '--file', file_path]
    if loop_enabled:
        cmd.append('--loop')

    try:
        self.logger.info(f"Executando player GTK: {' '.join(cmd)}")
        subprocess.Popen(cmd)
    except Exception as e:
        self.show_error_dialog("Erro Player", f"Nao foi possivel abrir o player:\n{e}")
```

**Fazer o mesmo para `_launch_player_in_terminal()` (linha 68-82).**

---

### 3.3 Modificar: `src/app/actions/calibration_actions.py`

**O que mudar:** Substituir `_launch_webcam_in_terminal()` para usar GTK.

**Codigo atual (linha 26-60):** Lanca `kitty` com `realtime_ascii.py`.

**Codigo novo:**
```python
def _launch_webcam_in_terminal(self):
    python_executable = self._get_python_executable()
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          '..', 'core', 'gtk_fullscreen_player.py')
    script = os.path.normpath(script)

    cmd = [python_executable, script, "--config", self.config_path]

    try:
        self.logger.info(f"Executando webcam GTK: {' '.join(cmd)}")
        subprocess.Popen(cmd)
    except Exception as e:
        self.show_error_dialog("Erro Webcam", f"Nao foi possivel abrir:\n{e}")
```

---

### 3.4 Modificar: `src/core/gtk_calibrator.py`

**O que mudar:** `_open_terminal_preview()` (linha 1512-1631) deve usar GTK ao inves de terminal.

**Codigo novo para `_open_terminal_preview()`:**
```python
def _open_terminal_preview(self):
    try:
        script = os.path.join(BASE_DIR, "src", "core", "gtk_fullscreen_player.py")
        python_exec = sys.executable

        cmd = [python_exec, script, "--config", self.config_path]

        if self.video_path:
            cmd.extend(["--video", self.video_path])

        subprocess.Popen(cmd)
        self._set_status("Preview GTK aberto")
    except Exception as e:
        self._set_status(f"Erro ao abrir preview: {e}")
```

---

### 3.5 Adicionar Constante: `src/app/constants.py`

Adicionar:
```python
GTK_FULLSCREEN_PLAYER_SCRIPT = os.path.join(ROOT_DIR, "src", "core", "gtk_fullscreen_player.py")
```

---

## 4. ARQUIVOS A MODIFICAR

| Arquivo | Acao | O Que Fazer |
|---------|------|-------------|
| `src/core/gtk_fullscreen_player.py` | CRIAR | Modulo novo com GtkFullscreenPlayer + funcoes play_file_gtk e play_realtime_gtk |
| `src/app/actions/playback_actions.py` | MODIFICAR | Substituir _play_with_terminal e _launch_player_in_terminal |
| `src/app/actions/calibration_actions.py` | MODIFICAR | Substituir _launch_webcam_in_terminal |
| `src/core/gtk_calibrator.py` | MODIFICAR | Substituir _open_terminal_preview (linha 1512) |
| `src/app/constants.py` | MODIFICAR | Adicionar GTK_FULLSCREEN_PLAYER_SCRIPT |

---

## 5. CRITERIOS DE ACEITACAO

- [ ] Botao "Reproduzir" abre janela GTK fullscreen (nao terminal)
- [ ] Botao "Play ASCII" abre janela GTK fullscreen (nao terminal)
- [ ] Duplo-clique no RESULTADO do calibrador abre janela GTK fullscreen
- [ ] Botao "Webcam Real-Time" abre janela GTK fullscreen com webcam
- [ ] Visual da janela fullscreen eh IDENTICO ao painel RESULTADO do calibrador
- [ ] Fundo preto, caracteres coloridos, proporcao mantida (AspectFrame)
- [ ] ESC ou 'q' fecha a janela fullscreen
- [ ] Webcam real-time mantem pelo menos 15 FPS na janela GTK
- [ ] Loop funciona corretamente na reproducao de arquivos
- [ ] Imagens estaticas (fps=0) exibem e aguardam ESC

---

## 6. RISCOS E MITIGACOES

| Risco | Mitigacao |
|-------|-----------|
| Performance GTK inferior ao terminal para real-time | O calibrador ja faz isso a ~15-30 FPS. O fullscreen usa o mesmo pipeline |
| Conflito GTK se app principal e player usarem o mesmo loop | Player eh lancado como subprocess separado (Popen), nao compartilha processo GTK |
| Webcam pode nao ser liberada entre calibrador e player | Calibrador fecha a webcam antes de abrir preview (ja implementado em _save_and_open_preview) |
| Usuarios que dependem do terminal (kitty) para reproduzir | Manter realtime_ascii.py e cli_player.py como alternativa, sem deletar |

---

## 7. VERIFICACAO

```bash
# 1. Testar player de arquivo
python3 src/core/gtk_fullscreen_player.py --config config.ini --file data_output/sample.txt

# 2. Testar webcam real-time
python3 src/core/gtk_fullscreen_player.py --config config.ini

# 3. Testar via app principal
python3 main.py
# -> Selecionar video -> Converter -> Clicar "Reproduzir"
# -> Verificar que abre janela GTK (nao terminal)

# 4. Testar duplo-clique no calibrador
python3 src/core/gtk_calibrator.py --config config.ini
# -> Duplo-clique na area ASCII -> Verificar que abre janela GTK

# 5. Comparar visual: calibrador RESULTADO vs fullscreen devem ser identicos
```
