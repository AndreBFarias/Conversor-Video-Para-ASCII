# Sprint 41: Verificacao de Conflitos de Features Ativas Simultaneamente

**Prioridade:** ALTA
**Resolve:** Conflitos entre 11 features independentes
**Dependencia:** Sprint 35, Sprint 38

## Objetivo

Criar uma camada de validacao que impeca/avise sobre combinacoes de features que geram resultados incorretos, degradacao de performance, ou comportamento inesperado quando ativas ao mesmo tempo.

## Contexto

O projeto tem 11 features independentes que podem ser combinadas livremente:

| # | Feature | Checkbox/Widget | Chave config |
|---|---------|----------------|--------------|
| 1 | Modo ASCII | radio_ascii | Mode.conversion_mode=ascii |
| 2 | Modo PixelArt | radio_pixelart | Mode.conversion_mode=pixelart |
| 3 | Braille | chk_braille | Conversor.braille_enabled |
| 4 | Temporal Coherence | chk_temporal | Conversor.temporal_coherence_enabled |
| 5 | Auto Segmentation | chk_auto_seg | Conversor.auto_seg_enabled |
| 6 | Edge Boost | chk_edge_boost | Conversor.edge_boost_enabled |
| 7 | Matrix Rain | chk_matrix | MatrixRain.enabled |
| 8 | PostFX (4 efeitos) | chk_bloom/chrom/scan/glitch | PostFX.* |
| 9 | Style Transfer | chk_style | Style.style_enabled |
| 10 | Optical Flow | chk_optical_flow | OpticalFlow.enabled |
| 11 | Audio Reactive | chk_audio | Audio.enabled |

## Matriz Completa de Conflitos

| Combinacao | Tipo | Problema | Acao |
|-----------|------|---------|------|
| Braille + PixelArt | BLOQUEIO | Mutuamente exclusivos por conceito | Desativar um ao ativar outro |
| Braille + CPU converter | AVISO | CPU ignora braille silenciosamente | Dialogo pre-conversao |
| Braille + Edge Boost | SEM EFEITO | Edge Boost nao afeta braille (threshold binario) | Aviso no status |
| Braille + Style Transfer | SEM EFEITO | Style altera cores, braille ignora cores | Aviso no status |
| Matrix Rain + PixelArt | VISUAL | ASCII sobre pixel art, visual misto | Aviso no status |
| Matrix Rain + Braille | VISUAL | Dois sistemas de caracteres sobrepostos | Aviso no status |
| Audio Reactive + PostFX OFF | LOGICA | Audio precisa de PostFX para modular | Aviso, nao forcar |
| Audio Reactive + Scanlines | INFO | Scanlines nao eh modulado pelo audio | Info no status |
| Temporal + resolucao >200 | PERFORMANCE | 22500+ comparacoes por frame | Aviso no status |
| Auto Seg + ChromaKey | LOGICA | HSV stale salvos como fallback | Documentar |
| Edge Boost + PixelArt | SEM EFEITO | Nao ha caracteres ASCII em PixelArt | Desabilitar widget |
| 4+ features GPU pesadas | PERFORMANCE | Memory pressure, possivel OOM | Aviso no status |

## Arquivos a Modificar

1. `src/core/gtk_calibrator.py` - Validacao em tempo real
2. `src/app/actions/conversion_actions.py` - Verificacao pre-conversao

## Tarefas

### 41.1 - Criar funcao _validate_features no calibrador

**Arquivo:** `src/core/gtk_calibrator.py`

Adicionar este metodo na classe GTKCalibrator (apos `_update_mode_visibility`):

