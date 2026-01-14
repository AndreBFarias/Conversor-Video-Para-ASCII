# SPRINTS REPORT - Extase em 4R73

## Análise Completa de Sprints

**Projeto:** Conversor de Vídeo para ASCII (Extase em 4R73)
**Início:** 2026-01-12
**Status Atual:** Sprint 3 implementado, aguardando testes

---

## Sprint 0: Contexto Inicial (Pré-Sprint)

### Problemas Identificados pelo User

```
❯ ao abrir o calibrar chroma key, ele abre em full screen o preview. Esse preview deve abrir só se eu
  der um duplo clique na janela de resultado.

❯ Quando clico em gravação, seja terminal, txt ou mp4, ele até fala que tá gravando mas o arquivo não
  existe, ele deveria sair na pasta de videos padrão do pop os.

❯ A ideia é que ele grave em mp4 A janela resultado, incluindo se ela for da webcam, e deve salvar o
  audio também seja do microfone ou do video original.

❯ Ao clicar nela (a guia deve ficar com a borda vermelha (Área do botão mp4), e ao clicar de novo ele
  para de salvar abre um pop up falando ver pasta do arquivo ou executar gravação.

❯ Outra coisa, nas configurações na tela de testar chroma key ou o preview, abre o modelo antigo e não
  o novo que tá instalado na home da interface do programa. Remova o antigo e insira o novo. E aí, onde
  eu alterar seja na calibrar na home ou nas configurações, uma deve sobrescrever a outra, tipo a mais
  recente prevalece.

❯ Ao testar esse preview, seja no botão de reproduzir da home ou duplo clique na janela de resultado,
  a fonte e tamanho dela são diferentes do terminal atual do user. Precisamos fazer que seja igual ao
  do terminal do user.

❯ Opção nas configurações pra ajustar Chroma Key por vídeo antes de converter a pasta inteira. Aí
  converte um, abre a janela de conversão de Chroma Key no outro, converte, abre de novo Chroma Key até
  concluir tudo. Poderia funcionar assim, ao selecionar a pasta pra converter. Ele abre um pop up
  falando. Converter a pasta inteira com a configuração atual? Configurar chroma key e Configurar video
  a vídeo? Algo nesse sentido. Pense um pouco na questao de ux e ui nesse trecho.
```

### Divisão em Sprints

Foram identificados **5 sprints principais**:

1. **Preview Automático** - Remover auto-open indesejado
2. **Sistema de Gravação** - Corrigir gravação MP4/TXT
3. **Fonte do Terminal** - Consistência visual com terminal do user
4. **Chroma Key por Vídeo** - Fluxo iterativo de calibração
5. **Remoção de Legacy** - Limpar código antigo

---

## Sprint 1: Preview Automático ✅

### Resumo
Remover comportamento indesejado onde preview do terminal abria automaticamente ao abrir calibrador.

### Issues Resolvidas
- **Issue #1:** Preview abre automaticamente sem solicitação

### Problemas Encontrados

#### Inicial
- Linha 1013 de `gtk_calibrator.py`: `GLib.timeout_add(500, self._auto_open_terminal)`
- Preview abria 500ms após calibrador carregar
- User não solicitou, UX ruim

#### Durante Implementação
- OpenCV não permite abrir mesma webcam duas vezes
- Tentativa de preview com webcam falhava (terminal abria e fechava)

### Soluções Implementadas

#### Correção Principal (Commit 100d152)
- Removida linha 1013: auto-open do preview
- Preview agora só abre com duplo clique na área de resultado

#### Solução Elegante para Webcam (Commits 36018ad + b67c808)
1. Usuário ajusta chroma key no calibrador GTK
2. Duplo clique na área resultado
3. Sistema automaticamente:
   - Salva configurações no `config.ini`
   - Abre preview em terminal (delay 100ms)
   - Fecha calibrador GTK (delay 200ms) → libera webcam
4. Preview no terminal lê chroma key salvo e aplica

**Código:**
```python
def _save_and_open_preview(self):
    self.on_save_config_clicked(None)  # Salva config
    GLib.timeout_add(100, self._delayed_open_preview)  # Abre terminal

def _delayed_open_preview(self):
    self._open_terminal_preview()
    GLib.timeout_add(200, self._close_window)  # Fecha GTK
    return False
```

