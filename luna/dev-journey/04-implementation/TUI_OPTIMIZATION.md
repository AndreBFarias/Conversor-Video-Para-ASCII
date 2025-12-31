# TUI Optimization - Performance Visual

```
STATUS: PRODUCAO
FPS: 24 (vs ~60 sem throttle)
ECONOMIA CPU: ~10-15%
```

## Problema

O render loop do visualizador competia com processamento de audio:
1. Cada chunk de audio disparava um render
2. Audio chega a ~100Hz (cada 10ms)
3. Terminal nao percebe diferenca acima de 30fps
4. CPU desperdicada em renders inuteis

## Solucao

Rate limiting no `AudioVisualizer`:
1. `TARGET_FPS = 24` (configuravel via `VIZ_FPS`)
2. Skip renders se tempo < `MIN_FRAME_INTERVAL`
3. Libera CPU para processamento de audio

## Arquitetura

```
Audio Capture (100Hz)
    |
    v
update_audio()
    |
    +-- elapsed < MIN_FRAME_INTERVAL?
    |         |
    |    SIM  |  NAO
    |         |
    v         v
  SKIP     RENDER
```

## Configuracao

### Via .env

```bash
# FPS do visualizador (default: 24)
VIZ_FPS=24

# Valores recomendados:
# 24 = Suave, economico (RECOMENDADO)
# 30 = Mais fluido
# 15 = Ultra economico
```

### Via config.py

```python
UI_CONFIG = {
    "VIZ_FPS": 24,  # int(os.getenv("VIZ_FPS", "24"))
    ...
}
```

## Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `src/ui/audio_visualizer.py` | Rate limiting adicionado |
| `config.py` | `VIZ_FPS` adicionado a `UI_CONFIG` |
| `src/tests/test_audio_visualizer.py` | 7 novos testes |

## Metricas

| FPS | CPU Render | Diferenca Visual |
|-----|------------|------------------|
| 60 | ~15% | Baseline |
| 30 | ~8% | Imperceptivel |
| 24 | ~6% | Imperceptivel |
| 15 | ~4% | Leve stutter |

## Implementacao

```python
TARGET_FPS = config.UI_CONFIG.get("VIZ_FPS", 24)
MIN_FRAME_INTERVAL = 1.0 / TARGET_FPS

def update_audio(self, audio_chunk, rate):
    if self._busy:
        return

    current_time = time.time()
    elapsed = current_time - self.last_update
    if elapsed < MIN_FRAME_INTERVAL:
        return  # Skip render

    self._busy = True
    # ... render logic
```

## Testes

```bash
pytest src/tests/test_audio_visualizer.py -v
```

20 testes cobrindo:
- Constants e inicializacao
- Update audio
- Rate limiting (4 testes novos)
- Config (3 testes novos)

## Beneficios

1. **CPU livre**: 10-15% menos uso
2. **Audio smoother**: Menos competicao por CPU
3. **Bateria**: Menor consumo em laptops
4. **Configuravel**: Ajuste via env var

---

*Implementado em 2025-12-31*
