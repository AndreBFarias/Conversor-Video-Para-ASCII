# Sprint 33: Aba Preview + Bidirecionalidade

**Status:** CONCLUIDO
**Prioridade:** ALTA
**Dependencias:** Sprint 31 (usa GtkFullscreenPlayer como referencia de pipeline)
**Estimativa de Complexidade:** Alta

---

## 1. PROBLEMA

### 1.1 Preview Ausente
A interface principal tem um `preview_frame` (Glade linha 772) que so aparece durante conversoes MP4/GIF/HTML e some ao terminar. NAO existe preview permanente que permita ao usuario ver como ficara a conversao ASCII ANTES de converter.

O usuario quer uma aba "Preview" na area de selecao (ao lado dos botoes Arquivo/Pasta/ASCII .txt) que mostra o primeiro frame do video selecionado convertido para ASCII em tempo real, usando o mesmo visual do painel RESULTADO do calibrador.

### 1.2 Falta de Bidirecionalidade
Quando o usuario altera parametros no calibrador e salva, a app principal recarrega config.ini (`reload_config()` em calibration_actions.py:69). Mas:
- NAO atualiza nenhum preview na app principal
- NAO ha feedback visual imediato de que os parametros mudaram
- Se o usuario altera parametros no dialog de Opcoes da app principal, o calibrador (se estiver aberto) nao ve as mudancas

**Resultado desejado:** Mudar parametro em qualquer lugar atualiza o preview automaticamente.

---

## 2. CONTEXTO TECNICO

### 2.1 Estrutura Atual do Glade (main.glade)

Layout da sidebar esquerda (vertical):
```
main_window
  VBox principal
    [Logo + Titulo + Config]          <- posicao 0
    [Frame: Selecionar]               <- posicao 1 (Arquivo, Pasta, ASCII .txt)
    [Frame: Conversao]                <- posicao 2
    [Frame: Qualidade]                <- posicao 3 (oculto)
    [Frame: Reproducao]               <- posicao 4
    [Frame: Ferramentas]              <- posicao 5
    [Frame: Motor Grafico]            <- posicao 6
    [ProgressBar]                     <- posicao 7
  preview_frame (separado, visible=False)  <- filho direto do window
```

A area de selecao (posicao 1 no Glade, linhas 217-330) contem:
- Box horizontal com 3 botoes: Arquivo (pos 0), Pasta (pos 1), ASCII .txt (pos 2)
- Label `selected_path_label`

### 2.2 Preview Existente (conversion_actions.py)

O `preview_frame` atual:
- Widget: `GtkFrame` id=`preview_frame` (Glade linha 772)
- Imagem: `GtkImage` id=`preview_thumbnail` (Glade linha 779)
- Ativado em: `_update_thumbnail()` (conversion_actions.py:263)
- Desativado em: `_hide_thumbnail()` (conversion_actions.py:326)
- So funciona durante conversao MP4/GIF/HTML via progress_cb callback

### 2.3 Calibrador - Fluxo de Salvamento

Quando o calibrador salva:
1. `on_save_config_clicked()` (gtk_calibrator.py:2456) escreve config.ini
2. `_close_after_save()` (gtk_calibrator.py:2570) fecha o calibrador
3. App principal detecta em `_launch_gtk_calibrator()` (calibration_actions.py:62): `subprocess.run()` bloqueia ate o calibrador fechar
4. `reload_config()` (calibration_actions.py:69) recarrega config.ini

NAO ha nenhuma atualizacao de preview apos reload.

---

## 3. SOLUCAO

### 3.1 Visao Geral da Arquitetura

```
[Botao "Preview"] <- Novo botao na area de selecao
       |
       v
[preview_expander] <- GtkExpander (expansivel/colapsavel)
       |
       v
[preview_ascii_image] <- GtkImage dentro de AspectFrame
       |
       v (alimentado por)
[PreviewEngine] <- Novo mixin que captura primeiro frame e renderiza
       |
       v (usa)
[_render_ascii_to_image()] <- Mesmo pipeline do calibrador
       |
       v (atualiza quando)
[config.ini muda] <- File watcher via GLib.timeout_add
```

