#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark de Performance do Calibrador

Este script mede o tempo de cada componente do pipeline
de renderização para identificar gargalos.
"""

import sys
import os
import time
import gc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Resultados
results = {}

def measure(name, func, iterations=10):
    """Mede tempo médio de uma função."""
    gc.collect()
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # ms
    avg = sum(times) / len(times)
    results[name] = {'avg_ms': avg, 'min_ms': min(times), 'max_ms': max(times)}
    print(f"  {name}: {avg:.2f}ms (min: {min(times):.2f}, max: {max(times):.2f})")
    return avg

print("=" * 60)
print("BENCHMARK DE PERFORMANCE - CALIBRADOR")
print("=" * 60)

# Criar frame de teste
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_WIDTH = 120
TARGET_HEIGHT = 30

print(f"\nResolução fonte: {FRAME_WIDTH}x{FRAME_HEIGHT}")
print(f"Resolução target: {TARGET_WIDTH}x{TARGET_HEIGHT}")

# Frame de teste aleatório
test_frame = np.random.randint(0, 255, (FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
test_gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
test_mask = np.random.randint(0, 255, (FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)

print("\n--- 1. OPERAÇÕES OPENCV ---")
measure("cv2.cvtColor BGR→GRAY", lambda: cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY))
measure("cv2.cvtColor BGR→HSV", lambda: cv2.cvtColor(test_frame, cv2.COLOR_BGR2HSV))
measure("cv2.resize INTER_AREA", lambda: cv2.resize(test_frame, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_AREA))
measure("cv2.GaussianBlur 5x5", lambda: cv2.GaussianBlur(test_frame, (5, 5), 0))
measure("cv2.Sobel", lambda: cv2.Sobel(test_gray, cv2.CV_64F, 1, 0, ksize=3))
measure("cv2.morphologyEx", lambda: cv2.morphologyEx(test_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)))

print("\n--- 2. AUTO SEGMENTER (MediaPipe) ---")
try:
    from src.core.auto_segmenter import AutoSegmenter, is_available
    if is_available():
        segmenter = AutoSegmenter(use_gpu=True)
        # Warmup
        segmenter.process(test_frame)
        measure("AutoSegmenter.process (GPU)", lambda: segmenter.process(test_frame), iterations=5)
        segmenter.close()
        
        segmenter_cpu = AutoSegmenter(use_gpu=False)
        segmenter_cpu.process(test_frame)
        measure("AutoSegmenter.process (CPU)", lambda: segmenter_cpu.process(test_frame), iterations=5)
        segmenter_cpu.close()
    else:
        print("  AutoSegmenter não disponível")
except Exception as e:
    print(f"  AutoSegmenter erro: {e}")

print("\n--- 3. POST FX (CuPy) ---")
try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    config = PostFXConfig(bloom_enabled=True, chromatic_enabled=False, scanlines_enabled=False, glitch_enabled=False)
    postfx = PostFXProcessor(config, use_gpu=True)
    # Warmup
    postfx.process(test_frame)
    measure("PostFX.process (bloom only, GPU)", lambda: postfx.process(test_frame), iterations=5)
    
    postfx_cpu = PostFXProcessor(config, use_gpu=False)
    postfx_cpu.process(test_frame)
    measure("PostFX.process (bloom only, CPU)", lambda: postfx_cpu.process(test_frame), iterations=5)
except Exception as e:
    print(f"  PostFX erro: {e}")

print("\n--- 4. RENDERIZAÇÃO PIL ---")
resized = cv2.resize(test_frame, (TARGET_WIDTH, TARGET_HEIGHT))
resized_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

try:
    font = ImageFont.load_default()
except:
    font = None

def render_pil_ascii():
    """Simula renderização ASCII com PIL."""
    char_width, char_height = 10, 16
    img = Image.new('RGB', (TARGET_WIDTH * char_width, TARGET_HEIGHT * char_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    chars = "@%#*+=-:. "
    for y in range(TARGET_HEIGHT):
        for x in range(TARGET_WIDTH):
            brightness = resized_gray[y, x]
            char_idx = int(brightness / 256 * len(chars))
            char_idx = min(char_idx, len(chars) - 1)
            r, g, b = resized[y, x][::-1]  # BGR→RGB
            draw.text((x * char_width, y * char_height), chars[char_idx], fill=(r, g, b), font=font)
    return np.array(img)

measure("PIL ASCII render (loop Python)", render_pil_ascii, iterations=3)

print("\n--- 5. NUMPY→GDKPIXBUF SIMULADO ---")
def numpy_to_bytes():
    """Simula conversão para GdkPixbuf."""
    rgb = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
    return rgb.tobytes()

measure("numpy→bytes (para GdkPixbuf)", numpy_to_bytes)

print("\n--- 6. CUPY (se disponível) ---")
try:
    import cupy as cp
    test_gpu = cp.asarray(test_frame)
    
    def cupy_operations():
        result = cp.asarray(test_frame, dtype=cp.float32)
        result = result * 1.1
        result = cp.clip(result, 0, 255).astype(cp.uint8)
        return cp.asnumpy(result)
    
    # Warmup
    cupy_operations()
    cp.cuda.Stream.null.synchronize()
    
    measure("CuPy array ops + sync", cupy_operations, iterations=5)
    
    def cupy_free_all():
        mempool = cp.get_default_memory_pool()
        mempool.free_all_blocks()
    
    measure("CuPy free_all_blocks", cupy_free_all, iterations=5)
    
except Exception as e:
    print(f"  CuPy não disponível: {e}")

print("\n--- 7. GARBAGE COLLECTION ---")
measure("gc.collect()", lambda: gc.collect(), iterations=5)

print("\n" + "=" * 60)
print("RESUMO - TOP 5 GARGALOS")
print("=" * 60)

sorted_results = sorted(results.items(), key=lambda x: x[1]['avg_ms'], reverse=True)
for i, (name, data) in enumerate(sorted_results[:5], 1):
    print(f"{i}. {name}: {data['avg_ms']:.2f}ms")

print("\n" + "=" * 60)
print("RECOMENDAÇÕES")
print("=" * 60)

if 'AutoSegmenter.process (GPU)' in results:
    seg_time = results['AutoSegmenter.process (GPU)']['avg_ms']
    target_fps = 30
    max_time = 1000 / target_fps
    if seg_time > max_time * 0.5:
        print(f"⚠️  AutoSegmenter ({seg_time:.1f}ms) consome >{50}% do tempo para {target_fps}FPS")
        print("   → Considere: processar a cada N frames, reduzir resolução, ou usar CPU")

if 'PIL ASCII render (loop Python)' in results:
    pil_time = results['PIL ASCII render (loop Python)']['avg_ms']
    if pil_time > 30:
        print(f"⚠️  Renderização PIL ({pil_time:.1f}ms) é muito lenta")
        print("   → Considere: pré-cachear atlas de caracteres, usar cv2.putText, ou kernels GPU")

if 'CuPy free_all_blocks' in results:
    free_time = results['CuPy free_all_blocks']['avg_ms']
    if free_time > 5:
        print(f"⚠️  CuPy free_all_blocks ({free_time:.1f}ms) causa stall")
        print("   → Considere: chamar menos frequentemente ou em thread separada")

print("\nBenchmark concluído!")
