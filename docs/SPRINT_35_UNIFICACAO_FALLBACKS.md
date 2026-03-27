# Sprint 35: Unificacao de Fallbacks e Constantes

**Prioridade:** ALTA
**Resolve:** BUG-05, BUG-06, BUG-07, BUG-08, BUG-09, BUG-16, BUG-20, BUG-21, BUG-22
**Dependencia:** Nenhuma

## Objetivo

Centralizar TODOS os valores padrao (fallbacks) em um unico arquivo `src/app/defaults.py`. Atualmente, 11+ arquivos definem fallbacks diferentes para os mesmos parametros, causando resultados divergentes entre calibrador, converters, player e GUI.

## Criar Arquivo

### 35.1 - Criar `src/app/defaults.py`

```python
# Valores padrao centralizados - UNICA fonte de verdade
# Espelha os valores do config.ini padrao na raiz do projeto
# Todos os modulos DEVEM importar daqui em vez de usar fallback inline

DEFAULTS = {
    'Conversor': {
        'target_width': 85,
        'target_height': 44,
        'char_aspect_ratio': 1.0,
        'sobel_threshold': 10,
        'sharpen_enabled': True,
        'sharpen_amount': 0.8,
        'luminance_preset': 'standard',
        'gpu_enabled': True,
        'gpu_render_mode': 'high_fidelity',
        'gpu_async_enabled': True,
        'gpu_async_num_streams': 4,
        'gpu_async_batch_size': 8,
        'braille_enabled': False,
        'braille_threshold': 128,
        'temporal_coherence_enabled': False,
        'temporal_threshold': 50,
        'auto_seg_enabled': False,
        'render_mode': 'both',
        'edge_boost_enabled': False,
        'edge_boost_amount': 100,
        'use_edge_chars': True,
    },
    'PostFX': {
        'bloom_enabled': False,
        'bloom_intensity': 1.2,
        'bloom_radius': 21,
        'bloom_threshold': 80,
        'chromatic_enabled': False,
        'chromatic_shift': 12,
        'scanlines_enabled': False,
        'scanlines_intensity': 0.7,
        'scanlines_spacing': 2,
        'glitch_enabled': False,
        'glitch_intensity': 0.6,
        'glitch_block_size': 8,
    },
    'MatrixRain': {
        'enabled': False,
        'mode': 'user',
        'char_set': 'katakana',
        'num_particles': 2500,
        'speed_multiplier': 1.5,
    },
    'ChromaKey': {
        'h_min': 0, 'h_max': 84,
        's_min': 154, 's_max': 255,
        'v_min': 0, 'v_max': 228,
        'erode': 1, 'dilate': 1,
    },
    'OpticalFlow': {
        'enabled': False,
        'target_fps': 30,
        'quality': 'medium',
    },
    'Audio': {
        'enabled': False,
        'sample_rate': 44100,
        'chunk_size': 2048,
        'bass_sensitivity': 1.0,
        'mids_sensitivity': 1.0,
        'treble_sensitivity': 1.0,
    },
}


def get_default(section: str, key: str):
    """Retorna o valor padrao para uma chave de config."""
    return DEFAULTS.get(section, {}).get(key)
```

## Arquivos a Modificar (11 arquivos)

### 35.2 - Substituir fallbacks hardcoded

Em CADA arquivo abaixo, adicionar o import e substituir os fallbacks divergentes.

**Import a adicionar em cada arquivo:**
```python
from src.app.defaults import get_default
```

**Substituicoes por arquivo:**

#### `src/core/gtk_calibrator.py`

| Linha | Antes | Depois |
|-------|-------|--------|
| 268 | `fallback=22` | `fallback=get_default('Conversor', 'target_height')` |
| 269 | `fallback=1.0` | `fallback=get_default('Conversor', 'char_aspect_ratio')` |
| 270 | `fallback=20` | `fallback=get_default('Conversor', 'sobel_threshold')` |
| 590 | `fallback='user'` | `fallback=get_default('Conversor', 'render_mode')` |
| 606 | `fallback=10` | `fallback=get_default('Conversor', 'temporal_threshold')` |

Tambem atualizar `DEFAULT_VALUES` (linha 82) para usar valores do config.ini:
```python
DEFAULT_VALUES = {
    'h_min': 0, 'h_max': 84,
    's_min': 154, 's_max': 255,
    'v_min': 0, 'v_max': 228,
    'erode': 1, 'dilate': 1,
}
```

#### `src/core/gpu_converter.py`
| Linha | Antes | Depois |
|-------|-------|--------|
| 579 | `fallback=20` | `fallback=get_default('Conversor', 'temporal_threshold')` |

#### `src/core/converter.py`
Fallbacks ja estao corretos (50 para temporal). Adicionar import por consistencia.

#### `src/core/mp4_converter.py`
Fallbacks ja corretos. Adicionar import.