### 3.2 Criar Novo Mixin: `src/app/actions/preview_actions.py`

```python
import os
import cv2
import numpy as np
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf

from src.core.utils.ascii_converter import LUMINANCE_RAMP_DEFAULT
from src.core.utils.image import sharpen_frame, apply_morphological_refinement


class PreviewActionsMixin:
    """
    Mixin para preview em tempo real na app principal.
    Renderiza primeiro frame do video selecionado como ASCII art.
    Usa o MESMO pipeline visual do calibrador (cv2.putText em canvas).
    """

    def _init_preview(self):
        """Chamado em App.__init__() apos _get_widgets()."""
        self._preview_visible = False
        self._preview_config_mtime = 0
        self._preview_frame_data = None
        self._preview_thread = None

    def on_preview_button_clicked(self, widget):
        """Handler do botao Preview na area de selecao."""
        if not hasattr(self, 'preview_expander') or not self.preview_expander:
            return

        is_expanded = self.preview_expander.get_expanded()

        if is_expanded:
            self.preview_expander.set_expanded(False)
            self._preview_visible = False
            self.window.resize(1, 1)
        else:
            self.preview_expander.set_expanded(True)
            self._preview_visible = True
            self._refresh_preview()

    def _refresh_preview(self):
        """Atualiza preview com o frame mais recente. Thread-safe."""
        if not self._preview_visible:
            return

        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            self._set_preview_placeholder("Selecione um video para preview")
            return

        if self._preview_thread and self._preview_thread.is_alive():
            return

        self._preview_thread = threading.Thread(
            target=self._generate_preview_frame,
            daemon=True
        )
        self._preview_thread.start()

    def _generate_preview_frame(self):
        """Gera frame de preview em background thread."""
        try:
            file_path = self.selected_file_path
            if not file_path or not os.path.exists(file_path):
                return

            from ..constants import VIDEO_EXTENSIONS, IMAGE_EXTENSIONS

            if file_path.lower().endswith(IMAGE_EXTENSIONS):
                frame = cv2.imread(file_path)
            elif file_path.lower().endswith(VIDEO_EXTENSIONS):
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    GLib.idle_add(self._set_preview_placeholder, "Erro ao abrir video")
                    return
                ret, frame = cap.read()
                cap.release()
                if not ret or frame is None:
                    GLib.idle_add(self._set_preview_placeholder, "Erro ao ler frame")
                    return
            else:
                GLib.idle_add(self._set_preview_placeholder, "Formato nao suportado")
                return

            result_image = self._render_preview_frame(frame)

            if result_image is not None:
                GLib.idle_add(self._display_preview_image, result_image)

        except Exception as e:
            self.logger.error(f"Erro ao gerar preview: {e}")
            GLib.idle_add(self._set_preview_placeholder, f"Erro: {e}")

    def _render_preview_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Renderiza frame como ASCII art.
        MESMO PIPELINE do calibrador (gtk_calibrator.py:1125-1177).
        """
        self.reload_config()
        c = self.config

        target_width = c.getint('Conversor', 'target_width', fallback=85)
        target_height = c.getint('Conversor', 'target_height', fallback=44)
        sobel_threshold = c.getint('Conversor', 'sobel_threshold', fallback=10)
        luminance_ramp = c.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
        sharpen_enabled = c.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = c.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        edge_boost_enabled = c.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
        edge_boost_amount = c.getint('Conversor', 'edge_boost_amount', fallback=100)
        use_edge_chars = c.getboolean('Conversor', 'use_edge_chars', fallback=True)

        render_mode_str = c.get('Conversor', 'render_mode', fallback='both').lower()
        RENDER_MODE_USER = 0
        RENDER_MODE_BACKGROUND = 1
        RENDER_MODE_BOTH = 2
        render_mode = {'user': 0, 'background': 1, 'both': 2}.get(render_mode_str, 2)

        if sharpen_enabled:
            frame_bgr = sharpen_frame(frame_bgr, sharpen_amount)

        frame_h, frame_w = frame_bgr.shape[:2]

        # ChromaKey mask
        h_min = c.getint('ChromaKey', 'h_min', fallback=35)
        h_max = c.getint('ChromaKey', 'h_max', fallback=85)
        s_min = c.getint('ChromaKey', 's_min', fallback=40)
        s_max = c.getint('ChromaKey', 's_max', fallback=255)
        v_min = c.getint('ChromaKey', 'v_min', fallback=40)
        v_max = c.getint('ChromaKey', 'v_max', fallback=255)
        erode = c.getint('ChromaKey', 'erode', fallback=2)
        dilate_val = c.getint('ChromaKey', 'dilate', fallback=2)

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv,
                           np.array([h_min, s_min, v_min]),
                           np.array([h_max, s_max, v_max]))
        mask = apply_morphological_refinement(mask, erode, dilate_val)

        # Resize para resolucao ASCII
        target_dims = (target_width, target_height)
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

        # Renderizar ASCII como imagem
        # Canvas de 640x480 para preview (proporcional)
        canvas_w = 640
        canvas_h = 480
        ascii_image = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        height, width = resized_gray.shape
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
        ramp_len = len(luminance_ramp)

        is_edge = magnitude_norm > sobel_threshold

        if edge_boost_enabled:
            brightness = resized_gray.astype(np.int32)
            edge_boost = is_edge.astype(np.int32) * edge_boost_amount
            brightness = np.clip(brightness + edge_boost, 0, 255)
            lum_indices = ((brightness / 255) * (ramp_len - 1)).astype(np.int32)
        else:
            lum_indices = (resized_gray * (ramp_len - 1) / 255).astype(np.int32)

        for y in range(height):
            py = offset_y + y * char_h + char_h - 3
            for x in range(width):
                is_chroma = resized_mask[y, x] > 127
                if render_mode == RENDER_MODE_USER and is_chroma:
                    continue
                elif render_mode == RENDER_MODE_BACKGROUND and not is_chroma:
                    continue

                mag = magnitude_norm[y, x]
                ang = angle[y, x]

                if use_edge_chars and mag > sobel_threshold:
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

    def _display_preview_image(self, bgr_image: np.ndarray):
        """Exibe imagem renderizada no preview_ascii_image widget."""
        if not hasattr(self, 'preview_ascii_image') or not self.preview_ascii_image:
            return False

        try:
            h, w = bgr_image.shape[:2]

            max_width = 500
            if w > max_width:
                scale = max_width / w
                new_w = max_width
                new_h = int(h * scale)
                bgr_image = cv2.resize(bgr_image, (new_w, new_h))
                h, w = new_h, new_w

            rgb = bgr_image[:, :, ::-1].copy()
            rgb = np.ascontiguousarray(rgb)

            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                GLib.Bytes.new(rgb.tobytes()),
                GdkPixbuf.Colorspace.RGB,
                False, 8, w, h, w * 3
            )

            self.preview_ascii_image.set_from_pixbuf(pixbuf)
            self.preview_ascii_image.set_visible(True)

            if hasattr(self, 'preview_aspect_frame') and self.preview_aspect_frame:
                self.preview_aspect_frame.set_property("ratio", w / h)

        except Exception as e:
            self.logger.error(f"Erro ao exibir preview: {e}")

        return False

    def _set_preview_placeholder(self, text: str):
        """Mostra texto placeholder no preview."""
        if hasattr(self, 'preview_ascii_image') and self.preview_ascii_image:
            self.preview_ascii_image.clear()
        return False

    def _start_config_watcher(self):
        """Inicia watcher que detecta mudancas no config.ini e atualiza preview."""
        self._preview_config_mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
        GLib.timeout_add(2000, self._check_config_and_refresh)

    def _check_config_and_refresh(self) -> bool:
        """Verifica se config.ini mudou e atualiza preview se necessario."""
        try:
            if not self._preview_visible:
                return True

            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._preview_config_mtime:
                self._preview_config_mtime = current_mtime
                self.reload_config()
                self._refresh_preview()
                self.logger.info("Config mudou, preview atualizado")
        except Exception:
            pass

        return True
```

