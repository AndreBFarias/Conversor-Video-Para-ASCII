# TTS Daemon - Sintese de Voz Otimizada

```
STATUS: PRODUCAO
LATENCIA: ~0.7s (vs ~3s sem daemon)
MELHORIA: 4x mais rapido
```

## Problema

O sistema original de TTS usava subprocess para cada frase:
1. Spawn novo processo Python
2. Carregar PyTorch (~1s)
3. Carregar modelo TTS (~2s)
4. Gerar audio (~0.5s)
5. Matar processo

**Total: ~3-4 segundos por frase**

## Solucao

O TTS Daemon mantem o modelo carregado na GPU:
1. Inicia uma vez
2. Carrega modelo na VRAM
3. Escuta requisicoes via Unix socket
4. Gera audio instantaneamente

**Total: ~0.7 segundos por frase**

## Arquitetura

```
run_luna.sh
    |
    v
scripts/tts_daemon.sh ensure
    |
    v
/tmp/luna_tts_daemon.sock <--- Unix Socket
    ^
    |
src/soul/boca/core.py --> gerar_via_daemon()
```

## Uso

### Iniciar Manualmente

```bash
./scripts/tts_daemon.sh start
./scripts/tts_daemon.sh status
./scripts/tts_daemon.sh stop
./scripts/tts_daemon.sh restart
./scripts/tts_daemon.sh logs
```

### Automatico (Recomendado)

O `run_luna.sh` inicia o daemon automaticamente:

```bash
./run_luna.sh          # Inicia daemon + Luna
./run_luna.sh --no-daemon  # Sem daemon (subprocess lento)
```

## Configuracao

### Engine TTS

Definido em `.env`:
```bash
TTS_ENGINE=coqui     # Coqui XTTS v2
TTS_ENGINE=chatterbox  # Chatterbox (alternativo)
```

### Reference Audio

O daemon usa o audio de referencia da entidade ativa:
```
src/assets/panteao/entities/{entity}/voice/{engine}/reference.wav
```

## Fallback

Se o daemon nao estiver disponivel:
1. `check_daemon()` em `engine_check.py` verifica socket
2. Se falhar, `daemon_disponivel = False`
3. `_falar_interno()` usa subprocess como fallback

## Arquivos

```
scripts/tts_daemon.sh          # Gerenciador do daemon
src/tools/tts_daemon/
    __init__.py
    __main__.py               # Entry point
    cli.py                    # Argumentos e controle
    daemon.py                 # TTSDaemon class
    constants.py              # Paths e defaults
src/soul/boca/
    daemon.py                 # Cliente (gerar_via_daemon)
    engine_check.py           # check_daemon()
    core.py                   # _falar_interno() prioriza daemon
```

## Requisitos

```bash
# venv_tts separado
python -m venv venv_tts
./venv_tts/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
./venv_tts/bin/pip install -r requirements_tts.txt
```

## Metricas

| Metodo | Latencia | VRAM |
|--------|----------|------|
| Daemon (Coqui) | ~0.7s | ~2GB |
| Daemon (Chatterbox) | ~0.5s | ~3GB |
| Subprocess | ~3-4s | 0 (carrega/descarrega) |

## RAM Disk (I/O Otimizado)

O daemon usa `/dev/shm` (RAM) ao inves de `/tmp` (disco):
- Latencia I/O: <0.1ms vs ~5-15ms
- Fallback automatico para `/tmp` se RAM disk nao disponivel
- Ver: [RAM_DISK_AUDIO.md](./RAM_DISK_AUDIO.md)

## Troubleshooting

### Daemon nao inicia

```bash
cat /tmp/luna_tts_daemon.log
```

### Erro weights_only

PyTorch 2.6+ mudou o default. O daemon ja tem patch incluido.

### Modelo nao encontrado

```bash
# Baixar modelo manualmente
./venv_tts/bin/python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
```

---

*Implementado em 2025-12-31*
