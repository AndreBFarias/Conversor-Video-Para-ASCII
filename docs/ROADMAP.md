# Roadmap - Extase em 4R73

## Sprints Concluídas ✅

### Sprint 1: Preview Automático
Preview só abre com duplo clique, solução elegante para webcam.

### Sprint 2: Sistema de Gravação
MP4 screencast com áudio, 30 FPS, popup com opções.

### Sprint 3: Fonte do Terminal
Detecção automática de fonte/tamanho, ComboBox de fontes.

### Sprint 4: Chroma Key por Vídeo
Calibração individual em batch, sincronização timestamp.

### Sprint 5: Remoção de Código Legacy
544 linhas removidas, calibrador CLI eliminado.

### Sprint 6: Performance Extrema (GPU Base)
`gpu_converter.py` com CUDA kernels, toggle GPU na interface.

### Sprint 7A: High Fidelity + Braille + Temporal
Modo textura MSE, Unicode Braille (4x resolução), anti-flicker.

---

## Sprints Futuras 🚀

### Sprint 7B: Async CUDA Streams
**Foco:** Otimização de pipeline GPU
**Ganho:** 15-20% FPS (30 → 35-40 fps)
**Tecnologias:** CuPy Streams, batch processing paralelo
**Duração:** 3-5 dias

### Sprint 8: Infraestrutura e Profissionalização
**Foco:** Preparar para release público
**Features:**
- Lazy imports (startup < 1s)
- Documentação Sphinx/MkDocs
- Sistema de issues GitHub
- Pacote .deb para Ubuntu/Debian
- Regra de anonimato (remover traços de IA)
- Reorganização de estrutura
**Duração:** 7-10 dias

### Sprint 9: Matrix Rain (Particle System GPU)
**Foco:** Chuva de caracteres interativa
**Features:**
- 5000-10000 partículas GPU
- Física: gravidade, rebote, colisão
- Interação com máscara chroma key
- Modos: Overlay, Replace, Blend
**Tecnologias:** CUDA RawKernel, particle physics
**Duração:** 5-7 dias

### Sprint 10: Pós-Processamento Cyberpunk
**Foco:** Bloom neon e glitch effects
**Features:**
- Bloom effect (brilho neon)
- Chromatic aberration (RGB shift)
- Scanlines CRT
- Distorção glitch
**Tecnologias:** Gaussian blur, blend modes
**Duração:** 4-6 dias

### Sprint 11: Neural ASCII (Style Transfer)
**Foco:** Estilizar vídeo antes de ASCII
**Features:**
- DoG/XDoG edge detection
- Style presets: Sketch, Comic, Oil, Pencil
- Mini CNN opcional (ONNX)
**Tecnologias:** cupyx.scipy.ndimage, ONNX Runtime
**Duração:** 5-7 dias

### Sprint 12: Optical Flow (Interpolação de Movimento)
**Foco:** Suavizar vídeos de baixo FPS
**Features:**
- 15 fps → 30/60 fps interpolation
- OpenCV CUDA Farneback
- Warping baseado em flow vectors
**Tecnologias:** cv2.cuda optical flow
**Duração:** 4-6 dias

### Sprint 13: Audio-Reactive ASCII
**Foco:** Caracteres reagem à música
**Features:**
- FFT na GPU (frequências bass/mids/treble)
- Modulação de brightness, intensity, color, bloom
- Visualizador de espectro
**Tecnologias:** PyAudio, CuPy FFT
**Duração:** 3-5 dias

### Sprint 14: Polimento Final e Release
**Foco:** Versão 1.0.0 pública
**Features:**
- Testes completos (pytest, coverage > 80%)
- Profiling e otimizações finais
- Documentação user manual
- GitHub release com .deb e AppImage
- Marketing: YouTube, Reddit, Hacker News
**Duração:** 7-10 dias

---

## Priorização Sugerida

### Caminho A: Infraestrutura Primeiro (Recomendado)
1. Sprint 8 (Infra)
2. Sprint 7B (Async)
3. Sprints 9-13 (Features visuais)
4. Sprint 14 (Release)

**Justificativa:** Estabelecer base sólida antes de adicionar features complexas.

### Caminho B: Features Visuais Primeiro
1. Sprint 7B (Async - quick win)
2. Sprint 9 (Matrix Rain - wow factor)
3. Sprint 10 (Cyberpunk - visual appeal)
4. Sprint 8 (Infra)
5. Sprints 11-13
6. Sprint 14 (Release)

**Justificativa:** Demonstrar valor visual rapidamente, infraestrutura depois.

---

## Tecnologias e Dependências

### Core
- Python 3.10+
- NumPy, OpenCV
- CuPy (CUDA 11.0+)
- GTK 3.0

### Sprint 7B
- CuPy CUDA Streams

### Sprint 8
- Sphinx / MkDocs
- pytest
- Debian packaging tools

### Sprint 9
- CUDA RawKernel (já usado)

### Sprint 10
- cupyx.scipy.ndimage (já disponível)

### Sprint 11
- ONNX Runtime (opcional)

### Sprint 12
- OpenCV com CUDA build

### Sprint 13
- PyAudio

---

## Performance Targets

| Hardware | Target FPS | Resolution | Features |
|----------|-----------|------------|----------|
| RTX 3050 | 60 FPS | 150x80 | Todas |
| RTX 3060 | 120 FPS | 200x100 | Todas |
| RTX 4090 | 240+ FPS | 300x150 | Todas |

**Memória GPU:**
- Baseline: ~500MB
- Full features: ~2GB (seguro para RTX 3050 com 8GB)

---

## Release Timeline

**Estimativa total:** 8-12 semanas

**Milestones:**
- v0.8.0 (Sprint 7B): Async otimizado
- v0.9.0 (Sprint 8): Infraestrutura profissional
- v0.10.0 (Sprint 9-10): Features visuais 1
- v0.11.0 (Sprint 11-12): Features visuais 2
- v0.12.0 (Sprint 13): Audio-reactive
- v1.0.0 (Sprint 14): Release público

---

## Próximos Passos

1. User escolhe caminho (A ou B)
2. Criar issues no GitHub para cada sprint
3. Iniciar primeira sprint
4. Manter Dev_log atualizado
5. Testes incrementais

---

**Última Atualização:** 2026-01-13
