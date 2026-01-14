import sys
import os
import time
import configparser
import logging

# Mock Config
config = configparser.ConfigParser(interpolation=None)
config.add_section('Conversor')
config.set('Conversor', 'target_width', '150')
config.set('Conversor', 'char_aspect_ratio', '0.5')
config.set('Conversor', 'sobel_threshold', '100')
config.set('Conversor', 'luminance_ramp', ' .:-=+*#%@')
config.add_section('ChromaKey')
config.set('ChromaKey', 'h_min', '35')
config.set('ChromaKey', 'h_max', '85')
config.set('ChromaKey', 's_min', '40')
config.set('ChromaKey', 's_max', '255')
config.set('ChromaKey', 'v_min', '40')
config.set('ChromaKey', 'v_max', '255')

video_path = '/home/andrefarias/Vídeos/Luna/Luna_observando.mp4'
output_dir = './benchmark_output'
os.makedirs(output_dir, exist_ok=True)

print("Starting GPU Benchmark...")
try:
    from src.core.gpu_converter import converter_video_para_mp4_gpu
    start = time.time()
    converter_video_para_mp4_gpu(video_path, output_dir, config)
    gpu_time = time.time() - start
    print(f"GPU Time: {gpu_time:.2f}s")
except Exception as e:
    print(f"GPU Failed: {e}")
    import traceback
    traceback.print_exc()

print("\nStarting CPU Benchmark...")
try:
    from src.core.mp4_converter import converter_video_para_mp4
    start = time.time()
    converter_video_para_mp4(video_path, output_dir, config)
    cpu_time = time.time() - start
    print(f"CPU Time: {cpu_time:.2f}s")
except Exception as e:
    print(f"CPU Failed: {e}")

if 'gpu_time' in locals() and 'cpu_time' in locals():
    print(f"\nSpeedup: {cpu_time / gpu_time:.2f}x")