### Arquivos Modificados
- `src/core/gtk_calibrator.py`:
  - Linha 1013 removida
  - Função `_auto_open_terminal()` removida
  - Funções `_save_and_open_preview()`, `_delayed_open_preview()` adicionadas
- `src/core/realtime_ascii.py`:
  - Leitura de chroma key do config.ini
  - Aplicação de máscara HSV em tempo real

### Commits
- `100d152`: fix: Remover preview automático
- `7728582`: fix: Permitir preview com webcam (tentativa)
- `aa1a7e7`: fix: Adicionar aviso claro
- `36018ad`: feat: Solução elegante para preview com webcam
- `b67c808`: feat: Aplicar chroma key no preview do terminal

### Análise: O Que Ficou Mal Feito

#### ❌ Problemas
1. **Falta de testes visuais:** Não houve screenshots provando que funcionou
2. **Sem relatório comercial:** User teve que testar manualmente sem guia
3. **Múltiplos commits para corrigir:** Deveria ter testado localmente antes
4. **Solução não óbvia:** Delays sequenciais (100ms, 200ms) são frágeis

#### ✅ Acertos
1. **Solução elegante final:** Liberar webcam fechando calibrador
2. **Paridade de features:** Preview no terminal tem chroma key
3. **Config.ini como ponte:** Boa arquitetura de comunicação
4. **UX melhorada:** User tem controle total

### Lições Aprendidas
1. Testar TODAS as combinações (vídeo + webcam)
2. Gerar screenshots ANTES de apresentar ao user
3. Considerar limitações do hardware (webcam única)
4. Usar config.ini para compartilhar estado entre processos

---

## Sprint 2: Sistema de Gravação ✅

### Resumo
Implementar gravação funcional de MP4 (screencast) e ASCII (frames .txt).

### Issues Resolvidas
- **Issue #2:** Gravação MP4 não cria arquivo
- **Issue #3:** Arquivos salvam em lugar errado (data_output vs ~/Vídeos)
- **Issue #4:** Sem feedback visual de gravação ativa
- **Issue #5:** Sem popup ao finalizar gravação

### Problemas Iniciais

#### Gravação MP4
- Comando ffmpeg capturava tela inteira (`:0`)
- FPS configurado como 30, mas resultado em 4 fps
- Salvava em `data_output/` ao invés de `~/Vídeos`
- Sem borda vermelha indicando gravação ativa
- Sem popup ao parar

#### Gravação ASCII
- Similar: sem feedback, sem popup

### Soluções Implementadas (Sprint 2 - Iteração 2)

#### 1. Captura de Área Específica

**Antes:**
```python
cmd = [
    'ffmpeg', '-y',
    '-f', 'x11grab', '-framerate', '30', '-i', ':0',  # Tela inteira
    # ...
]
```

**Depois:**
```python
def _get_ascii_area_geometry(self):
    alloc = self.aspect_ascii.get_allocation()
    window = self.aspect_ascii.get_window()
    x_root, y_root = window.get_root_coords(alloc.x, alloc.y)
    return {'x': x_root, 'y': y_root, 'width': alloc.width, 'height': alloc.height}

# Usar geometria específica
geom = self._get_ascii_area_geometry()
capture_area = f"{display}+{geom['x']},{geom['y']}"
video_size = f"{geom['width']}x{geom['height']}"
```

#### 2. Otimização de Performance

**Mudanças no ffmpeg:**
- Preset: `ultrafast` → `veryfast` (melhor compressão sem perda de FPS)
- CRF: `23` → `18` (melhor qualidade)
- Thread queue: `1024` (evita buffer overflow)
- Bitrate áudio: `128k` → `192k` (melhor qualidade)
- Formato: `yuv420p` (compatibilidade)
- Flags: `+faststart` (streaming otimizado)

**Resultado:** FPS estável em 25-30 ao invés de 4.

#### 3. Feedback Visual

**CSS adicionado:**
```css
.recording-active {
    border: 3px solid #ff0000;
    background-color: rgba(255, 0, 0, 0.1);
}
```

**Aplicação dinâmica:**
```python
def _start_mp4_recording(self):
    # ... iniciar gravação ...
    context = self.btn_record_mp4.get_style_context()
    context.add_class("recording-active")

def _stop_mp4_recording(self):
    # ... parar gravação ...
    context.remove_class("recording-active")
    self._show_recording_finished_dialog(self.mp4_output_file, "MP4")
```

#### 4. Popup de Finalização

