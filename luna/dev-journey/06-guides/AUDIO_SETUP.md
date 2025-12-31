# Guia de Configuracao de Audio - Luna

**Data:** 2025-12-21
**Versao:** 1.0

---

## TL;DR

Microfone nao funciona? Use o dispositivo de hardware direto (hw:X,0), sample rate nativo (48000Hz), e ajuste VAD_ENERGY_THRESHOLD para seu ambiente. O sistema descarta os primeiros 50 frames para evitar falsos positivos.

---

## Diagnostico Rapido

### 1. Listar Dispositivos

```bash
./venv/bin/python -c "
import pyaudio
p = pyaudio.PyAudio()
print('Dispositivos de entrada:')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  [{i}] {info[\"name\"]} (Rate: {int(info[\"defaultSampleRate\"])}Hz)')
p.terminate()
" 2>/dev/null
```

### 2. Testar Captura

```bash
timeout 5 ./venv/bin/python -c "
import pyaudio
import numpy as np

DEVICE_ID = 5  # ALTERE PARA SEU DISPOSITIVO
SAMPLE_RATE = 48000

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                input=True, input_device_index=DEVICE_ID, frames_per_buffer=1024)

print('Fale algo...')
for i in range(50):
    data = stream.read(1024, exception_on_overflow=False)
    rms = np.sqrt(np.mean(np.frombuffer(data, np.int16).astype(np.float64)**2))
    bar = '#' * int(min(rms/100, 50))
    print(f'RMS: {rms:6.0f} |{bar}')

stream.close()
p.terminate()
" 2>/dev/null
```

---

## Problemas Comuns

### 1. Microfone Nao Detecta Fala

**Sintomas:**
- VAD nunca detecta fala
- RMS sempre baixo mesmo falando
- Silencio constante nos logs

**Causa Provavel:**
- Dispositivo de audio incorreto (pulse/pipewire vs hardware)
- Sample rate incompativel
- VAD threshold muito alto

**Solucao:**

```bash
# .env
AUDIO_DEVICE_ID=5           # Use hw:X,0 direto, nao pulse
AUDIO_SAMPLE_RATE=48000     # Rate nativo do microfone
VAD_ENERGY_THRESHOLD=2000   # Ajuste conforme seu ambiente
```

### 2. Falsos Positivos no Inicio

**Sintomas:**
- Fala detectada imediatamente apos iniciar
- RMS muito alto nos primeiros segundos
- Burst de audio no inicio

**Causa:**
- DC offset de inicializacao do microfone
- Capacitores carregando no hardware de audio

**Solucao:**
O codigo em `audio_threads.py` agora descarta os primeiros 50 frames automaticamente (warmup period).

### 3. Ruido Ambiente Dispara VAD

**Sintomas:**
- Fala detectada sem ninguem falando
- Ventoinha, ar condicionado ou teclado disparam deteccao

**Solucao:**

```bash
# .env - Aumente o threshold
VAD_ENERGY_THRESHOLD=3000   # Valores tipicos: 2000-4000
```

### 4. Erros ALSA no Log

**Mensagens tipicas:**
```
ALSA lib pcm_dsnoop.c:566:(snd_pcm_dsnoop_open) unable to open slave
ALSA lib pcm.c:2666:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
```

**Causa:**
Erros normais do ALSA tentando abrir dispositivos virtuais. Podem ser ignorados se o audio funcionar.

**Solucao:**
Redirecione stderr se incomodar:
```bash
./venv/bin/python main.py 2>/dev/null
```

---

## Arquitetura de Audio

### Fluxo de Dados

```
[Microfone] -> [PyAudio Stream] -> [AudioCaptureThread]
                                          |
                                          | (warmup: descarta 50 frames)
                                          v
                                   [audio_queue]
                                          |
                                          v
                              [TranscriptionThread]
                                          |
                                          | (VAD: energy + webrtc)
                                          v
                              [Whisper STT] -> [transcription_queue]
```

### Warmup Period

O microfone tem um burst de inicializacao (DC offset) que causa RMS muito alto nos primeiros frames:

