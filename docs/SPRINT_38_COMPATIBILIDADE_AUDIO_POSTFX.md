# Sprint 38: Compatibilidade de Features e Audio+PostFX

**Prioridade:** MEDIA
**Resolve:** BUG-15, BUG-17
**Dependencia:** Sprint 35

## Objetivo

Corrigir o conflito entre Audio Reactive e PostFX (Audio sobrescreve estado manual) e adicionar validacao basica de features incompativeis (Braille+PixelArt).

## Arquivo a Modificar

- `src/core/gtk_calibrator.py`

## Tarefas

### 38.1 - Corrigir Audio Reactive + PostFX (BUG-15)

**Funcao:** `on_audio_settings_changed` (linhas ~2321-2330)

O problema: ao ativar Audio Reactive, o codigo SOBRESCREVE os estados de Bloom, Chromatic e Glitch, ignorando as escolhas manuais do usuario.

```python
# ANTES (linhas 2321-2330):
        if audio_enabled and not self.audio_enabled:
            self._start_audio_analyzer()
            if POSTFX_AVAILABLE:
                if self.postfx_processor is None:
                    self.postfx_config = PostFXConfig()
                    self.postfx_processor = PostFXProcessor(self.postfx_config)
                self.postfx_config.bloom_enabled = self.audio_modulate_bloom
                self.postfx_config.chromatic_enabled = self.audio_modulate_chromatic
                self.postfx_config.glitch_enabled = self.audio_modulate_glitch
                self.postfx_enabled = True

# DEPOIS:
        if audio_enabled and not self.audio_enabled:
            self._start_audio_analyzer()
            if POSTFX_AVAILABLE:
                if self.postfx_processor is None:
                    if self.postfx_config is None:
                        self.postfx_config = PostFXConfig()
                    self.postfx_processor = PostFXProcessor(self.postfx_config)
                self.postfx_enabled = True
```

### 38.2 - Validacao Braille + PixelArt

**Funcao:** `on_mode_toggled` (linha ~1759)

Adicionar ao final da funcao, ANTES de `self._update_mode_visibility()`:
```python
    # Braille e PixelArt sao mutuamente exclusivos
    if self.conversion_mode == MODE_PIXELART and self.braille_enabled:
        self.braille_enabled = False
        self._block_signals = True
        if self.chk_braille:
            self.chk_braille.set_active(False)
        self._block_signals = False
        self._set_status("Braille desativado: incompativel com PixelArt")
```

**Funcao:** `on_gpu_settings_changed` (linha ~1788)

Adicionar ao final da funcao, ANTES de `self._force_rerender()`:
```python
    # Braille e PixelArt sao mutuamente exclusivos
    if self.braille_enabled and self.conversion_mode == MODE_PIXELART:
        self.conversion_mode = MODE_ASCII
        self._block_signals = True
        if self.radio_ascii:
            self.radio_ascii.set_active(True)
        self._block_signals = False
        self._update_mode_visibility()
        self._set_status("Modo ASCII ativado: Braille requer ASCII")
```

### 38.3 - Aviso Matrix Rain + PixelArt

**Funcao:** `on_matrix_settings_changed` (linha ~1872)

Adicionar ao final, apos o bloco de status:
```python
    if self.matrix_enabled and self.conversion_mode == MODE_PIXELART:
        self._set_status("Aviso: Matrix Rain com PixelArt gera visual misto")
```

## Verificacao

1. Abrir calibrador
2. **Teste Audio+PostFX:** Ativar Scanlines e desativar Bloom. Ativar Audio Reactive. Verificar que Scanlines continua ON e Bloom continua OFF (antes, Bloom era forcado ON).
3. **Teste Braille+PixelArt:** Selecionar PixelArt. Tentar ativar Braille. Verificar que Braille eh desativado automaticamente com mensagem de status.
4. **Teste Braille em ASCII:** Selecionar ASCII. Ativar Braille. Funciona normalmente.
5. **Teste Matrix+PixelArt:** Ativar Matrix Rain. Selecionar PixelArt. Verificar aviso no status.
