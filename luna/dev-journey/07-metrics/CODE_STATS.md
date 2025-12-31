# Estatisticas de Codigo

> **TL;DR:** Analise detalhada do codigo fonte do projeto Luna.

## Contexto

Este documento apresenta estatisticas detalhadas sobre a base de codigo, incluindo complexidade, distribuicao e qualidade.

## Distribuicao por Tipo de Arquivo

| Tipo | Quantidade | Linhas |
|------|------------|--------|
| Python (.py) | 51 | ~10.700 |
| CSS (.tcss) | 1 | ~200 |
| Markdown (.md) | 15+ | ~2.000 |
| Shell (.sh) | 3 | ~500 |
| Config (.env, .ini) | 2 | ~150 |

## Maiores Arquivos

Os arquivos com mais linhas de codigo:

1. `main.py` - ~975 linhas (Orquestrador principal)
2. `src/soul/consciencia.py` - ~400 linhas (Integracao Gemini)
3. `src/soul/visao.py` - ~450 linhas (Visao computacional)
4. `src/ui/banner.py` - ~400 linhas (Banner com glitch)
5. `src/soul/audio_threads.py` - ~350 linhas (Threading audio)

## Modulos por Responsabilidade

### Core (src/soul/) - ~4.500 linhas
- consciencia.py: Processamento de linguagem
- boca.py: Text-to-Speech
- visao.py: Visao computacional
- ouvido.py: Captura de audio
- metricas.py: Sistema de metricas
- threading_manager.py: Gerenciamento de threads
- audio_threads.py: Threads de audio
- processing_threads.py: Threads de processamento

### UI (src/ui/) - ~2.300 linhas
- banner.py: Banner ASCII com efeitos
- widgets.py: Componentes customizados
- dashboard.py: Dashboard lateral
- status_decrypt.py: Widget de status com decrypt
- glitch_button.py: Botao com efeito glitch

### Core Logic (src/core/) - ~550 linhas
- animation.py: Controlador de animacoes
- session.py: Gerenciamento de sessoes

### Memory (src/data_memory/) - ~350 linhas
- memory_manager.py: RAG e embeddings
- memoria.py: Reconhecimento facial

## TODO

- [ ] Adicionar metricas de complexidade ciclomatica
- [ ] Calcular cobertura de testes
- [ ] Medir tempo medio de resposta

---
*Ultima atualizacao: 2025-12-18*
