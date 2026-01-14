#!/usr/bin/env python3

import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.converter import iniciar_conversao
import configparser

def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    input_dir = sys.argv[1] if len(sys.argv) > 1 else 'data_input'
    output_dir = 'data_output'

    os.makedirs(output_dir, exist_ok=True)

    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.webm')
    videos = []
    for ext in video_extensions:
        videos.extend(glob.glob(os.path.join(input_dir, f'*{ext}')))

    if not videos:
        print(f"Nenhum video encontrado em {input_dir}")
        sys.exit(1)

    print(f"Encontrados {len(videos)} videos para converter")

    for i, video_path in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] Convertendo: {os.path.basename(video_path)}")
        try:
            iniciar_conversao(video_path, output_dir, config)
            print("OK")
        except Exception as e:
            print(f"ERRO: {e}")
            continue

    print(f"\nBatch completo! {len(videos)} videos processados")

if __name__ == '__main__':
    main()
