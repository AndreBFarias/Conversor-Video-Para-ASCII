# Sprint 39: Eliminacao de Duplicacao de Codigo

**Prioridade:** BAIXA
**Resolve:** BUG-12, BUG-13, BUG-14
**Dependencia:** Nenhuma

## Objetivo

Remover funcoes duplicadas e substituir print() por logging em todos os converters.

## Tarefas

### 39.1 - Remover funcoes duplicadas em realtime_ascii.py

**Arquivo:** `src/core/realtime_ascii.py`

1. REMOVER funcao `sharpen_frame` (linhas ~40-47)
2. REMOVER funcao `rgb_to_ansi256` (linhas ~50-60)
3. ADICIONAR imports no topo do arquivo (apos os imports existentes):
```python
from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame
```

ATENCAO: O `rgb_to_truecolor` (linha ~63) eh UNICO deste arquivo, NAO remover.

### 39.2 - Remover _load_postfx_config duplicada em png_converter.py

**Arquivo:** `src/core/png_converter.py`

1. REMOVER funcao `_load_postfx_config` (linhas ~30-47)
2. REMOVER imports locais de PostFXProcessor/PostFXConfig (linhas ~18-21)
3. ADICIONAR import do loader:
```python
from src.core.utils.postfx_loader import load_postfx_config, POSTFX_AVAILABLE
if POSTFX_AVAILABLE:
    from src.core.post_fx_gpu import PostFXProcessor
```
4. Nas funcoes que usam `_load_postfx_config(config)`, trocar por `load_postfx_config(config)`

### 39.3 - Substituir print() por logging nos converters

Em CADA arquivo abaixo:
- `src/core/converter.py`
- `src/core/mp4_converter.py`
- `src/core/gpu_converter.py`
- `src/core/gif_converter.py`
- `src/core/png_converter.py`
- `src/core/gtk_calibrator.py`
- `src/core/realtime_ascii.py`

Adicionar no topo:
```python
import logging
logger = logging.getLogger(__name__)
```

Substituir:
- `print(f"...")` -> `logger.info(f"...")`
- `print(f"Aviso: ...")` -> `logger.warning(f"...")`
- `print(f"[ERRO] ...")` -> `logger.error(f"...")`
- `print(f"[DEBUG] ...")` -> `logger.debug(f"...")`

EXCECAO: Manter `print()` em blocos `if __name__ == "__main__"` (execucao direta via CLI).

## Verificacao

1. `python -c "from src.core.realtime_ascii import frame_para_ascii_rt"` - sem erro de import
2. `python -c "from src.core.png_converter import converter_imagem_para_png"` - sem erro
3. `pytest tests/` - todos os testes passando
4. `python cli.py validate` - todos os checks passando
