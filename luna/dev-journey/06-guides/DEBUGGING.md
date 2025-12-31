# Guia de Debugging - Luna

**Data:** 2025-12-18

## TL;DR

Debug Luna usando logs em `src/logs/`, variavel de ambiente `DEBUG=1`, breakpoints com pdb, e Textual DevTools para TUI. Prioridade: logs > pdb > print (nunca use print).

## Contexto

Luna e um assistente IA com TUI em Textual e multiplas camadas de processamento. Debugging eficiente requer conhecimento de onde procurar: logs rotacionados, estado de conversacao, erros de API, e renderizacao TUI.

## Sistema de Logs

### Estrutura

```
src/logs/
├── luna.log          # Log principal rotacionado
├── luna.log.1        # Rotacao anterior
├── api.log           # Chamadas de API
└── debug.log         # Debug verbose (apenas quando DEBUG=1)
```

### Logs Principais

**luna.log:**
- Inicializacao do sistema
- Fluxo de conversacao
- Erros criticos
- Performance metrics

**api.log:**
- Requests enviados para API LLM
- Responses recebidos
- Rate limiting
- Timeouts

**debug.log:**
- Estado interno de objetos
- Cache hits/misses
- Thread lifecycle
- Memory snapshots

### Ler Logs em Tempo Real

```bash
tail -f src/logs/luna.log
tail -f src/logs/api.log | grep ERROR
tail -f src/logs/debug.log | grep "ConversationMemory"
```

### Filtrar Logs

```bash
grep "ERROR" src/logs/luna.log
grep "APIError" src/logs/api.log | tail -20
grep "timestamp.*2025-12-18" src/logs/luna.log
```

## Modo Debug

### Ativar Debug Verbose

```bash
export DEBUG=1
python main.py
```

Efeitos:
- Logs detalhados em `debug.log`
- Stack traces completos
- Estado de objetos logado
- Performance timing de cada operacao

### Desativar

```bash
unset DEBUG
```

## Debugging de Codigo Python

### 1. PDB (Python Debugger)

Adicione breakpoint no codigo:

```python
def process_message(message: str) -> str:
    import pdb; pdb.set_trace()

    result = transform(message)
    return result
```

Comandos uteis:
- `n` (next): proxima linha
- `s` (step): entra na funcao
- `c` (continue): continua ate proximo breakpoint
- `p variable`: imprime variavel
- `pp variable`: pretty-print variavel
- `l`: mostra contexto de codigo
- `q`: sair do debugger

### 2. Breakpoint Condicional

```python
def process_batch(items: list[dict]) -> None:
    for item in items:
        if item.get("id") == "problematic-id":
            import pdb; pdb.set_trace()
        process_item(item)
```

### 3. Logging ao Inves de Print

**ERRADO:**

```python
def fetch_data():
    data = api.get()
    print(f"Data: {data}")
    return data
```

**CERTO:**

```python
import logging
logger = logging.getLogger(__name__)

def fetch_data() -> dict:
    data = api.get()
    logger.debug(f"Dados obtidos da API: {data}")
    return data
```

## Debugging de TUI (Textual)

### Textual DevTools

Inicie com console separado:

```bash
textual console
```

Em outro terminal:

```bash
python main.py
```

DevTools mostra:
- Arvore de widgets em tempo real
- Eventos DOM
- CSS aplicado
- Performance de renderizacao

### Log no TUI

```python
from textual.app import App

class LunaApp(App):
    def on_mount(self) -> None:
        self.log("Aplicacao iniciada")
        self.log.debug(f"Estado inicial: {self.state}")
```

Logs aparecem no DevTools.

### Inspecionar Widget

```python
from textual import on

@on(Button.Pressed, "#submit-button")
def handle_submit(self, event: Button.Pressed) -> None:
    self.log(f"Botao pressionado: {event}")
    self.log(f"Estado do input: {self.query_one('#input-field').value}")
```

## Debugging de API

### Verificar Chamadas

```bash
grep "API Request" src/logs/api.log | tail -10
```

Exemplo de log:

```
2025-12-18 14:32:10 - API Request: messages.create(model=gemini-2.0-flash, max_tokens=4096)
2025-12-18 14:32:12 - API Response: 200 OK (2.1s, 1024 tokens)
```

### Simular Erro de API

```python
from unittest.mock import patch

@patch('src.core.api_client.LLMClient')
def test_api_error_handling(mock_client):
    mock_client.side_effect = Exception("API timeout")

    # Teste fluxo de erro
```

### Verificar Rate Limiting

```bash
grep "rate_limit" src/logs/api.log
```

## Debugging de Memoria

### Memory Profiler

```bash
pip install memory-profiler
```

Adicione decorator:

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(1000000)]
    return sum(large_list)
```

Execute:

```bash
python -m memory_profiler src/core/processor.py
```

### Verificar Vazamento

```python
import gc
import logging

logger = logging.getLogger(__name__)

def check_memory_leaks():
    gc.collect()
    objects = gc.get_objects()
    logger.debug(f"Total de objetos: {len(objects)}")

    for obj in gc.garbage:
        logger.warning(f"Objeto nao coletado: {type(obj)}")
```

## Debugging de Threading

### Log de Threads

```python
import threading
import logging

logger = logging.getLogger(__name__)

