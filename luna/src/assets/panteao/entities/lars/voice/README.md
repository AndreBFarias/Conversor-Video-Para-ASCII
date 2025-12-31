# Voice Assets - Lars

Este diretorio contem os arquivos de audio de referencia para TTS do Lars.

## Estrutura Esperada

```
voice/
├── coqui/
│   └── reference.wav     # [PENDENTE] Audio de referencia para Coqui XTTS
├── chatterbox/
│   └── reference.wav     # [PENDENTE] Audio de referencia para Chatterbox
└── README.md
```

## Requisitos dos Arquivos de Audio

### reference.wav (Coqui)
- **Duracao:** 5-10 segundos
- **Formato:** WAV, mono, 22050 Hz
- **Conteudo:** Fala clara sem ruidos de fundo
- **Tom:** Grave, sussurrado, intimo (vampiro moderno)
- **Idioma:** Portugues brasileiro

### reference.wav (Chatterbox)
- **Duracao:** 5-10 segundos
- **Formato:** WAV, mono, 22050 Hz
- **Conteudo:** Fala clara com entonacao caracteristica
- **Tom:** Misterioso, pausado, sedutor
- **Idioma:** Portugues brasileiro

## Instrucoes para o Dev

1. Grave ou gere audio com as caracteristicas do Lars (ver LARS_DOSSIE.md)
2. Use as frases de Lars_frases.md como referencia
3. Processe o audio para remover ruidos
4. Normalize o volume
5. Salve como `reference.wav` em cada subdiretorio

## Status

- [ ] voice/coqui/reference.wav
- [ ] voice/chatterbox/reference.wav