#### `src/core/gif_converter.py`
Fallbacks ja corretos. Adicionar import.

#### `src/core/realtime_ascii.py`
| Linha | Antes | Depois |
|-------|-------|--------|
| 260 | `fallback=0.48` | `fallback=get_default('Conversor', 'char_aspect_ratio')` |
| 285 | `fallback=70` | `fallback=get_default('Conversor', 'sobel_threshold')` |

#### `src/core/gtk_fullscreen_player.py`
| Linha | Antes | Depois |
|-------|-------|--------|
| 83 | `fallback=44` | `fallback=get_default('Conversor', 'target_height')` |

#### `src/app/actions/options_actions.py`
| Linha | Antes | Depois |
|-------|-------|--------|
| 268 | `fallback=120` | `fallback=get_default('Conversor', 'target_width')` |
| 270 | `fallback=100` | `fallback=get_default('Conversor', 'sobel_threshold')` |
| 271 | `fallback=0.95` | `fallback=get_default('Conversor', 'char_aspect_ratio')` |
| 393 | `fallback=20` | `fallback=get_default('Conversor', 'temporal_threshold')` |

#### `src/app/actions/preview_actions.py`
Fallbacks ja corretos (10, 44). Adicionar import por consistencia.

### 35.3 - Corrigir PostFX defaults do calibrador (BUG-16)

**Arquivo:** `src/core/gtk_calibrator.py`, funcao `_init_postfx` (linhas ~2048-2061)

Substituir os fallbacks divergentes:
```python
# ANTES (defaults do calibrador):
bloom_intensity=0.6, bloom_radius=15, bloom_threshold=150
chromatic_shift=5, scanlines_intensity=0.5, scanlines_spacing=3
glitch_intensity=0.3, glitch_block_size=16

# DEPOIS (alinhado com config.ini):
bloom_intensity=self.config.getfloat('PostFX', 'bloom_intensity', fallback=get_default('PostFX', 'bloom_intensity')),
bloom_radius=self.config.getint('PostFX', 'bloom_radius', fallback=get_default('PostFX', 'bloom_radius')),
bloom_threshold=self.config.getint('PostFX', 'bloom_threshold', fallback=get_default('PostFX', 'bloom_threshold')),
chromatic_shift=self.config.getint('PostFX', 'chromatic_shift', fallback=get_default('PostFX', 'chromatic_shift')),
scanlines_intensity=self.config.getfloat('PostFX', 'scanlines_intensity', fallback=get_default('PostFX', 'scanlines_intensity')),
scanlines_spacing=self.config.getint('PostFX', 'scanlines_spacing', fallback=get_default('PostFX', 'scanlines_spacing')),
glitch_intensity=self.config.getfloat('PostFX', 'glitch_intensity', fallback=get_default('PostFX', 'glitch_intensity')),
glitch_block_size=self.config.getint('PostFX', 'glitch_block_size', fallback=get_default('PostFX', 'glitch_block_size')),
```

### 35.4 - Corrigir "Restaurar Padroes" (BUG-20)

**Arquivo:** `src/app/actions/options_actions.py`, funcao `on_options_restore_clicked` (linhas ~506-559)

```python
def on_options_restore_clicked(self, widget):
    self.opt_loop_check.set_active(False)
    self.opt_width_spin.set_value(85)       # era 120
    self.opt_height_spin.set_value(44)      # era 0
    self.opt_sobel_spin.set_value(10)       # era 100
    self.opt_aspect_spin.set_value(1.0)     # era 0.95
    self.opt_luminance_entry.set_text(DEFAULT_LUMINANCE_RAMP)
    self.opt_h_min_spin.set_value(0)        # era 35
    self.opt_h_max_spin.set_value(84)       # era 85
    self.opt_s_min_spin.set_value(154)      # era 40
    self.opt_s_max_spin.set_value(255)
    self.opt_v_min_spin.set_value(0)        # era 40
    self.opt_v_max_spin.set_value(228)      # era 255
    self.opt_erode_spin.set_value(1)        # era 2
    self.opt_dilate_spin.set_value(1)       # era 2

    # ... manter o resto dos widgets ...

    if hasattr(self, 'pref_gpu_switch') and self.pref_gpu_switch:
        self.pref_gpu_switch.set_active(True)  # era False
```

## Verificacao

1. `python cli.py validate` - todos os checks devem passar
2. Deletar `~/.config/extase-em-4r73/config.ini`
3. Abrir calibrador - todos os valores devem ser os defaults corretos do config.ini
4. Abrir GUI principal, abrir Opcoes - valores devem ser os mesmos
5. Clicar "Restaurar Padroes" na GUI - valores devem corresponder ao config.ini padrao
6. Converter video: `python cli.py convert --video data_input/Luna_flertando.mp4 --format mp4 --no-gpu`
7. O resultado deve corresponder ao que se ve no calibrador