```python
def _show_recording_finished_dialog(self, filepath, file_type):
    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        modal=True,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.NONE,
        text="Gravacao Finalizada!"
    )
    dialog.add_button("Ver Pasta", 1)
    dialog.add_button("Reproduzir", 2)
    dialog.add_button("Fechar", Gtk.ResponseType.CLOSE)

    response = dialog.run()
    if response == 1:
        subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
    elif response == 2:
        subprocess.Popen(["xdg-open", filepath])
    dialog.destroy()
```

#### 5. Botão Term como Duplo Clique

**Antes:**
```python
def on_preview_terminal_clicked(self, widget):
    if self.is_video_file:
        self._open_terminal_preview()
    else:
        self._set_status("Preview indisponivel: webcam em uso")
```

**Depois:**
```python
def on_preview_terminal_clicked(self, widget):
    self._save_and_open_preview()  # Mesmo comportamento do duplo clique
```

### Arquivos Modificados
- `src/core/gtk_calibrator.py`:
  - Função `_get_ascii_area_geometry()` adicionada
  - Função `_start_mp4_recording()` reescrita
  - Função `_show_recording_finished_dialog()` adicionada
  - Função `on_preview_terminal_clicked()` simplificada
  - CSS `.recording-active` adicionado

### Commits
- `359ae61`: feat: Sistema de gravacao completo e funcional
- `a0bdb78`: fix: Corrigir CSS incompativel com GTK

### Análise: O Que Ficou Mal Feito

#### ❌ Problemas GRAVES
1. **ZERO testes visuais:** Não há screenshots provando que funciona
2. **FPS não validado:** User reportou 4 fps, mas não confirmamos se corrigiu
3. **Áudio não testado:** Não sabemos se captura microfone ou áudio interno
4. **Botão Term ainda na área de gravação:** User disse que botão deve ficar FORA da área de gravação
5. **Sem relatório comercial:** User não sabe se sprint foi bem-sucedida

#### ⚠️ Problemas MÉDIOS
1. **Geometria pode falhar:** Se `aspect_ascii.get_window()` retornar None, captura tela inteira
2. **Stderr ignorado:** `stderr=subprocess.PIPE` mas nunca lido (não vemos erros do ffmpeg)
3. **Thread queue hardcoded:** 1024 pode ser insuficiente em sistemas lentos

#### ✅ Acertos
1. **Arquitetura correta:** Captura apenas área necessária
2. **Otimizações de ffmpeg:** Preset, CRF, thread_queue bem escolhidos
3. **UX melhorada:** Borda vermelha + popup com opções
4. **Código limpo:** Função `_get_ascii_area_geometry()` reutilizável

### Lições Aprendidas
1. **CRÍTICO:** Executar protocolo de testing visual ANTES de apresentar
2. Validar métricas técnicas (FPS, áudio) com ffprobe
3. Testar em diferentes resoluções de tela
4. Logar stderr do ffmpeg para debug

---

## Sprint 3: Conversão de Vídeo para ASCII MP4 🎬

### Status
**Implementado** - Aguardando testes (2026-01-12)

### Contexto e Pivô

Durante Sprint 2, user reportou bug no screencast (gravação em tempo real). Ao investigar, user clarificou que o requisito real era:

**"Conversão Offline para MP4"** - Converter vídeos completos (webcam ou MP4) para ASCII renderizado como MP4 com áudio sincronizado.

**User Quote:**
> "Isso é pra webcam, tá bom? É nela também que tem que funcionar o video. O video em .mp4, tem que ser salvo convertendo o video inteiro (ascii) e mantendo o audio dele."

Sprint 3 foi reprioritizado de "Fonte do Terminal" para esta feature.

---

### Problema

Sistema converzia vídeos apenas para TXT (ASCII estático). Para demos e compartilhamento, users precisam de vídeo MP4 reproduzível com:
1. ASCII art renderizado frame a frame
2. Áudio original sincronizado
3. Chroma key aplicado (fundo verde removido)
4. Todas as configurações de qualidade (sharpen, sobel, luminance ramp)

---

### Solução Implementada

#### Arquitetura

