# Guia Rapido: Sistema de Ambientes Isolados

## O que foi implementado

Seu projeto Luna agora tem **dois ambientes virtuais completamente isolados**:

1. **`venv/`** - Luna Core (dependências modernas)
2. **`venv_tts/`** - TTS System (dependências legacy travadas)

Isso resolve o conflito entre:
- `transformers` moderna (sem `BeamSearchScorer`)
- `transformers==4.36.2` (com `BeamSearchScorer` que o coqui-tts precisa)

---

## Proximos Passos (FACA AGORA)

### 1. Corrigir o venv_tts

O ambiente TTS existente tem a versão errada do transformers. Execute:

```bash
cd ~/Desenvolvimento/Luna
./fix_venv_tts.sh
```

Isso vai:
- Remover o `venv_tts` antigo
- Criar novo venv_tts
- Instalar `transformers==4.36.2` (com BeamSearchScorer)
- Verificar que tudo está correto

**Tempo estimado**: 5-10 minutos (download de pacotes)

---

### 2. Testar o TTS Isolado

Depois do fix, teste se está funcionando:

```bash
source venv/bin/activate
python test_tts_isolado.py
```

Voce deve ver:

```
============================================================
TESTE: Sistema de Voz Luna com TTS Isolado
============================================================

[1/3] Inicializando sistema de voz...
[OK] Sistema de voz inicializado

[2/3] Verificando disponibilidade do Coqui TTS...
[OK] Coqui TTS disponivel

[3/3] Testando geracao de audio...
[OK] Audio gerado com sucesso!
  - Engine: coqui-tts
  - Arquivo: .../luna_tts_xxxxx.wav
  - Tempo: 15.43s
```

---

### 3. Verificar Ambientes (Opcional)

Para ver o status completo dos ambientes a qualquer momento:

```bash
./verificar_ambientes.sh
```

---

## Estrutura de Arquivos Atualizada

```
Luna/
├── venv/                          # Ambiente principal (Luna Core)
│   └── lib/python3.10/site-packages/
│       ├── textual
│       ├── openai
│       ├── google-generativeai
│       └── transformers (moderna, >=4.40)
│
├── venv_tts/                      # Ambiente TTS isolado
│   └── lib/python3.10/site-packages/
│       ├── TTS (coqui-tts)
│       ├── torch==2.5.1
│       └── transformers==4.36.2   # ← COM BeamSearchScorer!
│
├── tts_wrapper.py                 # Interface de chamada do TTS
├── requirements.txt               # Deps Luna Core
├── requirements_tts.txt           # Deps TTS (TRAVADAS)
│
├── install.sh                     # Cria AMBOS os venvs
├── uninstall.sh                   # Remove AMBOS os venvs
├── run_luna.sh                    # Inicia Luna (usa venv/)
│
├── fix_venv_tts.sh               # [NOVO] Reinstala venv_tts
├── verificar_ambientes.sh         # [NOVO] Verifica status
└── test_tts_isolado.py           # [NOVO] Testa TTS
```

---

## Como Funciona

### Antes (Conflito)

```
venv/
  ├── transformers==4.57.3  (sem BeamSearchScorer)
  └── TTS  ← ERRO ao importar BeamSearchScorer!
```

### Depois (Isolado)

```
venv/                              venv_tts/
  ├── textual                        ├── TTS
  ├── openai                         ├── transformers==4.36.2
  └── transformers (moderna)         └── BeamSearchScorer [OK]

Luna Core ──────────────> subprocess ──────────> TTS Engine
                            ↓
                    venv_tts/bin/python tts_wrapper.py
```

---

## Fluxo de Uso Diario

### Instalacao Fresh (primeira vez ou apos clean)

```bash
./install.sh
./fix_venv_tts.sh  # Garante versões corretas
```

### Executar Luna

```bash
./run_luna.sh
```

Luna vai automaticamente:
1. Tentar gerar TTS via `venv_tts/bin/python tts_wrapper.py`
2. Se falhar, usar Chatterbox (se disponível)
3. Se falhar, usar ElevenLabs (se API key configurada)

### Desinstalar

```bash
./uninstall.sh  # Remove TUDO (venv + venv_tts + arquivos de app)
```

---

## Troubleshooting

### "ERROR: cannot import name 'BeamSearchScorer'"

Execute:
```bash
./fix_venv_tts.sh
```

### "venv_tts Python not found"

Execute:
```bash
./install.sh
```

### TTS muito lento

Normal! A primeira geração carrega o modelo (15-30s). Gerações seguintes são mais rápidas.

### Quero usar Chatterbox em vez de Coqui

Edite `src/soul/voice_system.py` linha ~337, mude a ordem em `synthesize()`:

```python
# Trocar de:
audio_path = self._generate_coqui_tts(text, emotion)
# ...
audio_path = self._generate_chatterbox(text, emotion)

# Para:
audio_path = self._generate_chatterbox(text, emotion)
# ...
audio_path = self._generate_coqui_tts(text, emotion)
```

---

## Beneficios

- **Automatico**: `install.sh` cria tudo
- **Isolado**: Zero conflitos de dependencia
- **Flexivel**: Fallback para multiplos engines
- **Testavel**: Scripts de verificacao prontos
- **Manutenivel**: Versoes travadas no `requirements_tts.txt`

---

## Arquivos Modificados

- `requirements.txt` - Adicionado google-generativeai, audio libs
- `requirements_tts.txt` - Versoes travadas + todas deps do coqui-tts
- `src/soul/voice_system.py` - Nova classe `CoquiTTSEngine` + integracao
- `uninstall.sh` - Remove ambos os venvs

## Arquivos Novos

- `fix_venv_tts.sh` - Reinstala venv_tts com versoes corretas
- `verificar_ambientes.sh` - Mostra status completo
- `test_tts_isolado.py` - Testa geracao de TTS

---

## Proximos Passos

1. Execute `./fix_venv_tts.sh`
2. Teste com `python test_tts_isolado.py`
3. Se tudo OK, use Luna normalmente com `./run_luna.sh`

Nunca mais vai passar por conflitos de dependencia do TTS.
