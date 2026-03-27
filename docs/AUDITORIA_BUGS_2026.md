# Auditoria de Bugs e Inconsistencias - Extase em 4R73

**Data:** 2026-03-27
**Versao auditada:** 2.4.0
**Total de bugs encontrados:** 22
**Sprints propostas:** 8 (34-41)

## Resumo Executivo

O projeto cresceu organicamente com features adicionadas em sprints separadas sem atualizar todos os modulos consumidores. O resultado: calibrador, converters, player, GUI principal e CLI usam fallbacks diferentes para os mesmos parametros, gerando resultados divergentes.

## Indice de Bugs

| # | Descricao | Prioridade | Sprint |
|---|-----------|------------|--------|
| 01 | Calibrador nao inicia maximizado | CRITICA | 34 |
| 02 | Botao Salvar fecha o calibrador | CRITICA | 34 |
| 03 | QUALITY_PRESETS duplicado sem aspect ratio | ALTA | 36 |
| 04 | Limite largura 150 impede presets high/veryhigh | ALTA | 36 |
| 05 | render_mode fallback inconsistente | ALTA | 35 |
| 06 | temporal_threshold fallback divergente (10/20/50) | ALTA | 35 |
| 07 | sobel_threshold fallback divergente (10/20/70/100) | ALTA | 35 |
| 08 | char_aspect_ratio fallback divergente (0.48/0.95/1.0) | ALTA | 35 |
| 09 | target_height fallback divergente (0/22/44) | ALTA | 35 |
| 10 | Encoding FFmpeg errado no calibrador (CRF 18, sem -g 24) | MEDIA | 37 |
| 11 | luminance_ramp salva com pipe trailing | MEDIA | 36 |
| 12 | print() direto em vez de logging | BAIXA | 39 |
| 13 | realtime_ascii.py duplica funcoes de utils | BAIXA | 39 |
| 14 | png_converter.py duplica _load_postfx_config | BAIXA | 39 |
| 15 | Audio Reactive sobrescreve PostFX manual | MEDIA | 38 |
| 16 | PostFX defaults divergentes calibrador vs config.ini | ALTA | 35 |
| 17 | Combinacoes de features incompativeis nao tratadas | MEDIA | 38 |
| 18 | gpu_render_mode vs render_mode confusao | MEDIA | 40 |
| 19 | on_key_press duplicado (Space nao funciona) | CRITICA | 34 |
| 20 | "Restaurar Padroes" usa valores errados | ALTA | 35 |
| 21 | ChromaKey defaults divergentes | ALTA | 35 |
| 22 | target_width fallback divergente (120 vs 85) | ALTA | 35 |

## Ordem de Execucao das Sprints

```
Sprint 34 (Janela + Salvar + Space)  -- 0 dependencias, 3 bugs criticos
    |
Sprint 35 (Fallbacks unificados)     -- Base para tudo, 10 bugs
    |
    +-- Sprint 36 (Presets + Limites) -- Depende de 35, 3 bugs
    +-- Sprint 37 (Encoding)          -- Independente, 1 bug
    |
Sprint 38 (Audio+PostFX)             -- Depende de 35, 2 bugs
    |
Sprint 41 (Conflitos de features)    -- Depende de 35 + 38
    |
Sprint 39 (Duplicacao)               -- Independente, 3 bugs
    |
Sprint 40 (Sync GUI)                 -- Depende de 35 + 41, 1 bug
```

## Detalhes dos Sprints

- `docs/SPRINT_34_CALIBRADOR_JANELA_SALVAR.md` - Janela maximizada, botao salvar, tecla space
- `docs/SPRINT_35_UNIFICACAO_FALLBACKS.md` - Centralizar todos os defaults em defaults.py
- `docs/SPRINT_36_PRESETS_LIMITES_CONFIG.md` - Presets, limite de largura, pipe trailing
- `docs/SPRINT_37_ENCODING_FFMPEG_CALIBRADOR.md` - CRF 12, -g 24, -vsync cfr
- `docs/SPRINT_38_COMPATIBILIDADE_AUDIO_POSTFX.md` - Audio+PostFX, Braille+PixelArt
- `docs/SPRINT_39_ELIMINACAO_DUPLICACAO.md` - Remover duplicacoes, print->logger
- `docs/SPRINT_40_SINCRONIZACAO_GUI.md` - gpu_render_mode vs render_mode
- `docs/SPRINT_41_CONFLITOS_FEATURES.md` - Matriz de conflitos entre 11 features
