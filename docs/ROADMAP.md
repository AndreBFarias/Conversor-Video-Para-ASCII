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

### Sprint 14: Polimento Final e Release
**Concluido:** v2.3.0
- Suite pytest com 43 testes (97% cobertura)
- Motion Blur otimizado (downscale + frame skip)
- Manual do usuario completo (docs/USER_MANUAL.md)
- Pacote .deb funcional
- Documentacao Sphinx

### Sprint 15: Impacto Visual Real
**Concluido:** v2.3.0
- PostFX com valores visiveis (bloom_threshold 80, chromatic_shift 12)
- Audio Reactive com todas as modulacoes conectadas
- Style Transfer com presets intensificados
- Motion Blur baseado em Optical Flow
- Brightness e Color Shift como novos efeitos PostFX

---

## Sprints Futuras

### Sprint 16: Release Publico
**Foco:** Distribuicao e marketing
**Features:**
- AppImage para distribuicao universal
- GitHub release oficial
- Video demonstrativo
- Posts em comunidades (Reddit, Hacker News)

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

1. Criar AppImage para distribuicao universal
2. Preparar GitHub release (tag v2.3.0)
3. Video demonstrativo dos efeitos visuais
4. Divulgacao em comunidades

---

**Ultima Atualizacao:** 2026-01-14 (Sprint 15 concluida)
