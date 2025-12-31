# Luna - Session Summary
**Data:** 2024-12-21
**Sessao:** Correcao de Audio e Documentacao

---

## Resumo Executivo

Investigacao e correcao de problema de microfone que impedia deteccao de fala. Descobertas importantes sobre configuracao de audio no Linux documentadas.

---

## Problema Identificado

1. **Dispositivo de audio incorreto**: `pulse` (ID 9) nao roteava audio corretamente
2. **Sample rate incompativel**: 44100Hz vs 48000Hz nativo do microfone
3. **VAD threshold muito alto**: 5000 para RMS real de ~150 em silencio
4. **Burst de inicializacao**: DC offset do microfone causava falsos positivos

---

## Solucao Implementada

### Configuracoes Corrigidas (.env)

| Configuracao | Antes | Depois | Motivo |
|--------------|-------|--------|--------|
| AUDIO_DEVICE_ID | 9 (pulse) | 5 (ALC287) | Hardware direto, menor latencia |
| AUDIO_SAMPLE_RATE | 44100 | 48000 | Rate nativo do microfone |
| VAD_ENERGY_THRESHOLD | 5000 | 2000 | Ajustado para RMS real |
| VISION_LOCAL_MODEL | (vazio) | moondream | Corrigido no QA |
| TTS_PROVIDER | (vazio) | local | Corrigido no QA |

### Codigo Modificado

**src/soul/audio_threads.py** - Warmup de inicializacao:
```python
# Linha 96-97: Variaveis de warmup
warmup_frames = 50
warmup_done = False

# Linha 107-111: Descarte de frames iniciais
if not warmup_done:
    if self._chunks_captured >= warmup_frames:
        warmup_done = True
        logger.info(f"[AUDIO_CAPTURE] Warmup concluido")
    continue
```

---

## Descobertas Tecnicas

### Hierarquia de Dispositivos de Audio no Linux

```
Hardware (ALSA) -> PulseAudio/PipeWire -> Aplicacao
    hw:X,0           pulse/pipewire
```

### Burst de Inicializacao do Microfone

O microfone tem um DC offset ao iniciar que gera RMS muito alto:

| Frame | RMS Tipico |
|-------|------------|
| 0-5 | 25000-30000 |
| 5-20 | 10000-20000 |
| 20-40 | 2000-5000 |
| 40+ | 100-300 (silencio real) |

### Comandos de Diagnostico

```bash
# Listar dispositivos de audio
./venv/bin/python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'[{i}] {info[\"name\"]} (Rate: {int(info[\"defaultSampleRate\"])}Hz)')
p.terminate()
" 2>/dev/null

# Testar captura de audio
timeout 5 ./venv/bin/python -c "
import pyaudio, numpy as np
DEVICE_ID = 5
SAMPLE_RATE = 48000
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                input=True, input_device_index=DEVICE_ID, frames_per_buffer=1024)
for _ in range(50):
    data = stream.read(1024, exception_on_overflow=False)
    rms = np.sqrt(np.mean(np.frombuffer(data, np.int16).astype(np.float64)**2))
    print(f'RMS: {rms:.0f}')
stream.close()
p.terminate()
" 2>/dev/null
```

---

## Arquivos Alterados

| Arquivo | Alteracao |
|---------|-----------|
| `.env` | Corrigido AUDIO_DEVICE_ID, AUDIO_SAMPLE_RATE, VAD_ENERGY_THRESHOLD |
| `.env.example` | Documentacao atualizada para configuracao de audio |
| `src/soul/audio_threads.py` | Adicionado warmup de 50 frames |
| `config.py` | Luna_piscando movido de EMOTION_MAP para ACTION_ANIMATIONS |
| `src/ui/reaction_suggester.py` | Removido Luna_piscando das emocoes |
| `install.sh` | Removidos modelos desnecessarios (tinyllama, gemma2:2b, phi3:mini) |

---

## Documentacao Criada

1. **dev-journey/06-guides/AUDIO_SETUP.md** (NOVO)
   - Diagnostico rapido de audio
   - Problemas comuns e solucoes
   - Arquitetura de audio
   - Configuracoes recomendadas por ambiente

---

## Modelos Ollama

### Removidos
- tinyllama (muito pequeno, JSON instavel)
- gemma2:2b (censura forte)

### Mantidos
- dolphin-mistral (chat principal)
- moondream (visao)
- llama3.2:3b (fallback)
- deepseek-coder:1.3b (codigo leve)
- qwen2.5-coder:3b (codigo equilibrado)

---

## Resultado do QA

```
Erros:  0
Avisos: 0

QA PASSOU
```

---

## Proximos Passos

1. Testar Luna completa com as novas configuracoes de audio
2. Considerar adicionar teste automatico de microfone no QA
3. Documentar configuracao para outros dispositivos de audio

---

**[QOL CHECKPOINT REACHED]**
