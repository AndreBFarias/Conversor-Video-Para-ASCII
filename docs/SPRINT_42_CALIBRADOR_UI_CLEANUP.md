# Sprint 42: Calibrador - UI Cleanup e Reorganizacao

**Prioridade:** ALTA
**Resolve:** Janelas fora de ordem, UI morta (presets/acoes), controles agrupados incorretamente
**Dependencia:** Nenhuma

## Objetivo

Reorganizar a interface do calibrador com foco em UX: remover elementos mortos, reordenar janelas, e reagrupar controles por funcao ao inves de proximidade historica.

## Contexto

### Problemas de UX identificados

1. **ROW 1 (toolbar):** Presets Studio/Natural/Bright e Acoes Auto/Reset sao 100% inuteis quando Auto Seg esta ativo -- o HSV e ignorado. Sao UI morta.

2. **ROW 3 (displays):** Ordem errada (Original | Resultado | Mascara). O fluxo logico e: Origem -> Processamento -> Destino.

3. **ROW 4 (controles):** Agrupamento por proximidade historica, nao por funcao:
   - Edge Boost esta DENTRO da ilha HSV Chroma Key (nao tem relacao com chroma)
   - Edge Chars esta ISOLADO na ilha GPU (separado do Edge Boost sem motivo)
   - Braille e Temporal estao DENTRO do HSV (nao tem relacao com chroma)
   - HSV ocupa 60% do espaco com 8 sliders que ficam SEMPRE desabilitados com Auto Seg

### Layout atual

```
ROW 1: [Presets] [Acoes] [Rec] [FX] [Style] [OF] [Save]
ROW 2: [Modo] [Config ASCII] [Render] [Config PixelArt]
ROW 3: ORIGINAL | RESULTADO | MASCARA
ROW 4: [HSV: H/S/V Min-Max + Erode/Dilate + Braille + Temporal + Edge Boost] [GPU: AutoSeg + EdgeChars] [Matrix Rain] [Audio Reactive]
ROW 5: Status
```

### Layout proposto

```
ROW 1: [Rec] [FX] [Style] [OF] [Save]
ROW 2: [Modo] [Config ASCII] [Render] [Config PixelArt]
ROW 3: ORIGEM | PROCESSAMENTO | DESTINO
ROW 4: [Segmentacao: AutoSeg + HSV colapsavel] [Bordas: EdgeBoost + slider + EdgeChars] [Rendering: Braille + slider + Temporal + slider] [Matrix Rain] [Audio Reactive]
ROW 5: Status
```

## Tarefas

### 42.1 - Reordenar e renomear janelas no Glade

**Arquivo:** `src/gui/calibrator.glade`

No bloco `<!-- ROW 3: VIDEO DISPLAYS -->` (linha ~406), os 3 boxes de video estao nesta ordem:
1. `video_box_1` (ORIGINAL) -- LEFT
2. `video_box_3` (RESULTADO, contem `event_ascii`) -- CENTER
3. `video_box_2` (MASCARA) -- RIGHT

**Acao:** Trocar a POSICAO de `video_box_3` e `video_box_2` no XML:
1. `video_box_1` -- LEFT (mantem)
2. `video_box_2` -- CENTER (sobe de RIGHT para CENTER)
3. `video_box_3` -- RIGHT (desce de CENTER para RIGHT)

**Acao:** Renomear os labels:
- `ORIGINAL` -> `ORIGEM` (linha ~429)
- `MÁSCARA` -> `PROCESSAMENTO` (linha ~495)
- `RESULTADO` -> `DESTINO` (linha ~458)

**IMPORTANTE:** NAO alterar IDs dos widgets (`image_original`, `image_ascii`, `image_chroma`, etc.). Apenas trocar posicao dos blocos XML e textos dos labels.

### 42.2 - Remover ilha de Presets e Acoes do Glade

**Arquivo:** `src/gui/calibrator.glade`

Remover 2 blocos completos da ROW 1:

1. Bloco `<!-- ILHA: Presets -->` (linhas ~151-163):
```xml
<child>
  <object class="GtkBox" id="island_presets">
    ...btn_preset_studio, btn_preset_natural, btn_preset_bright...
  </object>
</child>
```

2. Bloco `<!-- ILHA: Ações -->` (linhas ~165-176):
```xml
<child>
  <object class="GtkBox" id="island_actions">
    ...btn_auto_detect, btn_reset...
  </object>
</child>
```

### 42.3 - Reorganizar ROW 4: Segmentacao + Bordas + Rendering

**Arquivo:** `src/gui/calibrator.glade`

