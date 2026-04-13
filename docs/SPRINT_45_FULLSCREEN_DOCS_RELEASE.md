# Sprint 45: Fullscreen Preview + Atualizacao de Docs + Release

**Prioridade:** ALTA
**Resolve:** Fullscreen sem controles, documentacao desatualizada, release
**Dependencia:** Sprints 42, 43 e 44 (executar APOS todas as anteriores)

## Objetivo

1. Atualizar o fullscreen preview do calibrador para refletir as novas configuracoes
2. Atualizar toda documentacao impactada pelas Sprints 42-44
3. Preparar release v2.7.0

## Contexto

O fullscreen preview (abre ao clicar duas vezes no resultado) atualmente e uma janela maximizada que so mostra o resultado sem controles. Apos as Sprints 42-44, ele precisa refletir as novas configuracoes (edge boost corrigido, rampas expandidas, etc.).

## Tarefas

### 45.1 - Fullscreen Preview com overlay de controles

**Arquivo:** `src/core/gtk_calibrator.py`

O metodo `_open_fullscreen_preview` (linha 1496) cria uma janela maximizada apenas com a imagem. Adicionar um overlay de controles basicos que aparece ao mover o mouse e desaparece apos 3 segundos:

**Controles no overlay:**
- Combo de rampa (mesmo combo_ramp_preset)
- Checkbox Edge Boost + slider de intensidade
- Checkbox Edge Chars
- Modo ASCII/PixelArt (radio buttons)
- Botao de fechar (volta pro calibrador)

**Implementacao:**
```python
def _open_fullscreen_preview(self):
    if self._fullscreen_window:
        self._fullscreen_window.destroy()

    self.window.hide()

    fs_win = Gtk.Window(title="Extase em 4R73 - Preview")
    fs_win.set_wmclass("extase-em-4r73", "Extase em 4R73")

    screen = Gdk.Screen.get_default()
    css = Gtk.CssProvider()
    css.load_from_data(b"""
        window { background-color: #000000; }
        .fs-overlay {
            background-color: rgba(30, 20, 40, 0.85);
            border-radius: 10px;
            padding: 8px 16px;
            margin: 8px;
        }
    """)
    Gtk.StyleContext.add_provider_for_screen(
        screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    fs_win.maximize()

    overlay = Gtk.Overlay()
    aspect = Gtk.AspectFrame(xalign=0.5, yalign=0.5, ratio=self.source_aspect_ratio, obey_child=False)
    img = Gtk.Image()
    aspect.add(img)
    overlay.add(aspect)

    controls_box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER, valign=Gtk.Align.END)
    controls_box.get_style_context().add_class("fs-overlay")

    # Adicionar combo de rampa, edge boost checkbox+slider, edge chars checkbox
    # ... widgets sincronizados com os do calibrador principal

    btn_close = Gtk.Button(label="Voltar")
    btn_close.connect("clicked", lambda w: self._close_fullscreen_to_calibrator())
    controls_box.pack_end(btn_close, False, False, 0)

    overlay.add_overlay(controls_box)

    fs_win.add(overlay)
    # ... resto da logica
```

**IMPORTANTE:** Ao fechar o fullscreen, deve VOLTAR para o calibrador (nao fechar tudo):
```python
def _close_fullscreen_to_calibrator(self):
    if self._fullscreen_window:
        try:
            self._fullscreen_window.destroy()
        except Exception:
            pass
        self._fullscreen_window = None
        self._fullscreen_image = None
        self._fullscreen_aspect = None
    self.window.show()
```

Modificar `_on_fullscreen_key_press` para que Q/Escape tambem volte ao calibrador ao inves de fechar tudo. Nao chamar `Gtk.main_quit()`.

Modificar `_close_fullscreen` (linha 1537) para PARAR de chamar `Gtk.main_quit()`:
```python
def _close_fullscreen(self):
    if self._fullscreen_window:
        try:
            self._fullscreen_window.destroy()
        except Exception:
            pass
        self._fullscreen_window = None
        self._fullscreen_image = None
        self._fullscreen_aspect = None
    self.window.show()
```

### 45.2 - Atualizar CONFIG_REFERENCE.md

**Arquivo:** `docs/CONFIG_REFERENCE.md`

