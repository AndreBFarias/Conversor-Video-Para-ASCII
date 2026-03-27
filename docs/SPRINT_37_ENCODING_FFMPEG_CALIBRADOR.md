# Sprint 37: Encoding FFmpeg do Calibrador

**Prioridade:** MEDIA
**Resolve:** BUG-10
**Dependencia:** Nenhuma

## Objetivo

Alinhar o encoding FFmpeg da gravacao MP4 do calibrador com o pipeline padrao usado por todos os outros converters.

## Arquivo a Modificar

- `src/core/gtk_calibrator.py` (linhas 1357-1369)

## Tarefa

### 37.1 - Atualizar cmd_video na gravacao MP4

**Funcao:** `_stop_mp4_recording` (linhas ~1357-1369)

```python
# ANTES:
cmd_video = [
    'ffmpeg', '-y',
    '-framerate', str(self.recording_fps),
    '-i', os.path.join(self.mp4_temp_dir, 'frame_%06d.png'),
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '18',
    '-tune', 'animation',
    '-bf', '0',
    '-movflags', '+faststart',
    '-pix_fmt', 'yuv420p',
    temp_video
]

# DEPOIS:
cmd_video = [
    'ffmpeg', '-y',
    '-framerate', str(self.recording_fps),
    '-i', os.path.join(self.mp4_temp_dir, 'frame_%06d.png'),
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '12',
    '-tune', 'animation',
    '-g', '24',
    '-bf', '0',
    '-vsync', 'cfr',
    '-movflags', '+faststart',
    '-pix_fmt', 'yuv420p',
    temp_video
]
```

Mudancas:
- `-crf` de `18` para `12` (qualidade padrao do projeto)
- Adicionado `-g 24` (keyframe a cada 24 frames, obrigatorio)
- Adicionado `-vsync cfr` (constant frame rate, obrigatorio)

## Verificacao

1. Abrir calibrador com webcam
2. Clicar no botao de gravar (icone de record)
3. Gravar por 5-10 segundos
4. Parar gravacao
5. Verificar o MP4 gerado com: `ffprobe -i ~/Videos/webcam_ascii_*.mp4 -show_streams -loglevel error`
6. Verificar encoding com: `ffprobe -i ~/Videos/webcam_ascii_*.mp4 -show_entries stream=codec_name,profile,pix_fmt -loglevel error`
7. Confirmar: profile deve ser "High" (nao "High 4:4:4"), pix_fmt deve ser "yuv420p"