A ROW 4 atual (`row_hsv_gpu_matrix`, linha ~517) contem:
1. `island_hsv` -- HSV Chroma Key (8 sliders + Braille + Temporal + Edge Boost)
2. `island_gpu` -- GPU (Auto Seg + Edge Chars)
3. `island_matrix` -- Matrix Rain
4. `island_audio` -- Audio Reactive

Reorganizar para 5 ilhas por funcao:

#### 42.3.1 - Ilha Segmentacao (substitui ilha HSV + ilha GPU)

Nova ilha `island_segmentation` com:
- Titulo: "Segmentacao"
- Checkbox Auto Seg (movido da ilha GPU)
- GtkRevealer contendo os sliders HSV (visivel apenas quando Auto Seg esta DESATIVADO)
- Dentro do revealer: grid com H/S/V Min/Max + Erode/Dilate (mesmos widgets, apenas reposicionados)

```xml
<!-- ILHA: Segmentacao -->
<child>
  <object class="GtkBox" id="island_segmentation">
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <property name="hexpand">True</property>
    <style><class name="island-hsv"/></style>

    <!-- Header com Auto Seg -->
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="spacing">8</property>
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">Segmentacao</property>
            <property name="halign">start</property>
            <attributes><attribute name="weight" value="bold"/></attributes>
          </object>
        </child>
        <child>
          <object class="GtkCheckButton" id="chk_auto_seg">
            <property name="visible">True</property>
            <property name="label">Auto Seg</property>
            <property name="active">False</property>
            <signal name="toggled" handler="on_auto_seg_changed"/>
          </object>
        </child>
      </object>
      <packing><property name="expand">False</property></packing>
    </child>

    <!-- HSV Fallback (colapsavel) -->
    <child>
      <object class="GtkRevealer" id="revealer_hsv">
        <property name="visible">True</property>
        <property name="reveal-child">True</property>
        <property name="transition-type">slide-down</property>
        <property name="transition-duration">300</property>
        <child>
          <object class="GtkGrid">
            <property name="visible">True</property>
            <property name="row-spacing">1</property>
            <property name="column-spacing">3</property>
            <property name="margin-start">3</property>
            <property name="margin-end">3</property>
            <property name="margin-top">2</property>
            <property name="margin-bottom">2</property>

            <!-- Linha 0: H Min | S Min | V Min | Erode -->
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">H Min:</property><property name="xalign">1</property></object><packing><property name="left-attach">0</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkScale" id="scale_h_min"><property name="visible">True</property><property name="adjustment">adj_h_min</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">1</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">S Min:</property><property name="xalign">1</property></object><packing><property name="left-attach">2</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkScale" id="scale_s_min"><property name="visible">True</property><property name="adjustment">adj_s_min</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">3</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">V Min:</property><property name="xalign">1</property></object><packing><property name="left-attach">4</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkScale" id="scale_v_min"><property name="visible">True</property><property name="adjustment">adj_v_min</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">5</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">Erode:</property><property name="xalign">1</property></object><packing><property name="left-attach">6</property><property name="top-attach">0</property></packing></child>
            <child><object class="GtkScale" id="scale_erode"><property name="visible">True</property><property name="adjustment">adj_erode</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">7</property><property name="top-attach">0</property></packing></child>

            <!-- Linha 1: H Max | S Max | V Max | Dilate -->
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">H Max:</property><property name="xalign">1</property></object><packing><property name="left-attach">0</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkScale" id="scale_h_max"><property name="visible">True</property><property name="adjustment">adj_h_max</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">1</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">S Max:</property><property name="xalign">1</property></object><packing><property name="left-attach">2</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkScale" id="scale_s_max"><property name="visible">True</property><property name="adjustment">adj_s_max</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">3</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">V Max:</property><property name="xalign">1</property></object><packing><property name="left-attach">4</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkScale" id="scale_v_max"><property name="visible">True</property><property name="adjustment">adj_v_max</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">5</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkLabel"><property name="visible">True</property><property name="label">Dilate:</property><property name="xalign">1</property></object><packing><property name="left-attach">6</property><property name="top-attach">1</property></packing></child>
            <child><object class="GtkScale" id="scale_dilate"><property name="visible">True</property><property name="adjustment">adj_dilate</property><property name="digits">0</property><property name="value-pos">right</property><property name="hexpand">True</property><signal name="value-changed" handler="on_hsv_changed"/></object><packing><property name="left-attach">7</property><property name="top-attach">1</property></packing></child>
          </object>
        </child>
      </object>
      <packing><property name="expand">False</property></packing>
    </child>
  </object>
  <packing><property name="expand">True</property><property name="fill">True</property></packing>
</child>
```

