# Roadmap - Extase em 4R73

## Sprints Concluidas

### Sprint 1: Preview Automatico
Preview so abre com duplo clique, solucao elegante para webcam.

### Sprint 2: Sistema de Gravacao
MP4 screencast com audio, 30 FPS, popup com opcoes.

### Sprint 3: Fonte do Terminal
Deteccao automatica de fonte/tamanho, ComboBox de fontes.

### Sprint 4: Chroma Key por Video
Calibracao individual em batch, sincronizacao timestamp.

### Sprint 5: Remocao de Codigo Legacy
544 linhas removidas, calibrador CLI eliminado.

### Sprint 6: Performance Extrema (GPU Base)
`gpu_converter.py` com CUDA kernels, toggle GPU na interface.

### Sprint 7A: High Fidelity + Braille + Temporal
Modo textura MSE, Unicode Braille (4x resolucao), anti-flicker.

### Sprint 7B: Async CUDA Streams
`async_gpu_converter.py` com CuPy Streams, +15-20% FPS.

### Sprint 8: Infraestrutura e Profissionalizacao
- Pacote .deb funcional com postinst robusto
- Lazy loader para modulos pesados
- Documentacao Sphinx configurada
- Regra de anonimato aplicada

### Sprint 9: Matrix Rain (Particle System GPU)
`matrix_rain_gpu.py` com sistema de particulas, charsets Katakana/Binary.

### Sprint 10: Pos-Processamento Cyberpunk
`post_fx_gpu.py` com efeitos:
- Bloom (brilho neon com Gaussian blur)
- Chromatic Aberration (RGB shift)
- Scanlines CRT
- Glitch effect (distorcao aleatoria)

### Sprint 11: Neural ASCII (Style Transfer)
`style_transfer.py` com estilizacao pre-conversao:
- DoG/XDoG edge detection
- 6 presets: None, Sketch, Comic, Ink, Neon, Emboss
- Parametros: sigma, tau, edge_strength
- Integrado na toolbar do calibrador

### Sprint 12: Optical Flow (Interpolacao de Movimento)
`optical_flow.py` com interpolacao de frames:
- Farneback Optical Flow (CPU e GPU)
- 3 presets de qualidade: Fast, Medium, High
- Target FPS configuravel: 30, 60, 120
- Frame warping bidirecional com blending
- Integrado na toolbar do calibrador

### Sprint 13: Audio-Reactive ASCII
`audio_analyzer.py` com analise de audio em tempo real:
- FFT com CuPy (GPU) ou NumPy (CPU fallback)
- 3 bandas de frequencia: Bass (20-250Hz), Mids (250-4kHz), Treble (4k-16kHz)
- Smoothing exponencial para transicoes suaves
- Modulacao de efeitos PostFX: Bloom, Glitch, Chromatic
- Sensibilidade configuravel por banda
- Captura via PyAudio (loopback/mic)
- Integrado na Row 4 do calibrador

---

## Sprints Futuras

### Sprint 14: Polimento Final e Release
**Foco:** Versao 1.0.0 publica
**Features:**
- Testes completos (pytest, coverage > 80%)
- Profiling e otimizacoes finais
- Documentacao user manual
- GitHub release com .deb e AppImage
- Marketing: YouTube, Reddit, Hacker News
**Duracao:** 7-10 dias

---

## Performance Targets

| Hardware | Target FPS | Resolution | Features |
|----------|-----------|------------|----------|
| RTX 3050 | 60 FPS | 150x80 | Todas |
| RTX 3060 | 120 FPS | 200x100 | Todas |
| RTX 4090 | 240+ FPS | 300x150 | Todas |

**Memoria GPU:**
- Baseline: ~500MB
- Full features: ~2GB (seguro para RTX 3050 com 8GB)

---

## Proximos Passos

1. Testar Sprint 13 (Audio-Reactive) com musica
2. Iniciar Sprint 14 (Polimento Final e Release)
3. Criar issues no GitHub para cada sprint restante
4. Manter Dev_log atualizado

---

**Ultima Atualizacao:** 2026-01-14 (Sprint 13 concluida)
