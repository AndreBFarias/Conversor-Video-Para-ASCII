#!/usr/bin/env python3
import os
import sys
import configparser
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.core.gpu_converter import converter_video_para_mp4_gpu

def test_sprint7a():
    print("=== TESTE SPRINT 7A: BRAILLE + TEMPORAL COHERENCE ===\n")

    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini', encoding='utf-8')

    print("Configuracoes Ativas:")
    print(f"  GPU Enabled: {config.get('Conversor', 'gpu_enabled')}")
    print(f"  GPU Render Mode: {config.get('Conversor', 'gpu_render_mode')}")
    print(f"  Braille Enabled: {config.get('Conversor', 'braille_enabled')}")
    print(f"  Braille Threshold: {config.get('Conversor', 'braille_threshold')}")
    print(f"  Temporal Coherence: {config.get('Conversor', 'temporal_coherence_enabled')}")
    print(f"  Temporal Threshold: {config.get('Conversor', 'temporal_threshold')}")
    print(f"  Target Resolution: {config.get('Conversor', 'target_width')}x{config.get('Conversor', 'target_height')}\n")

    input_videos = [
        os.path.join(config.get('Pastas', 'input_dir'), f)
        for f in os.listdir(config.get('Pastas', 'input_dir'))
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
    ]

    if not input_videos:
        print("ERRO: Nenhum video encontrado em", config.get('Pastas', 'input_dir'))
        return

    video_path = input_videos[0]
    output_dir = config.get('Pastas', 'output_dir')

    print(f"Testando com video: {os.path.basename(video_path)}\n")
    print("Iniciando conversao GPU com Braille + Temporal Coherence...\n")

    start = time.time()

    try:
        output_mp4 = converter_video_para_mp4_gpu(video_path, output_dir, config)
        elapsed = time.time() - start

        print(f"\n=== RESULTADO ===")
        print(f"Sucesso! Video criado em: {output_mp4}")
        print(f"Tempo total: {elapsed:.2f}s")
        print(f"\nPara reproduzir:")
        print(f"  mpv {output_mp4}")

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sprint7a()