---

### 3.3 Adicionar Widgets de Preview na UI: Modificar `src/gui/main.glade`

Inserir um novo botao "Preview" ao lado dos botoes de selecao e um GtkExpander com area de preview ABAIXO da secao "Selecionar".

**Onde inserir no Glade:** Dentro do Frame "Selecionar" (linhas 217-330), adicionar um 4o botao na box horizontal de botoes (linha 237) e um Expander abaixo (posicao 2 da box vertical).

**Modificacoes no Glade:**

#### 3.3.1 Adicionar Botao "Preview" (4o botao na mesma linha)

Dentro da `<object class="GtkBox">` horizontal de botoes (Glade linha 234-286), ANTES do tag `</object>` da box (linha 286), adicionar:

```xml
                    <child>
                      <object class="GtkButton" id="preview_button">
                        <property name="label" translatable="yes">Preview</property>
                        <property name="visible">True</property>
                        <property name="can-focus">True</property>
                        <property name="receives-default">True</property>
                        <property name="tooltip-text" translatable="yes">Mostrar/ocultar preview ASCII do video selecionado</property>
                        <property name="hexpand">True</property>
                        <signal name="clicked" handler="on_preview_button_clicked" swapped="no"/>
                      </object>
                      <packing>
                        <property name="expand">True</property>
                        <property name="fill">True</property>
                        <property name="position">3</property>
                      </packing>
                    </child>
```

