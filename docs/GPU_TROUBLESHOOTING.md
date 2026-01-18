# Guia de Troubleshooting de Memória GPU

Este guia ajuda a diagnosticar e resolver problemas relacionados a memória GPU e freezes do sistema.

## Diagnóstico Rápido

### Verificar Status da GPU

```bash
# Via nvidia-smi
nvidia-smi

# Via GPU Memory Manager (mais detalhado)
cd /path/to/Conversor-Video-Para-ASCII
source venv/bin/activate
python -c "from src.utils.gpu_memory_manager import get_memory_info; print(get_memory_info())"
```

Saída esperada:
```
{
  'device': 'NVIDIA GeForce RTX 3050 Laptop GPU',
  'mode': 'GPU',
  'total': '3.68GB',
  'used': '92.2MB',
  'free': '3.59GB',
  'usage_percent': '2.4%',
  'is_safe': True
}
```

---

## Problemas Comuns

### 1. `cupy.cuda.memory.OutOfMemoryError`

**Causa:** GPU sem memória suficiente para alocar buffers.

**Soluções:**
1. **Reduza a resolução** - Em `Qualidade`, selecione um preset menor (Mobile, Low)
2. **Desative efeitos** - Desabilite PostFX, Matrix Rain ou Auto Segmenter
3. **Feche outros programas** - Chrome, jogos, etc. consomem VRAM
4. **Force modo CPU:**
   ```ini
   # config.ini
   [Conversor]
   gpu_enabled = false
   ```

### 2. Freeze/Travamento do Sistema

**Causa:** Alocação excessiva de VRAM causando swap ou deadlock.

**Proteções Implementadas:**
- **GPU Memory Manager** monitora uso de VRAM em tempo real
- **Threshold de 80%** - inicia liberação de memória
- **Emergency cleanup a 95%** - libera tudo não essencial
- **Fallback para CPU** - automático quando memória baixa
- **Watchdog thread** - detecta operações travadas

**Se ainda travar:**
1. Reduza `target_width` em `config.ini`
2. Desative `gpu_async_enabled`
3. Use modo CPU

### 3. Fallback constante para CPU

**Causa:** GPU Memory Manager detectando memória insuficiente.

**Verificar:**
```bash
# Ver logs de memória
grep -i "fallback\|OOM\|memory" logs/system.log
```

**Soluções:**
1. Feche outras aplicações GPU
2. Aumente `memory_threshold` em `gpu_memory_manager.py` (padrão: 0.80)
3. Use GPU mais potente

---

## Configurações Avançadas

### Parâmetros do GPU Memory Manager

```python
# src/utils/gpu_memory_manager.py

# Limite de VRAM (80% do total por padrão)
self._memory_limit = int(total_mem * 0.80)

# Threshold para iniciar garbage collection (95%)
self._emergency_threshold = 0.95

# Timeout para operações GPU (segundos)
DEFAULT_TIMEOUT = 30.0

# Cooldown após OOM antes de tentar GPU novamente
_oom_cooldown = 30  # segundos
```

### Forçar GPU/CPU via Código

```python
from src.utils.gpu_memory_manager import gpu_manager

# Forçar modo CPU
gpu_manager.disable_gpu()

# Tentar reabilitar GPU
gpu_manager.enable_gpu()

# Verificar modo atual
mode = gpu_manager.get_compute_mode()  # "GPU" ou "CPU"
```

---

## Benchmarks

### Comparar Performance GPU vs CPU

```bash
source venv/bin/activate
python -c "
from src.utils.gpu_memory_manager import benchmark_gpu_vs_cpu
results = benchmark_gpu_vs_cpu(array_size=500000, iterations=10)
print(f'CPU: {results[\"cpu_time\"]*1000:.1f}ms')
print(f'GPU: {results[\"gpu_time\"]*1000:.1f}ms')
print(f'Speedup: {results[\"speedup\"]:.1f}x')
"
```

### Testes de Stress

```bash
python tests/stress/test_gpu_stress.py
```

---

## Logs Relevantes

| Mensagem | Significado |
|----------|-------------|
| `[GPUManager] Inicializado: ...` | GPU detectada corretamente |
| `[Calibrator] Modo CPU` | Usando processamento CPU |
| `[Calibrator] ⚠️ Ativando fallback CPU` | Memória baixa, mudando para CPU |
| `[GPUConverter] Recursos liberados` | Cleanup bem-sucedido |
| `[PostFX] Bloom GPU falhou, usando CPU` | Fallback de efeito |

---

## Requisitos de Hardware

### Mínimo
- **RAM:** 4GB
- **VRAM:** 2GB (ou modo CPU)
- **GPU:** NVIDIA GTX 900+ (ou AMD/Intel em modo CPU)

### Recomendado
- **RAM:** 8GB+
- **VRAM:** 4GB+
- **GPU:** NVIDIA RTX 2000+
- **CUDA:** 12.x

---

## Links Úteis

- [Documentação CuPy](https://docs.cupy.dev/en/stable/)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
- [MediaPipe GPU Delegate](https://developers.google.com/mediapipe/solutions/guide)
