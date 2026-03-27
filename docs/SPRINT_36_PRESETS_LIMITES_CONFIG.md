# Sprint 36: Calibrador - Presets, Limites e Config

**Prioridade:** ALTA
**Resolve:** BUG-03, BUG-04, BUG-11
**Dependencia:** Sprint 35

## Objetivo

Corrigir 3 problemas no calibrador: presets duplicados sem aspect ratio, limite de largura que impede presets altos, e pipe trailing na luminance_ramp.

## Arquivos a Modificar

- `src/core/gtk_calibrator.py`
- `src/gui/calibrator.glade`

## Tarefas

### 36.1 - Remover QUALITY_PRESETS duplicado

**Arquivo:** `src/core/gtk_calibrator.py`
**Linhas:** 84-90

REMOVER estas linhas:
```python
QUALITY_PRESETS = {
    'mobile': {'width': 100, 'height': 25},
    'low': {'width': 120, 'height': 30},
    'medium': {'width': 180, 'height': 45},
    'high': {'width': 240, 'height': 60},
    'veryhigh': {'width': 300, 'height': 75},
}
```

Verificar que o import ja existe (linha 29). Se `QUALITY_PRESETS` nao estiver no import, adicionar:
```python
from src.app.constants import LUMINANCE_RAMPS, FIXED_PALETTES, QUALITY_PRESETS
```

### 36.2 - Atualizar on_resolution_changed para setar aspect_ratio

**Arquivo:** `src/core/gtk_calibrator.py`
**Funcao:** `on_resolution_changed` (linha ~2383)

Adicionar a linha `self.converter_config['char_aspect_ratio'] = preset['aspect']`:
```python
def on_resolution_changed(self, widget):
    if self._block_signals:
        return
    active = widget.get_active()
    preset_names = ['mobile', 'low', 'medium', 'high', 'veryhigh']
    if 0 <= active < len(preset_names):
        preset = QUALITY_PRESETS[preset_names[active]]
        self.spin_width.set_value(preset['width'])
        self.spin_height.set_value(preset['height'])
        self.converter_config['target_width'] = preset['width']
        self.converter_config['target_height'] = preset['height']
        self.converter_config['char_aspect_ratio'] = preset['aspect']  # NOVO
        self._update_target_dimensions()
        self._set_status(f"Resolucao: {preset_names[active].title()}")
```

### 36.3 - Glade: Aumentar limite de largura para 300

**Arquivo:** `src/gui/calibrator.glade`
**Linha:** 39

```xml
<!-- ANTES -->
<property name="lower">40</property><property name="upper">150</property><property name="value">85</property>

<!-- DEPOIS -->
<property name="lower">40</property><property name="upper">300</property><property name="value">85</property>
```

### 36.4 - Python: Aumentar limite de largura para 300

**Arquivo:** `src/core/gtk_calibrator.py`
**Funcao:** `on_ascii_config_changed` (linhas ~1682-1686)

```python
# ANTES:
elif w > 150:
    w = 150
    self._block_signals = True
    self.spin_width.set_value(150)
    self._block_signals = False

# DEPOIS:
elif w > 300:
    w = 300
    self._block_signals = True
    self.spin_width.set_value(300)
    self._block_signals = False
```

### 36.5 - Remover pipe trailing na luminance_ramp

**Arquivo:** `src/core/gtk_calibrator.py`
**Funcao:** `on_save_config_clicked` (linha ~2465)

```python
# ANTES:
self.config.set('Conversor', 'luminance_ramp', luminance_ramp + '|')

# DEPOIS:
self.config.set('Conversor', 'luminance_ramp', luminance_ramp)
```

## Verificacao

1. Abrir calibrador
2. Selecionar preset "High" (240x60) - campo Larg deve mostrar 240 (nao 150)
3. Selecionar preset "VeryHigh" (300x75) - campo Larg deve mostrar 300
4. Salvar e abrir config.ini - verificar que `char_aspect_ratio` foi salvo corretamente
5. Verificar que `luminance_ramp` no config.ini NAO termina com `|`