#### 3.3.2 Adicionar Expander com Preview

APOS o `selected_path_label` (que esta na posicao 1 da box vertical, Glade linhas 293-311), adicionar um Expander na posicao 2:

```xml
                <child>
                  <object class="GtkExpander" id="preview_expander">
                    <property name="visible">True</property>
                    <property name="can-focus">True</property>
                    <property name="expanded">False</property>
                    <child>
                      <object class="GtkBox" id="preview_content_box">
                        <property name="visible">True</property>
                        <property name="can-focus">False</property>
                        <property name="orientation">vertical</property>
                        <property name="spacing">4</property>
                        <child>
                          <object class="GtkAspectFrame" id="preview_aspect_frame">
                            <property name="visible">True</property>
                            <property name="can-focus">False</property>
                            <property name="xalign">0.5</property>
                            <property name="yalign">0.5</property>
                            <property name="ratio">1.333</property>
                            <property name="obey-child">False</property>
                            <child>
                              <object class="GtkImage" id="preview_ascii_image">
                                <property name="visible">True</property>
                                <property name="can-focus">False</property>
                                <property name="halign">center</property>
                                <property name="valign">center</property>
                              </object>
                            </child>
                          </object>
                          <packing>
                            <property name="expand">True</property>
                            <property name="fill">True</property>
                            <property name="position">0</property>
                          </packing>
                        </child>
                      </object>
                    </child>
                    <child type="label">
                      <object class="GtkLabel">
                        <property name="visible">True</property>
                        <property name="can-focus">False</property>
                        <property name="label" translatable="yes"> Preview </property>
                        <attributes>
                          <attribute name="weight" value="bold"/>
                        </attributes>
                      </object>
                    </child>
                  </object>
                  <packing>
                    <property name="expand">True</property>
                    <property name="fill">True</property>
                    <property name="position">2</property>
                  </packing>
                </child>
```

---

### 3.4 Integrar Mixin na App Principal: Modificar `src/app/app.py`

#### 3.4.1 Adicionar import

No topo do arquivo (depois dos imports existentes, linha 14):
```python
from .actions.preview_actions import PreviewActionsMixin
```

#### 3.4.2 Adicionar Mixin a classe App