#### 42.3.2 - Ilha Bordas (nova, agrupa Edge Boost + Edge Chars)

Nova ilha `island_edges` com:
- Titulo: "Bordas"
- Checkbox Edge Boost + slider de intensidade
- Checkbox Edge Chars

```xml
<!-- ILHA: Bordas -->
<child>
  <object class="GtkBox" id="island_edges">
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <property name="spacing">4</property>
    <property name="vexpand">False</property>
    <style><class name="island-hsv"/></style>
    <child>
      <object class="GtkLabel">
        <property name="visible">True</property>
        <property name="label">Bordas</property>
        <property name="halign">start</property>
        <attributes><attribute name="weight" value="bold"/></attributes>
      </object>
      <packing><property name="expand">False</property></packing>
    </child>
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="spacing">4</property>
        <child>
          <object class="GtkCheckButton" id="chk_edge_boost">
            <property name="visible">True</property>
            <property name="label">Boost</property>
            <property name="active">False</property>
            <signal name="toggled" handler="on_edge_boost_changed"/>
          </object>
        </child>
        <child>
          <object class="GtkScale" id="scale_edge_boost_amount">
            <property name="visible">True</property>
            <property name="adjustment">adj_edge_boost_amount</property>
            <property name="digits">0</property>
            <property name="value-pos">right</property>
            <property name="hexpand">True</property>
            <property name="width-request">100</property>
            <signal name="value-changed" handler="on_edge_boost_changed"/>
          </object>
        </child>
      </object>
    </child>
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="spacing">4</property>
        <child>
          <object class="GtkCheckButton" id="chk_use_edge_chars">
            <property name="visible">True</property>
            <property name="label">Contornos</property>
            <property name="active">True</property>
            <signal name="toggled" handler="on_edge_boost_changed"/>
          </object>
        </child>
      </object>
    </child>
  </object>
  <packing><property name="expand">False</property><property name="fill">True</property></packing>
</child>
```

#### 42.3.3 - Ilha Rendering (nova, agrupa Braille + Temporal)

Nova ilha `island_rendering` com:
- Titulo: "Rendering"
- Checkbox Braille + slider threshold
- Checkbox Temporal + slider threshold

```xml
<!-- ILHA: Rendering -->
<child>
  <object class="GtkBox" id="island_rendering">
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <property name="spacing">4</property>
    <property name="vexpand">False</property>
    <style><class name="island-hsv"/></style>
    <child>
      <object class="GtkLabel">
        <property name="visible">True</property>
        <property name="label">Rendering</property>
        <property name="halign">start</property>
        <attributes><attribute name="weight" value="bold"/></attributes>
      </object>
      <packing><property name="expand">False</property></packing>
    </child>
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="spacing">4</property>
        <child>
          <object class="GtkCheckButton" id="chk_braille">
            <property name="visible">True</property>
            <property name="label">Braille</property>
            <property name="active">False</property>
            <signal name="toggled" handler="on_gpu_settings_changed"/>
          </object>
        </child>
        <child>
          <object class="GtkScale" id="scale_braille_threshold">
            <property name="visible">True</property>
            <property name="adjustment">adj_braille_threshold</property>
            <property name="digits">0</property>
            <property name="value-pos">right</property>
            <property name="hexpand">True</property>
            <property name="width-request">80</property>
            <signal name="value-changed" handler="on_gpu_settings_changed"/>
          </object>
        </child>
      </object>
    </child>
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="spacing">4</property>
        <child>
          <object class="GtkCheckButton" id="chk_temporal">
            <property name="visible">True</property>
            <property name="label">Temporal</property>
            <property name="active">False</property>
            <signal name="toggled" handler="on_gpu_settings_changed"/>
          </object>
        </child>
        <child>
          <object class="GtkScale" id="scale_temporal_threshold">
            <property name="visible">True</property>
            <property name="adjustment">adj_temporal_threshold</property>
            <property name="digits">0</property>
            <property name="value-pos">right</property>
            <property name="hexpand">True</property>
            <property name="width-request">80</property>
            <signal name="value-changed" handler="on_gpu_settings_changed"/>
          </object>
        </child>
      </object>
    </child>
  </object>
  <packing><property name="expand">False</property><property name="fill">True</property></packing>
</child>
```

#### 42.3.4 - Remover ilha GPU antiga

A ilha `island_gpu` (linhas ~575-603) deve ser REMOVIDA. Seus widgets foram redistribuidos:
- `chk_auto_seg` -> ilha Segmentacao
- `chk_use_edge_chars` -> ilha Bordas

#### 42.3.5 - Matrix Rain e Audio Reactive

As ilhas `island_matrix` e `island_audio` PERMANECEM iguais. Nenhuma mudanca.

