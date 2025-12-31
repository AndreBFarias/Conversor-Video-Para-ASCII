# Luna - Modelos de IA

Estrutura centralizada de modelos locais para Luna.

## Estrutura

```
src/models/
├── echoes/              # Vozes de referencia (VERSIONADO)
│   ├── chatterbox/
│   │   └── luna_reference.wav
│   ├── coqui/
│   │   ├── luna_reference.wav
│   │   └── speaker_embedding.pt
│   ├── luna.py
│   └── README.md
│
├── whisper/             # Modelos STT (NAO VERSIONADO)
│   └── medium/          # ~1.5GB
│
├── embeddings/          # Sentence Transformers (NAO VERSIONADO)
│   └── paraphrase-multilingual-MiniLM-L12-v2/  # ~500MB
│
├── tts/                 # Cache Coqui XTTS (NAO VERSIONADO)
│   └── tts_models--multilingual--multi-dataset--xtts_v2/  # ~2GB
│
└── face/                # Modelos dlib (NAO VERSIONADO)
    └── dlib/            # ~100MB
```

## O que vai para o GitHub

- `echoes/` - Arquivos de referencia de voz (obrigatorio para TTS funcionar)

## O que NAO vai para o GitHub

- `whisper/` - Baixado automaticamente pelo install.sh
- `embeddings/` - Baixado automaticamente pelo install.sh
- `tts/` - Baixado automaticamente pelo install.sh
- `face/` - Baixado automaticamente pelo install.sh

## Instalacao

O `install.sh` configura as variaveis de ambiente para que os modelos sejam baixados nesta pasta:

```bash
# Whisper (faster-whisper)
export HF_HOME="src/models/whisper"

# Sentence Transformers
export SENTENCE_TRANSFORMERS_HOME="src/models/embeddings"

# Coqui TTS
export TTS_HOME="src/models/tts"
```

## Tamanho Total

| Modelo | Tamanho |
|--------|---------|
| Whisper medium | ~1.5GB |
| XTTS v2 | ~2.0GB |
| Embeddings | ~500MB |
| Face Recognition | ~100MB |
| **Total** | **~4.1GB** |

Mais os modelos Ollama:
| Modelo | Tamanho |
|--------|---------|
| llama3.2:3b | ~2.0GB |
| moondream | ~1.7GB |
| dolphin-mistral | ~4.1GB |
| **Total Ollama** | **~7.8GB** |

**Total Geral: ~12GB**