Modificar a heranca da classe App (linha 17-23):
```python
class App(
    FileActionsMixin,
    ConversionActionsMixin,
    PlaybackActionsMixin,
    CalibrationActionsMixin,
    OptionsActionsMixin,
    PreviewActionsMixin        # NOVO
):
```

#### 3.4.3 Inicializar preview apos widgets

Na funcao `__init__` (apos `_get_widgets()` retornar True, aproximadamente linha 120), adicionar:
```python
        self._init_preview()
        self._start_config_watcher()
```

#### 3.4.4 Adicionar widgets ao _get_widgets()

Na funcao `_get_widgets()` (app.py:309), adicionar apos os widgets existentes:
```python
            self.preview_button = self.builder.get_object("preview_button")
            self.preview_expander = self.builder.get_object("preview_expander")
            self.preview_ascii_image = self.builder.get_object("preview_ascii_image")
            self.preview_aspect_frame = self.builder.get_object("preview_aspect_frame")
```

NAO adicionar esses widgets na lista `required_widgets` (sao opcionais para compatibilidade).

---

### 3.5 Atualizar Preview ao Selecionar Arquivo: Modificar `src/app/actions/file_actions.py`

Quando o usuario seleciona um arquivo via Arquivo ou Pasta, chamar `_refresh_preview()`.

Localizar o handler `on_select_file_button_clicked()` e ao final, apos setar `self.selected_file_path`, adicionar:
```python
        if hasattr(self, '_refresh_preview'):
            self._refresh_preview()
```

Fazer o mesmo em `on_select_folder_button_clicked()`.

---

### 3.6 Atualizar Preview apos Calibrador Fechar

No `_launch_gtk_calibrator()` de `calibration_actions.py` (linha 62-73), apos `self.reload_config()` (linha 69), adicionar:
```python
            if hasattr(self, '_refresh_preview'):
                self._refresh_preview()
```

---

### 3.7 Atualizar Preview ao Salvar Opcoes

No dialog de opcoes (options_actions.py), quando o usuario salva parametros, tambem chamar `_refresh_preview()`. Localizar a funcao de salvamento de opcoes e adicionar ao final:
```python
        if hasattr(self, '_refresh_preview'):
            self._refresh_preview()
```

---

### 3.8 CSS para Botao Preview

No CSS da app principal (`app.py:_apply_custom_css` ou no `_apply_theme` dark), adicionar regra para o botao Preview ter estilo diferenciado (borda verde como os outros):

```css
#preview_button {
    border: 2px solid #418a69;
    border-radius: 4px;
    color: #ffffff;
    background-image: none;
    background-color: alpha(#418a69, 0.05);
    box-shadow: none;
}
#preview_button:hover {
    background-color: alpha(#418a69, 0.2);
}
```

Adicionar `#preview_button` na mesma regra CSS dos botoes de selecao existentes (app.py:239-251).

---

## 4. ARQUIVOS A MODIFICAR

| Arquivo | Acao | O Que Fazer |
|---------|------|-------------|
| `src/app/actions/preview_actions.py` | CRIAR | Novo mixin PreviewActionsMixin com todo o pipeline de preview |
| `src/gui/main.glade` | MODIFICAR | Adicionar botao Preview (posicao 3 na box de botoes) + GtkExpander com AspectFrame e Image |
| `src/app/app.py` | MODIFICAR | Importar PreviewActionsMixin, adicionar heranca, init preview, get widgets |
| `src/app/actions/file_actions.py` | MODIFICAR | Chamar _refresh_preview() apos selecionar arquivo |
| `src/app/actions/calibration_actions.py` | MODIFICAR | Chamar _refresh_preview() apos calibrador fechar |
| `src/app/actions/options_actions.py` | MODIFICAR | Chamar _refresh_preview() apos salvar opcoes |

---

## 5. FLUXO DE BIDIRECIONALIDADE