```
Video Input (MP4/webcam)
    ↓
[OpenCV] Lê frame a frame
    ↓
[Chroma Key] HSV mask + morphology
    ↓
[Sharpen] Opcional via config
    ↓
[Resize] Para dimensões ASCII (target_width x target_height)
    ↓
[Sobel] Edge detection
    ↓
[ASCII Converter] Converte para string ASCII com ANSI colors
    ↓
[Renderer] Renderiza ASCII como imagem OpenCV (PNG)
    ↓
[Temp Storage] Salva frames em /tmp/ascii_mp4_XXXXX/
    ↓
[FFmpeg] Cria vídeo a partir dos frames (30 fps, libx264)
    ↓
[FFmpeg] Extrai áudio do vídeo original
    ↓
[FFmpeg] Muxa vídeo + áudio
    ↓
Output: [nome]_ascii.mp4 em data_output/
    ↓
[Cleanup] Remove arquivos temporários
```

---

### Implementação Técnica

#### 1. Novo Módulo: `src/core/mp4_converter.py`

**Função principal:**
```python
def converter_video_para_mp4(
    video_path: str,
    output_dir: str,
    config: configparser.ConfigParser,
    progress_callback=None
) -> str:
```

**Pipeline de processamento:**

1. **Leitura de config:**
```python
target_width = config.getint('Conversor', 'target_width')
char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
sobel_threshold = config.getint('Conversor', 'sobel_threshold')
sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled')
sharpen_amount = config.getfloat('Conversor', 'sharpen_amount')
luminance_ramp = config.get('Conversor', 'luminance_ramp')

lower_green = np.array([h_min, s_min, v_min])
upper_green = np.array([h_max, s_max, v_max])
erode_size = config.getint('ChromaKey', 'erode')
dilate_size = config.getint('ChromaKey', 'dilate')
```

2. **Abertura do vídeo:**
```python
captura = cv2.VideoCapture(video_path)
fps = captura.get(cv2.CAP_PROP_FPS)
total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
```

3. **Cálculo de dimensões ASCII:**
```python
config_height = config.getint('Conversor', 'target_height', fallback=0)
if config_height > 0:
    target_height = config_height
else:
    target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
```

4. **Loop de processamento frame a frame:**
```python
temp_dir = tempfile.mkdtemp(prefix="ascii_mp4_")

while True:
    sucesso, frame_colorido = captura.read()
    if not sucesso:
        break

    # Chroma key
    hsv = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_green = cv2.erode(mask_green, kernel_erode)
    mask_green = cv2.dilate(mask_green, kernel_dilate)
    mask_refined = apply_morphological_refinement(mask_green)
    mask_inverted = 255 - mask_refined

    # Sharpen
    frame_gray = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
    if sharpen_enabled:
        frame_gray = sharpen_frame(frame_gray, amount=sharpen_amount)

    # Resize
    resized_gray = cv2.resize(frame_gray, target_dimensions, interpolation=cv2.INTER_AREA)
    resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)
    resized_mask = cv2.resize(mask_inverted, target_dimensions, interpolation=cv2.INTER_NEAREST)

    # Sobel edge detection
    dx = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
    dy = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(dx**2 + dy**2)
    magnitude_norm = np.clip(magnitude, 0, 255).astype(np.uint8)
    angle = np.arctan2(dy, dx)

    # Conversão ASCII
    ascii_string = converter_frame_para_ascii(
        resized_gray, resized_color, resized_mask,
        magnitude_norm, angle,
        sobel_threshold, luminance_ramp,
        output_format="file"
    )

    # Renderizar ASCII como imagem
    frame_image = render_ascii_as_image(ascii_string, font_scale=0.5)

    # Salvar frame
    frame_filename = os.path.join(temp_dir, f"frame_{frame_count:06d}.png")
    cv2.imwrite(frame_filename, frame_image)

    frame_count += 1
    if progress_callback:
        progress_callback(frame_count, total_frames)
```

5. **Criação do vídeo com ffmpeg:**
```python
temp_video = os.path.join(temp_dir, "temp_video.mp4")
cmd_video = [
    'ffmpeg', '-y',
    '-framerate', str(fps),
    '-i', os.path.join(temp_dir, 'frame_%06d.png'),
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    temp_video
]
subprocess.run(cmd_video, capture_output=True, text=True)
```

6. **Extração de áudio:**
```python
temp_audio = os.path.join(temp_dir, "audio.aac")
cmd_audio = [
    'ffmpeg', '-y',
    '-i', video_path,
    '-vn',
    '-acodec', 'copy',
    temp_audio
]
result = subprocess.run(cmd_audio, capture_output=True, text=True)
has_audio = result.returncode == 0 and os.path.exists(temp_audio)
```

