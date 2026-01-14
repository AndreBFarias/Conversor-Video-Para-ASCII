#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.converter import iniciar_conversao
import configparser

def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    video_path = sys.argv[1] if len(sys.argv) > 1 else 'data_input/sample.mp4'
    output_dir = 'data_output'

    if not os.path.exists(video_path):
        print(f"Erro: Video {video_path} não encontrado")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Convertendo: {video_path}")
    print(f"Saida em: {output_dir}")

    iniciar_conversao(video_path, output_dir, config)

    print("Conversao concluida!")

if __name__ == '__main__':
    main()