def worker_function():
    thread_name = threading.current_thread().name
    logger.debug(f"Thread {thread_name} iniciada")

    # Trabalho

    logger.debug(f"Thread {thread_name} finalizada")
```

### Deadlock Detection

```bash
export DEBUG=1
python main.py
```

Procure em `debug.log`:

```
Thread-1: Aguardando lock em ConversationMemory
Thread-2: Aguardando lock em ApiClient
```

## Ferramentas Uteis

### 1. IPython para Exploracao

```bash
pip install ipython
ipython
```

```python
from src.core.processor import DataProcessor
processor = DataProcessor()
processor?  # Mostra docstring
processor??  # Mostra codigo fonte
```

### 2. Py-Spy (Profiling sem Modificar Codigo)

```bash
pip install py-spy
py-spy top -- python main.py
```

Mostra funcoes mais chamadas em tempo real.

### 3. cProfile

```bash
python -m cProfile -o profile.stats main.py
```

Analise:

```python
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
```

## Debugging de Audio

### Microfone Nao Detecta Fala

**Sintomas:**
- VAD nunca detecta fala
- Logs mostram RMS sempre baixo
- Silencio constante mesmo falando

**Debug:**

```bash
# 1. Listar dispositivos
./venv/bin/python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'[{i}] {info[\"name\"]} (Rate: {int(info[\"defaultSampleRate\"])}Hz)')
p.terminate()
" 2>/dev/null

# 2. Testar captura
timeout 5 ./venv/bin/python -c "
import pyaudio, numpy as np
DEVICE_ID = 5  # ALTERE
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000,
                input=True, input_device_index=DEVICE_ID, frames_per_buffer=1024)
for _ in range(30):
    data = stream.read(1024, exception_on_overflow=False)
    rms = np.sqrt(np.mean(np.frombuffer(data, np.int16).astype(np.float64)**2))
    print(f'RMS: {rms:.0f}')
stream.close()
p.terminate()
" 2>/dev/null
```

**Solucoes Comuns:**

1. **Dispositivo errado**: Use hardware direto (hw:X,0) em vez de pulse
2. **Sample rate errado**: Use o rate nativo do microfone (48000Hz comum)
3. **Threshold alto demais**: Reduza VAD_ENERGY_THRESHOLD para 1500-2000

### Falsos Positivos no Inicio

**Sintomas:**
- Fala detectada imediatamente ao iniciar
- RMS muito alto nos primeiros segundos

**Causa:**
DC offset de inicializacao do microfone (capacitores carregando).

**Solucao:**
O codigo agora descarta os primeiros 50 frames automaticamente (warmup).
Verificar em `src/soul/audio_threads.py` linha 107.

### Erros ALSA no Log

**Mensagens tipicas:**
```
ALSA lib pcm_dsnoop.c:566:(snd_pcm_dsnoop_open) unable to open slave
```

**Causa:**
Erros normais do ALSA tentando dispositivos virtuais. Ignorar se audio funcionar.

---

## Problemas Comuns

### 1. "Import Error"

**Causa:** Modulo nao encontrado

**Debug:**

```bash
python -c "import sys; print('\n'.join(sys.path))"
```

**Solucao:**

```bash
export PYTHONPATH=/home/andrefarias/Desenvolvimento/Luna:$PYTHONPATH
```

### 2. "API Key Invalid"

**Debug:**

```bash
grep "API_KEY" src/logs/luna.log
```

**Verificar:**

```bash
python -c "from src.utils.config import load_config; print(load_config()['api']['key'][:10])"
```

### 3. "TUI Nao Renderiza"

**Debug:**

```bash
textual console
# Em outro terminal
DEBUG=1 python main.py
```

Verifique eventos DOM no console.

### 4. "Resposta Lenta da API"

**Debug:**

```bash
grep "API Response" src/logs/api.log | grep -oP '\(\d+\.\d+s'
```

Se > 5s consistentemente, verificar:
- Tamanho do contexto
- Rate limiting
- Conexao de rede

### 5. "Memory Leak"

**Debug:**

```python
import tracemalloc

tracemalloc.start()

# Execute operacao suspeita

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

## Debugging de Configuracao

### Verificar config.ini

```python
from src.utils.config import load_config

config = load_config()
print(f"Model: {config['api']['model']}")
print(f"Max Tokens: {config['api']['max_tokens']}")
```

### Validar Paths

```python
from pathlib import Path

log_dir = Path("src/logs")
print(f"Log dir existe: {log_dir.exists()}")
print(f"Arquivos: {list(log_dir.glob('*.log'))}")
```

## Checklist de Debugging

- [ ] Verificar logs em `src/logs/`
- [ ] Rodar com `DEBUG=1`
- [ ] Usar `pdb` em pontos criticos
- [ ] Verificar Textual DevTools (se TUI)
- [ ] Checar API logs para erros externos
- [ ] Profiling de memoria se suspeita de leak
- [ ] Validar configuracao em `config.ini`
- [ ] Testar modulos isoladamente

## Links Relacionados

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_STYLE.md](CODE_STYLE.md)
- [TESTING.md](TESTING.md)
- [Textual DevTools](https://textual.textualize.io/guide/devtools/)
- [Python PDB](https://docs.python.org/3/library/pdb.html)

---

**Licenca:** GPLv3