| Frame | RMS Tipico |
|-------|------------|
| 0-5 | 25000-30000 |
| 5-20 | 10000-20000 |
| 20-40 | 2000-5000 |
| 40+ | 100-300 (silencio) |

Por isso, os primeiros 50 frames sao descartados antes de iniciar deteccao de fala.

### VAD (Voice Activity Detection)

Duas estrategias combinadas:

1. **Energy-based:** RMS > threshold
2. **WebRTC VAD:** Modelo neural para detectar fala

Ambas devem concordar (OR logic) para detectar fala.

---

## Configuracoes Recomendadas

### Hardware Tipico (Notebook com Microfone Integrado)

```bash
# .env
AUDIO_SAMPLE_RATE=48000
AUDIO_DEVICE_ID=5           # Ajuste para seu hw:X,0
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1024

VAD_ENERGY_THRESHOLD=2000
VAD_SILENCE_DURATION=1.2
VAD_MODE=3
VAD_FRAME_BUFFER_SIZE=6
VAD_SILENCE_FRAME_LIMIT=12
VAD_MIN_SPEECH_CHUNKS=3
```

### Ambiente Silencioso (Estudio)

```bash
VAD_ENERGY_THRESHOLD=1500   # Mais sensivel
VAD_SILENCE_DURATION=1.0    # Resposta mais rapida
```

### Ambiente Ruidoso (Escritorio)

```bash
VAD_ENERGY_THRESHOLD=4000   # Menos sensivel
VAD_SILENCE_DURATION=1.5    # Mais tolerante
VAD_MIN_SPEECH_CHUNKS=5     # Mais confirmacao
```

---

## Dispositivos de Audio no Linux

### Hierarquia

```
Hardware (ALSA) -> PulseAudio/PipeWire -> Aplicacao
    hw:X,0           pulse/pipewire
```

### Qual Usar?

| Tipo | Exemplo | Quando Usar |
|------|---------|-------------|
| Hardware | `hw:2,0`, `ALC287` | Recomendado, menor latencia |
| PulseAudio | `pulse` | Se hardware nao funcionar |
| PipeWire | `pipewire` | Sistemas modernos |
| Default | `default` | Fallback automatico |

### Identificar Hardware

```bash
arecord -l
```

Saida tipica:
```
card 2: Generic [HD-Audio Generic], device 0: ALC287 Analog [ALC287 Analog]
```

Neste caso, use `AUDIO_DEVICE_ID` correspondente ao dispositivo PyAudio com nome similar.

---

## Troubleshooting Avancado

### Log de Audio em Tempo Real

```bash
# Em um terminal, rode Luna
./venv/bin/python main.py

# Em outro terminal, monitore logs
tail -f src/logs/templo_de_luna.log | grep -E "(AUDIO|VAD|WHISPER)"
```

### Testar Whisper Isoladamente

```bash
./venv/bin/python -c "
from faster_whisper import WhisperModel
model = WhisperModel('medium', device='cuda', compute_type='float16')
print('Whisper carregado com sucesso')
"
```

### Verificar CUDA para Audio

```bash
./venv/bin/python -c "
import torch
print(f'CUDA disponivel: {torch.cuda.is_available()}')
print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')
"
```

---

## Alteracoes no Codigo

### audio_threads.py - Warmup

```python
# Linha 96-97: Variaveis de warmup
warmup_frames = 50
warmup_done = False

# Linha 107-111: Descarte de frames iniciais
if not warmup_done:
    if self._chunks_captured >= warmup_frames:
        warmup_done = True
        logger.info(f"[AUDIO_CAPTURE] Warmup concluido ({warmup_frames} frames descartados)")
    continue
```

---

## Links Relacionados

- [DEBUGGING.md](DEBUGGING.md)
- [CURRENT_STATUS.md](../04-implementation/CURRENT_STATUS.md)
- [ARCHITECTURE_THREADING.md](../04-implementation/ARCHITECTURE_THREADING.md)

---

**Licenca:** GPLv3