- Remover tabela de presets Studio/Natural/Bright (linhas 87-89)
- Atualizar descricao do edge_boost_enabled: "Escurece bordas para caracteres mais densos (ASCII) ou maior contraste (Pixel Art)"
- Atualizar descricao do use_edge_chars: "Aplica caracteres direcionais apenas em bordas fortes"

### 45.3 - Atualizar USER_MANUAL.md

**Arquivo:** `docs/USER_MANUAL.md`

- Remover secao de presets Studio/Natural/Bright (linhas 80-82)
- Atualizar descricao do calibrador: janelas agora sao Origem | Processamento | Destino
- Atualizar descricao do Edge Boost: "Aumenta densidade dos caracteres nas bordas para melhor definicao"
- Atualizar descricao do Edge Chars: "Adiciona caracteres direcionais nas bordas mais fortes"
- Adicionar nota sobre Edge Boost funcionando em Pixel Art

### 45.4 - Atualizar PRESETS_REFERENCE.md

**Arquivo:** `docs/PRESETS_REFERENCE.md`

- Remover entrada "Detalhado" da tabela de presets
- Atualizar coluna "Caracteres por Preset" com os novos valores de blocks, arrows, dots, letters
- Atualizar secao "Como Escolher" para refletir rampas expandidas

### 45.5 - Atualizar SPRINT_41_CONFLITOS_FEATURES.md

**Arquivo:** `docs/SPRINT_41_CONFLITOS_FEATURES.md`

- Atualizar linha "Edge Boost + PixelArt | SEM EFEITO" para "Edge Boost + PixelArt | FUNCIONAL | Edge Boost escurece bordas antes da quantizacao"
- Remover validacao que desabilita edge_boost para PixelArt

### 45.6 - Atualizar CHANGELOG.md

**Arquivo:** `docs/CHANGELOG.md`

Adicionar entrada no topo:

```markdown
## [2.7.0] - 2026-04-XX

### Calibrador - Limpeza UI
- Janelas reordenadas: Origem | Processamento | Destino
- Removidos presets chroma (Studio/Natural/Bright) -- substituidos por Auto Seg
- Removidas acoes chroma (Auto/Reset) -- desnecessarias com Auto Seg
- Fullscreen preview com overlay de controles e retorno ao calibrador

### Rampas de Luminancia
- Restauradas rampas unicode: Blocos (5 chars) e Setas (11 chars)
- Expandida rampa Pontos (2 -> 10 chars com gradiente de pontos unicode)
- Expandida rampa Binario (3 -> 7 chars)
- Corrigida rampa Letras (removidos chars repetidos)
- Removida rampa Detalhado (redundante com Padrao)

### Edge Detection
- Edge Boost corrigido: escurece bordas (caracteres mais densos) ao inves de clarear
- Edge Boost normalizado: intensidade relativa ao comprimento da rampa
- Edge Chars corrigido: aplica apenas em bordas fortes (2x threshold)
- Edge Boost funciona em Pixel Art: escurece bordas antes da quantizacao
```

### 45.7 - Atualizar CHANGELOG nos outros formatos

**Arquivos:**
- `CHANGELOG.md` (raiz do projeto)
- `CHANGELOG.html` (raiz do projeto)
- `CHANGELOG.txt` (raiz do projeto)

Sincronizar com o conteudo de `docs/CHANGELOG.md`.

### 45.8 - Atualizar README.md

**Arquivo:** `README.md`

- Atualizar versao para 2.7.0
- Atualizar lista de features se necessario (Edge Boost agora funciona em PixelArt)

### 45.9 - Atualizar pyproject.toml

**Arquivo:** `pyproject.toml`

- Atualizar versao para 2.7.0

### 45.10 - Release

Apos todas as sprints implementadas e verificadas:
1. Commit com mensagem: `release: v2.7.0 - calibrador UI, rampas e edge detection corrigidos`
2. Tag: `v2.7.0`
3. Build dos pacotes:
   ```bash
   ./packaging/build-deb.sh
   ./packaging/build-appimage.sh
   ```

## Verificacao Final (pos-release)

1. Abrir calibrador e verificar TODAS as mudancas das Sprints 42-44
2. Testar fullscreen preview com controles
3. Verificar que o fullscreen VOLTA ao calibrador (nao fecha tudo)
4. Executar validacao completa:
   ```bash
   python cli.py validate --video data_input/Luna_flertando.mp4
   ```
5. Verificar que docs refletem o estado atual do software
6. Verificar que CHANGELOG esta consistente em todos os formatos