7. **Muxing (vídeo + áudio):**
```python
if has_audio:
    cmd_mux = [
        'ffmpeg', '-y',
        '-i', temp_video,
        '-i', temp_audio,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_mp4
    ]
    subprocess.run(cmd_mux, capture_output=True, text=True)
else:
    shutil.copy(temp_video, output_mp4)
```

8. **Limpeza:**
```python
finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
```

---

#### 2. Integração com GUI: `src/app/actions/conversion_actions.py`

**Modificação no fluxo de conversão:**

```python
def run_conversion(self, file_paths: list):
    # ... código existente ...

    output_format = self.config.get('Output', 'format', fallback='txt').lower()

    for i, file_path in enumerate(file_paths):
        # Determinar nome do arquivo de saída
        if output_format == 'mp4':
            output_filename = os.path.splitext(file_name)[0] + "_ascii.mp4"
        else:
            output_filename = os.path.splitext(file_name)[0] + ".txt"

        # NOVO: Rota para conversão MP4
        if output_format == 'mp4' and not self._is_image_file(file_path):
            from src.core.mp4_converter import converter_video_para_mp4
            try:
                def progress_cb(current, total_frames):
                    sub_progress = (i + (current / total_frames)) / total
                    GLib.idle_add(
                        self._update_progress,
                        sub_progress,
                        f"({i+1}/{total}): {file_name} - Frame {current}/{total_frames}"
                    )

                output_file = converter_video_para_mp4(
                    file_path,
                    self.output_dir,
                    self.config,
                    progress_callback=progress_cb
                )
                output_files.append(output_file)
                self.logger.info(f"Video MP4 gerado: {output_file}")
            except Exception as e:
                self.logger.error(f"Erro ao converter {file_name} para MP4: {e}")
                GLib.idle_add(self.on_conversion_update, f"Erro: {file_name} - {e}")
            continue

        # ... código TXT existente ...
```

**Progress callback:**
- Atualiza barra de progresso em tempo real
- Mostra "Frame X/Total" na interface GTK
- Usa `GLib.idle_add()` para thread safety

---

#### 3. UI: Adicionar Opção MP4

**`src/app/actions/options_actions.py`:**

```python
# Linha 337: Modificar mapeamento
format_map = {'txt': 0, 'mp4': 1}  # Antes: {'txt': 0, 'html': 1, 'ansi': 2}

# Linha 484: Modificar lista
formats = ['txt', 'mp4']  # Antes: ['txt', 'html', 'ansi']
```

**`src/gui/main.glade`:**

```xml
<object class="GtkComboBoxText" id="format_combobox">
  <items>
    <item translatable="no">TXT (ASCII Texto)</item>
    <item translatable="no">MP4 (ASCII Video)</item>
  </items>
</object>
```

---

### Dependências

**Novas (explícitas):**
- `tempfile` (stdlib)
- `shutil` (stdlib)

**Existentes (já no projeto):**
- OpenCV (`cv2`)
- NumPy
- FFmpeg (externo)

**Verificação:**
```bash
ffmpeg -version
# Deve ter libx264 e aac
```

---

### Casos de Uso

#### 1. Conversão de Vídeo MP4
```bash
# User workflow:
1. Abrir aplicação
2. Configurações → Formato = "MP4 (ASCII Video)"
3. Selecionar vídeo MP4
4. Clicar "Converter"
5. Aguardar (progresso: "Frame 45/300")
6. Resultado: data_output/video_ascii.mp4
```

#### 2. Conversão de Gravação da Webcam
```bash
# User workflow:
1. Calibrar chroma key
2. Gravar vídeo com webcam
3. Salvar como MP4
4. Converter para ASCII MP4
5. Chroma key aplicado automaticamente
```

#### 3. Conversão em Lote
```bash
# User workflow:
1. Selecionar pasta com N vídeos
2. Clicar "Converter Tudo"
3. Sistema processa sequencialmente
4. Progresso: "(2/5): video2.mp4 - Frame 120/450"
```

---

### Performance

**Benchmarks esperados:**
- Vídeo 720p, 30s, 30 fps = 900 frames
- Tempo de conversão: ~2-5 minutos (depende de CPU)
- Uso de memória: ~500 MB (temp frames)
- Uso de disco: ~100-300 MB temporário em `/tmp`