```
[App Principal]                    [Calibrador]
      |                                  |
  Selecionar video --> Preview gera      |
      |                                  |
  Abrir calibrador ---------------> Calibrador abre
      |                            Ajustar parametros
      |                            Clicar "Salvar"
      |                                  |
      |                            Salva config.ini
      |                            Fecha calibrador
      |                                  |
  subprocess.run() retorna <-------------+
  reload_config()
  _refresh_preview() --> Preview atualiza com novos params
      |
  [Config Watcher]
  A cada 2s verifica mtime do config.ini
  Se mudou: reload + refresh preview
```

### Fluxo alternativo (Opcoes da app):
```
[App Principal]
      |
  Abrir dialog Opcoes
  Alterar parametros (width, sobel, rampa, etc)
  Clicar "Salvar e Fechar"
      |
  save_config() -> config.ini
  _refresh_preview() -> Preview atualiza
```

---

## 6. CRITERIOS DE ACEITACAO

- [ ] Botao "Preview" aparece ao lado de "ASCII (.txt)" na area de selecao
- [ ] Clicar "Preview" expande/colapsa o painel de preview
- [ ] Ao selecionar um video, o preview mostra o primeiro frame convertido para ASCII
- [ ] Visual do preview eh IDENTICO ao painel RESULTADO do calibrador (mesmo renderer)
- [ ] Ao fechar o calibrador (apos salvar), o preview atualiza automaticamente
- [ ] Ao salvar opcoes no dialog, o preview atualiza automaticamente
- [ ] Config watcher detecta mudancas externas no config.ini a cada 2 segundos
- [ ] Preview roda em background thread (nao trava a UI)
- [ ] Sem preview visivel se nenhum video esta selecionado (mostra placeholder)
- [ ] Preview de imagens tambem funciona (jpg, png)
- [ ] Expander colapsa corretamente e a janela redimensiona para liberar espaco

---

## 7. RISCOS E MITIGACOES

| Risco | Mitigacao |
|-------|-----------|
| Renderizar ASCII como imagem eh lento para resolucoes altas | Canvas fixo de 640x480 para preview (proporcional). Thread em background |
| Config watcher pode causar overhead | Intervalo de 2 segundos eh suficiente. So verifica mtime do arquivo |
| Preview pode travar se cv2.VideoCapture falhar | Toda a geracao eh em try/except com placeholder de erro |
| Expandir preview pode empurrar outros elementos | GtkExpander lida naturalmente com expansao. Janela redimensiona |
| Selecionar video muito grande pode demorar | So le o primeiro frame. cv2.VideoCapture eh rapido para isso |

---

## 8. VERIFICACAO

```bash
# 1. Testar preview com video
python3 main.py
# -> Clicar "Arquivo" e selecionar um video
# -> Clicar "Preview" -> Verificar que expande e mostra ASCII do primeiro frame
# -> Clicar "Preview" de novo -> Verificar que colapsa

# 2. Testar bidirecionalidade com calibrador
python3 main.py
# -> Selecionar video
# -> Clicar "Preview" (expandir)
# -> Clicar "Calibrador"
# -> No calibrador, mudar Sobel threshold para 50
# -> Clicar "Salvar" no calibrador
# -> Verificar que o preview na app principal ATUALIZOU com o novo Sobel

# 3. Testar bidirecionalidade com opcoes
python3 main.py
# -> Selecionar video
# -> Clicar "Preview" (expandir)
# -> Abrir Opcoes (engrenagem)
# -> Mudar target_width para 120
# -> Salvar opcoes
# -> Verificar que o preview ATUALIZOU com a nova resolucao

# 4. Testar com imagem
python3 main.py
# -> Clicar "Arquivo" e selecionar um .jpg ou .png
# -> Clicar "Preview" -> Verificar que mostra ASCII da imagem

# 5. Testar config watcher externo
python3 main.py
# -> Selecionar video, expandir preview
# -> Em outro terminal: editar config.ini manualmente (mudar sobel_threshold)
# -> Aguardar 2-3 segundos
# -> Verificar que preview atualizou automaticamente
```