### 42.4 - Atualizar Python: Revealer HSV

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `_init_ui` (linha ~410), adicionar referencia ao revealer:
```python
self.revealer_hsv = self.builder.get_object("revealer_hsv")
```

No metodo `on_auto_seg_changed` (linha ~1768), substituir a logica de desabilitar sliders pela logica de colapsar o revealer:

```python
# DE (linhas 1798-1803):
hsv_sensitive = not self.auto_seg_enabled
for scale_name in ['scale_h_min', 'scale_h_max', 'scale_s_min', 'scale_s_max',
                   'scale_v_min', 'scale_v_max', 'scale_erode', 'scale_dilate']:
    scale = getattr(self, scale_name, None)
    if scale:
        scale.set_sensitive(hsv_sensitive)

# PARA:
if self.revealer_hsv:
    self.revealer_hsv.set_reveal_child(not self.auto_seg_enabled)
```

Isso faz o painel HSV COLAPSAR com animacao quando Auto Seg e ativado, ao inves de apenas ficar cinza.

### 42.5 - Remover handlers Python dos presets e acoes

**Arquivo:** `src/core/gtk_calibrator.py`

Remover os seguintes metodos da classe `GTKCalibrator`:
1. `on_preset_studio_clicked` (linha ~2368)
2. `on_preset_natural_clicked` (linha ~2372)
3. `on_preset_bright_clicked` (linha ~2376)
4. `on_auto_detect_clicked` (linha ~2380)
5. `on_reset_clicked` (linha ~2385)
6. `_auto_detect_green` (linhas ~738-770)

Remover o dicionario `CHROMA_PRESETS` (linhas ~77-81).

### 42.6 - Remover atalhos de teclado

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `on_key_press`, remover os cases das teclas R (Reset) e A (Auto detect).

**Arquivo:** `src/gui/calibrator.glade`

Na ROW 5, atualizar o label de status (linha ~716):
```
De: "Atalhos: [A] Auto | [R] Reset | [S] Salvar | [T] Terminal | [Q] Sair"
Para: "Atalhos: [S] Salvar | [T] Terminal | [Q] Sair"
```

### 42.7 - Limpar CSS

**Arquivo:** `src/core/gtk_calibrator.py`

No metodo `_load_css` (linha ~179), remover:
- `.island-presets`
- `.island-actions`

### 42.8 - Limpar DEFAULT_VALUES

**Arquivo:** `src/core/gtk_calibrator.py`

O dicionario `DEFAULT_VALUES` (linha ~83) era usado por `on_reset_clicked`. Verificar se `_load_initial_values` usa como fallback. Se sim, MANTER. Se nao, REMOVER.

## Diagrama da Reorganizacao da ROW 4

```
ANTES:
+-----------------------------------------------------------------------+
| HSV Chroma Key                              | GPU      |Matrix| Audio |
| H Min [====] S Min [====] V Min [====] Erode [==]  | AutoSeg  |      |      |
| H Max [====] S Max [====] V Max [====] Dilate [==] | EdgeChars|      |      |
| [x]Braille [====] [x]Temporal [====] [x]EdgeBoost [====]  |          |      |      |
+-----------------------------------------------------------------------+
  ^^^^^^ misturado sem relacao ^^^^^^      ^^^separado^^^

DEPOIS:
+-----------------------------------------------------------------------+
| Segmentacao       | Bordas      | Rendering       | Matrix | Audio    |
| [x] Auto Seg      | [x]Boost [==]| [x]Braille [==] |        |          |
| v HSV Fallback v   | [x]Contornos | [x]Temporal [==]|        |          |
| (colapsavel)       |             |                 |        |          |
+-----------------------------------------------------------------------+
  ^^^agrupado por funcao^^^
```

## Verificacao

1. Abrir o calibrador:
   ```bash
   python src/core/gtk_calibrator.py --config config.ini --video data_input/Luna_flertando.mp4
   ```
2. **ROW 1:** Presets e Acoes NAO aparecem. Rec, FX, Style, OF, Save estao presentes
3. **ROW 3:** Janelas na ordem Origem | Processamento | Destino
4. **ROW 4:** 5 ilhas visiveis: Segmentacao | Bordas | Rendering | Matrix | Audio
5. **Auto Seg ON:** HSV sliders colapsam com animacao suave
6. **Auto Seg OFF:** HSV sliders aparecem no revealer
7. **Edge Boost + Edge Chars:** Juntos na ilha Bordas
8. **Braille + Temporal:** Juntos na ilha Rendering
9. **Atalhos [S], [T], [Q]** funcionam
10. **Nenhum erro** no terminal