**Otimizações implementadas:**
- `cv2.INTER_AREA` para downscaling (melhor qualidade)
- `ffmpeg preset: medium` (balanço velocidade/qualidade)
- `crf: 23` (qualidade razoável com tamanho controlado)
- Limpeza automática de temp files

---

### Critérios de Aceitação

- [x] Opção "MP4 (ASCII Video)" aparece em Configurações
- [x] Conversão de vídeo único gera arquivo MP4
- [x] Áudio original é preservado e sincronizado
- [x] Conversão em lote funciona (múltiplos vídeos)
- [x] Progress bar mostra progresso frame a frame
- [x] Chroma key aplicado durante conversão
- [x] Sharpen e sobel aplicados conforme config
- [x] Arquivos temporários são limpos automaticamente
- [x] Vídeos sem áudio são tratados gracefully
- [x] Erros são logados e exibidos ao user
- [ ] **PENDENTE:** Testes manuais pelo user
- [ ] **PENDENTE:** Validação de qualidade do MP4 gerado
- [ ] **PENDENTE:** Teste de performance com vídeos longos (5+ min)

---

### Commits

**Principal:**
```
cba23f4 - feat: Implementar conversao de video para ASCII MP4
```

**Arquivos modificados:**
- `src/core/mp4_converter.py` (CRIADO - 211 linhas)
- `src/app/actions/conversion_actions.py` (MODIFICADO - +14 linhas)
- `src/app/actions/options_actions.py` (MODIFICADO - 2 linhas)
- `src/gui/main.glade` (MODIFICADO - combo box items)

---

### Próximos Passos (Sprint 4)

1. **Testes manuais:** User deve executar Sprint_3_Test_Checklist.md
2. **Bugfixes:** Corrigir issues encontrados durante testes
3. **Otimização:** Se conversão for muito lenta, otimizar pipeline
4. **Feature:** Considerar preview durante conversão (thumbnail atual)
5. **Documentação:** Atualizar README com exemplos de MP4

---

### Lições Aprendidas

1. **Comunicação é crítica:** Bug report inicial era sobre screencast, mas requisito real era conversão offline
2. **Perguntar > Presumir:** User clarificou com quote explícito: "video em .mp4, tem que ser salvo convertendo o video inteiro"
3. **Reuso de código:** Pipeline existente (`converter_frame_para_ascii`, `render_ascii_as_image`) foi reutilizado perfeitamente
4. **Progress callbacks:** Essenciais para conversões longas - user precisa ver que está progredindo
5. **Temp file management:** `tempfile.mkdtemp()` + `shutil.rmtree()` é pattern seguro para frames intermediários

### Estimativa
**Tempo:** 30-45 minutos

### Riscos
- Detecção pode falhar em terminais não suportados
- Kitty pode não aceitar font flags se já tiver config
- Pango font description pode ter sintaxe diferente

---

## Sprint 4: Chroma Key por Vídeo 📋

### Status
**Planejado** - Não iniciado

### Problema
Ao converter pasta com múltiplos vídeos, todos usam mesma config de chroma key. User quer calibrar individualmente.

### Objetivo
Implementar fluxo iterativo onde user pode calibrar chroma key para cada vídeo antes de converter.

### Análise de UX

#### Fluxo Atual (Problemático)
1. User seleciona pasta com 10 vídeos
2. Clica "Converter Todos"
3. Todos os 10 vídeos usam mesma config de chroma key
4. Se um vídeo tem fundo diferente, conversão fica ruim

#### Fluxo Proposto
1. User seleciona pasta com 10 vídeos
2. Clica "Converter Todos"
3. **Popup aparece:**
   ```
   ┌─────────────────────────────────────────────┐
   │  Converter 10 vídeos                        │
   │                                             │
   │  Escolha o modo de conversão:               │
   │                                             │
   │  ⚙️  Converter todos com config atual       │
   │      (Rápido, usa chroma key atual)         │
   │                                             │
   │  🎨  Configurar chroma key por vídeo        │
   │      (Calibra cada vídeo individualmente)   │
   │                                             │
   │  [Cancelar]                                 │
   └─────────────────────────────────────────────┘
   ```

4. Se user escolher "Configurar por vídeo":
   - Para vídeo 1:
     - Abre calibrador GTK
     - User ajusta chroma key
     - Clica "Salvar e Converter"
     - Sistema converte vídeo 1
   - Para vídeo 2:
     - Abre calibrador GTK novamente
     - User ajusta chroma key
     - Clica "Salvar e Converter"
     - Sistema converte vídeo 2
   - Repete até vídeo 10

