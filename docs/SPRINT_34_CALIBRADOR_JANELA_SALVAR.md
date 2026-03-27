# Sprint 34: Calibrador - Janela Maximizada, Botao Salvar e Tecla Space

**Prioridade:** CRITICA
**Resolve:** BUG-01, BUG-02, BUG-19

## Objetivo

Resolver os 3 bugs mais visiveis ao usuario no calibrador:
1. Janela nao inicia maximizada (botoes cortados)
2. Botao Salvar fecha a janela em vez de apenas salvar
3. Tecla Space nao pausa o video (on_key_press duplicado)

## Arquivos a Modificar

- `src/gui/calibrator.glade` (linhas 114-115)
- `src/core/gtk_calibrator.py` (linhas 1614-1622, 2546, 2579-2603, 2632-2638)

## Tarefas

### 34.1 - Glade: Aumentar tamanho padrao da janela

**Arquivo:** `src/gui/calibrator.glade`
**Linhas:** 114-115

```xml
<!-- ANTES -->
<property name="default-width">1100</property>
<property name="default-height">650</property>

<!-- DEPOIS -->
<property name="default-width">1920</property>
<property name="default-height">1080</property>
```

### 34.2 - Python: Mover maximize() para depois de show_all()

**Arquivo:** `src/core/gtk_calibrator.py`
**Funcao:** `run()` (linha ~2632)

```python
# ANTES:
def run(self):
    self.window.maximize()
    self.window.show_all()
    self._update_mode_visibility()
    GLib.timeout_add(33, self._update_frame)
    Gtk.main()

# DEPOIS:
def run(self):
    self.window.show_all()
    self._update_mode_visibility()
    self.window.maximize()
    GLib.timeout_add(33, self._update_frame)
    Gtk.main()
```

### 34.3 - Python: Remover close automatico do Salvar

**Arquivo:** `src/core/gtk_calibrator.py`
**Funcao:** `on_save_config_clicked()` (linha ~2546)

REMOVER a linha:
```python
GLib.timeout_add(300, self._close_after_save)
```

O bloco try deve ficar assim:
```python
    try:
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
        self.config_last_load = os.path.getmtime(self.config_path)
        self._set_status("Config salvo!")
    except Exception as e:
        self._set_status(f"Erro: {e}")
```

### 34.4 - Python: Mesclar on_key_press duplicado

**Arquivo:** `src/core/gtk_calibrator.py`

1. REMOVER a primeira definicao de `on_key_press` (linhas 1614-1622):
```python
# REMOVER ESTAS LINHAS:
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_q or event.keyval == Gdk.KEY_Q:
            self._cleanup()
            Gtk.main_quit()
            return True
        elif event.keyval == Gdk.KEY_space:
            self._toggle_pause()
            return True
        return False
```

2. Na segunda definicao (linha ~2579), ADICIONAR handler para Space:
```python
    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)

        if keyname in ['q', 'Q', 'Escape']:
            self._cleanup()
            Gtk.main_quit()
            return True

        if keyname == 'space':
            self._toggle_pause()
            return True

        if keyname == 's':
            self.on_save_config_clicked(None)
            return True

        if keyname == 'r':
            self.on_reset_clicked(None)
            return True

        if keyname == 'a':
            self.on_auto_detect_clicked(None)
            return True

        if keyname == 't':
            self._save_and_open_preview()
            return True

        return False
```

## Verificacao

1. Abrir a GUI principal
2. Selecionar um video ou clicar em Calibrar sem video (webcam)
3. Verificar: janela inicia MAXIMIZADA, todos os botoes visiveis
4. Clicar no botao verde "Salvar" - janela deve CONTINUAR ABERTA, status bar mostra "Config salvo!"
5. Pressionar Space - video deve pausar/retomar
6. Pressionar Q ou Escape - janela fecha normalmente