```python
def _validate_features(self):
    """Valida combinacoes de features e mostra avisos/bloqueios."""
    warnings = []

    # BLOQUEIOS (mutuamente exclusivos)
    if self.braille_enabled and self.conversion_mode == MODE_PIXELART:
        self.braille_enabled = False
        self._block_signals = True
        if self.chk_braille:
            self.chk_braille.set_active(False)
        self._block_signals = False
        warnings.append("Braille desativado: incompativel com PixelArt")

    # AVISOS VISUAIS
    if self.matrix_enabled and self.conversion_mode == MODE_PIXELART:
        warnings.append("Matrix Rain + PixelArt: visual misto")

    if self.matrix_enabled and self.braille_enabled:
        warnings.append("Matrix Rain + Braille: sobreposicao de caracteres")

    if self.braille_enabled and self.edge_boost_enabled:
        warnings.append("Edge Boost sem efeito no modo Braille")

    if self.braille_enabled and self.style_enabled:
        warnings.append("Style Transfer sem efeito visual no Braille")

    # AUDIO + POSTFX
    if self.audio_enabled and not self.postfx_enabled:
        warnings.append("Audio Reactive requer PostFX ativo")

    # PERFORMANCE
    w, h = self.target_dimensions
    if self.temporal_enabled and w > 200:
        warnings.append("Temporal + alta resolucao: possivel queda de FPS")

    heavy_count = sum([
        self.auto_seg_enabled,
        self.optical_flow_enabled,
        self.style_enabled and self.style_preset != 'none',
        self.postfx_enabled,
        self.matrix_enabled
    ])
    if heavy_count >= 4:
        warnings.append(f"{heavy_count} features pesadas ativas: possivel lentidao")

    # DESABILITAR WIDGETS IRRELEVANTES
    if self.chk_edge_boost:
        self.chk_edge_boost.set_sensitive(self.conversion_mode == MODE_ASCII)
    if self.scale_edge_boost_amount:
        self.scale_edge_boost_amount.set_sensitive(
            self.edge_boost_enabled and self.conversion_mode == MODE_ASCII
        )
    if self.chk_use_edge_chars:
        self.chk_use_edge_chars.set_sensitive(self.conversion_mode == MODE_ASCII)

    if warnings:
        self._set_status(" | ".join(warnings[:2]))

    return warnings
```

### 41.2 - Chamar _validate_features nos handlers

Adicionar `self._validate_features()` ao FINAL dos seguintes metodos (ANTES de `self._force_rerender()` quando existir):

- `on_mode_toggled()` (linha ~1759)
- `on_gpu_settings_changed()` (linha ~1788)
- `on_matrix_settings_changed()` (linha ~1872)
- `on_postfx_changed()` (linha ~2097)
- `on_audio_settings_changed()` (linha ~2305)
- `on_style_changed()` (linha ~2138)
- `on_edge_boost_changed()` (linha ~1855)
- `on_auto_seg_changed()` (linha ~1818)
- `on_resolution_changed()` (linha ~2383)

Exemplo para on_mode_toggled:
```python
def on_mode_toggled(self, widget):
    if self._block_signals:
        return
    if not widget.get_active():
        return
    if widget == self.radio_ascii:
        self.conversion_mode = MODE_ASCII
        self._set_status("Modo: ASCII")
    else:
        self.conversion_mode = MODE_PIXELART
        self._set_status("Modo: Pixel Art")
    self._update_mode_visibility()
    self._validate_features()  # NOVO
```

### 41.3 - Verificacao pre-conversao na GUI principal

**Arquivo:** `src/app/actions/conversion_actions.py`

Adicionar import no topo:
```python
from gi.repository import Gtk, GLib, GdkPixbuf
```

Adicionar metodo na classe ConversionActionsMixin:
```python
def _pre_conversion_check(self) -> bool:
    """Verifica conflitos antes de converter. Retorna True se ok."""
    braille = self.config.getboolean('Conversor', 'braille_enabled', fallback=False)
    gpu = self.config.getboolean('Conversor', 'gpu_enabled', fallback=True)

    if braille and not gpu:
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Braille requer GPU"
        )
        dialog.format_secondary_text(
            "O modo Braille so funciona com GPU ativada.\n"
            "Deseja ativar GPU para esta conversao?"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self.config.set('Conversor', 'gpu_enabled', 'true')
            return True
        return False

    return True
```

No metodo `on_convert_button_clicked` (linha ~24), adicionar verificacao ANTES de iniciar thread:
```python
def on_convert_button_clicked(self, widget):
    if self.selected_file_path:
        if not self._pre_conversion_check():
            return
        thread = threading.Thread(target=self.run_conversion, args=([self.selected_file_path],))
        thread.daemon = True
        thread.start()
```

Mesmo para `on_convert_all_button_clicked`.

## Verificacao via GUI

1. **Braille + PixelArt:** Abrir calibrador. Ativar PixelArt. Tentar ativar Braille -> desativado automaticamente.
2. **PixelArt + Edge Boost:** Selecionar PixelArt -> checkbox Edge Boost fica cinza (insensitivo).
3. **Matrix + PixelArt:** Ativar Matrix Rain com PixelArt ativo -> aviso no status.
4. **Audio sem PostFX:** Desativar todos PostFX. Ativar Audio Reactive -> aviso no status.
5. **Temporal + VeryHigh:** Ativar Temporal, selecionar resolucao VeryHigh -> aviso de performance.
6. **4+ features pesadas:** Ativar Auto Seg + PostFX + Matrix Rain + Optical Flow -> aviso de lentidao.
7. **Braille + CPU:** Na GUI principal, ativar Braille e desativar GPU nas opcoes. Tentar converter -> dialogo perguntando se quer ativar GPU.