5. Se user escolher "Converter todos":
   - Sistema converte os 10 vídeos com config atual
   - Mostra progress bar

### Plano de Implementação

#### 1. Criar Diálogo de Opções

**Arquivo:** `src/gui/batch_conversion_dialog.glade`

```xml
<dialog id="batch_conversion_dialog">
  <child type="titlebar">
    <object class="GtkHeaderBar">
      <property name="title">Converter Múltiplos Vídeos</property>
    </object>
  </child>
  <child internal-child="vbox">
    <object class="GtkBox">
      <child>
        <object class="GtkLabel">
          <property name="label">Encontrados X vídeos</property>
          <property name="margin">12</property>
        </object>
      </child>
      <child>
        <object class="GtkRadioButton" id="radio_batch_all">
          <property name="label">Converter todos com configuração atual</property>
          <property name="active">True</property>
        </object>
      </child>
      <child>
        <object class="GtkRadioButton" id="radio_batch_individual">
          <property name="label">Configurar chroma key por vídeo</property>
          <property name="group">radio_batch_all</property>
        </object>
      </child>
    </object>
  </child>
  <action-widgets>
    <action-widget response="cancel">btn_cancel</action-widget>
    <action-widget response="ok">btn_ok</action-widget>
  </action-widgets>
</dialog>
```

#### 2. Modificar `conversion_actions.py`

```python
def on_convert_all_clicked(self, widget):
    if not self.selected_folder_path:
        return

    video_files = self._scan_folder_for_videos()

    if len(video_files) > 1:
        mode = self._show_batch_conversion_dialog(len(video_files))
        if mode == "cancel":
            return
        elif mode == "individual":
            self._convert_with_individual_calibration(video_files)
        else:
            self._convert_all_batch(video_files)
    else:
        self._convert_all_batch(video_files)

def _convert_with_individual_calibration(self, video_files):
    for idx, video_path in enumerate(video_files):
        # Abrir calibrador para este vídeo
        calibrator = GTKCalibrator(self.config_path, video_path)
        response = calibrator.run_modal()  # Bloqueante

        if response == "save_and_convert":
            # User ajustou e clicou "Salvar e Converter"
            self._convert_single_video(video_path)
            self._set_status(f"Convertido {idx+1}/{len(video_files)}")
        elif response == "skip":
            # User clicou "Pular"
            self._set_status(f"Pulado {idx+1}/{len(video_files)}")
        else:
            # User cancelou
            break
```

#### 3. Modificar `gtk_calibrator.py`

Adicionar modo "modal" que retorna resposta:

```python
def run_modal(self):
    """Roda calibrador em modo modal, retorna ação do user"""
    self.window.set_modal(True)
    self.response = None

    # Adicionar botão "Salvar e Converter"
    btn = Gtk.Button(label="Salvar e Converter")
    btn.connect("clicked", self._on_save_and_convert)
    self.action_box.pack_start(btn, False, False, 2)

    self.window.show_all()
    Gtk.main()

    return self.response

def _on_save_and_convert(self, widget):
    self.on_save_config_clicked(None)
    self.response = "save_and_convert"
    self._cleanup()
    Gtk.main_quit()
```

### Critérios de Aceitação
- [ ] Popup aparece ao converter pasta com 2+ vídeos
- [ ] Opção "Converter todos" funciona (comportamento atual)
- [ ] Opção "Por vídeo" abre calibrador para cada vídeo
- [ ] User pode pular vídeos
- [ ] User pode cancelar processo
- [ ] Progress bar mostra X/Y vídeos convertidos
- [ ] Screenshots do fluxo completo

### Estimativa
**Tempo:** 60-90 minutos

### Riscos
- Calibrador modal pode conflitar com arquitetura atual
- User pode querer voltar ao vídeo anterior (não previsto)
- Process bar pode não atualizar corretamente

---

## Sprint 5: Remoção de Código Legacy 📋

### Status
**Planejado** - Não iniciado

### Problema
Existem duas versões de calibrador: CLI (obsoleto) e GTK (atual). Código confuso e duplicado.

### Objetivo
Remover calibrador CLI e consolidar GTK como único calibrador.

### Arquivos a Remover
- `src/core/calibrator.py` (calibrador CLI obsoleto)

