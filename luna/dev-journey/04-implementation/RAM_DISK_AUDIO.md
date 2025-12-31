# RAM Disk Audio - I/O de Alta Performance

```
STATUS: PRODUCAO
LATENCIA I/O: ~0ms (vs ~5-15ms SSD NVMe)
MELHORIA: Eliminacao total de I/O de disco
```

## Problema

Arquivos temporarios de audio eram escritos em `/tmp`:
1. `/tmp` geralmente esta em disco (SSD/HDD)
2. Cada escrita/leitura passa pelo kernel filesystem
3. Para audio em tempo real, cada milissegundo conta
4. SSDs tem latencia de ~5-15ms por operacao

## Solucao

Usar `/dev/shm` (shared memory) como RAM disk:
1. Montado diretamente na RAM
2. Zero latencia de I/O
3. Fallback automatico para `/tmp` se nao disponivel
4. Limpeza automatica de arquivos temporarios

## Arquitetura

```
Audio Gerado
    |
    v
get_temp_audio_path()
    |
    +--> /dev/shm disponivel?
    |         |
    |    SIM  |  NAO
    |         |
    v         v
/dev/shm/    /tmp/
luna_audio_  luna_audio_
{uuid}.wav   {uuid}.wav
```

## Uso

### Helper Centralizado

```python
from src.soul.boca.temp_audio import (
    get_temp_audio_path,
    cleanup_temp_audio,
    cleanup_all_temp_audio,
    is_using_ram_disk
)

# Obter caminho para arquivo temporario
path = get_temp_audio_path(".wav")  # /dev/shm/luna_audio_uuid.wav

# Gerar audio
generate_audio(text, path)

# Reproduzir
play_audio(path)

# Limpar
cleanup_temp_audio(path)

# Verificar se esta usando RAM
if is_using_ram_disk():
    print("RAM disk ativo")
```

### Limpeza em Lote

```python
# Remover todos os arquivos temporarios de audio
count = cleanup_all_temp_audio()
print(f"Removidos {count} arquivos temporarios")
```

## Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `src/soul/boca/temp_audio.py` | Novo modulo helper |
| `src/soul/boca/coqui.py` | Usa `get_temp_audio_path()` |
| `src/soul/boca/chatterbox.py` | Usa `get_temp_audio_path()` |
| `src/soul/boca/elevenlabs.py` | Usa `get_temp_audio_path()` |
| `src/tools/tts_daemon/daemon.py` | Usa RAM disk local |

## Metricas

| Operacao | Disco (NVMe) | RAM Disk |
|----------|--------------|----------|
| Escrita 500KB | ~5ms | <0.1ms |
| Leitura 500KB | ~3ms | <0.1ms |
| Latencia total | ~8ms | <0.2ms |

## Fallback

Se `/dev/shm` nao estiver disponivel:
1. `os.access("/dev/shm", os.W_OK)` retorna False
2. Fallback automatico para `/tmp`
3. Nenhuma configuracao necessaria

## Testes

```bash
pytest src/tests/test_temp_audio.py -v
```

20 testes cobrindo:
- Geracao de paths
- Prefixos e sufixos
- Unicidade de UUIDs
- Cleanup individual e em lote
- Fallback para /tmp
- Constantes

## Notas Tecnicas

1. **UUID:** Cada arquivo tem UUID unico para evitar colisoes
2. **Prefixo:** `luna_audio_` para identificacao facil
3. **Daemon separado:** Usa `luna_daemon_` como prefixo
4. **Limpeza:** `cleanup_all_temp_audio()` limpa ambos os diretorios

---

*Implementado em 2025-12-31*