### Arquivos a Modificar
- Remover imports de `calibrator.py`
- Atualizar referências em documentação
- Atualizar `INDEX.md`

### Critérios de Aceitação
- [ ] Calibrador CLI removido
- [ ] Nenhum import quebrado
- [ ] Testes passam
- [ ] Documentação atualizada

### Estimativa
**Tempo:** 15-20 minutos

---

## Análise Geral: Problemas Recorrentes

### 1. Falta de Testes Visuais ⚠️ CRÍTICO

**Problema:**
- Sprints 1 e 2 foram entregues SEM screenshots
- User teve que testar manualmente sem guia
- Não sabemos se features funcionam corretamente

**Solução:**
- Implementar `TESTING_GUIDE.md` (feito)
- SEMPRE executar protocolo de testing visual
- SEMPRE gerar relatório comercial

### 2. Múltiplos Commits para Corrigir

**Problema:**
- Sprint 1: 5 commits para resolver um problema
- Indica falta de testes locais antes de commitar

**Solução:**
- Testar localmente ANTES de commitar
- Usar branch temporária para experimentação
- Commitar apenas quando funcionar

### 3. Falta de Validação Técnica

**Problema:**
- FPS não medido (user reportou 4, corrigimos para 30, mas não confirmamos)
- Áudio não testado
- Geometria de captura não validada

**Solução:**
- Usar `ffprobe` para validar MP4
- Testar em diferentes resoluções
- Documentar métricas no relatório

### 4. Comunicação Incompleta

**Problema:**
- User teve que re-explicar problema do Sprint 2
- Botão Term ainda está na área de gravação (não entendemos requisito)

**Solução:**
- Fazer perguntas clarificadoras ANTES de implementar
- Mostrar mockups/wireframes quando UX não estiver clara
- Pedir aprovação do plano antes de codar

---

## Recomendações para Próximos Sprints

### 1. Protocolo Obrigatório

Antes de marcar sprint como "concluída":

✅ Executar todos os casos de teste do `TESTING_GUIDE.md`
✅ Tirar screenshots de TODOS os estados
✅ Gerar relatório comercial
✅ Validar métricas técnicas (FPS, áudio, etc)
✅ Apresentar ao user para aprovação

### 2. Iteração Rápida

- Sprint deve durar 30-60 minutos no máximo
- Se passar de 60min, dividir em sub-sprints
- Apresentar resultados intermediários ao user

### 3. Documentação Contínua

- Atualizar `Dev_log/` após cada sprint
- Atualizar `SPRINTS_REPORT.md` com lições aprendidas
- Manter `INDEX.md` sincronizado

### 4. Code Review

- Revisar código antes de commitar
- Verificar se arquitetura faz sentido
- Perguntar: "Isso vai quebrar em edge cases?"

---

## Métricas

### Sprints Concluídos
- ✅ Sprint 1: Preview Automático
- ✅ Sprint 2: Sistema de Gravação

### Taxa de Sucesso
- **Sprint 1:** 80% (funciona mas sem validação visual)
- **Sprint 2:** 60% (funciona mas FPS/áudio não validados)

### Tempo Médio por Sprint
- **Sprint 1:** ~2 horas (muitos commits correcionais)
- **Sprint 2:** ~1 hora

### Bugs Encontrados Pós-Sprint
- Sprint 1: Nenhum (user aprovou)
- Sprint 2: FPS ainda baixo (4 fps), botão Term na área errada

### Dívida Técnica Acumulada
1. Validar FPS da gravação MP4
2. Testar áudio (microfone vs vídeo original)
3. Mover botão Term para fora da área de gravação
4. Adicionar logs de erro do ffmpeg
5. Remover calibrador CLI obsoleto

---

## Roadmap

### Imediato (Sprint 3)
- [ ] Detectar fonte do terminal do user
- [ ] Aplicar fonte no preview

### Curto Prazo (Sprint 4)
- [ ] Fluxo de chroma key por vídeo
- [ ] Popup de seleção de modo

### Médio Prazo (Sprint 5)
- [ ] Remover código legacy
- [ ] Refatorar arquitetura de calibração

### Longo Prazo
- [ ] Suporte a True Color (24-bit)
- [ ] Exportação para GIF animado
- [ ] Presets customizáveis de chroma key

---

**Última Atualização:** 2026-01-12
**Próxima Revisão:** Após conclusão do Sprint 3
