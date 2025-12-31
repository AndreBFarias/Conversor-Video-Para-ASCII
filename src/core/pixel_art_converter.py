#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import os
import sys
import numpy as np
import configparser
import argparse
from sklearn.cluster import KMeans

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement

COLOR_SEPARATOR = "§"


def quantize_colors(image, n_colors=16, use_fixed_palette=False):
    if use_fixed_palette:
        palette = np.array([
            [0, 0, 0], [255, 255, 255], [255, 0, 0], [0, 255, 0],
            [0, 0, 255], [255, 255, 0], [255, 0, 255], [0, 255, 255],
            [128, 0, 0], [0, 128, 0], [0, 0, 128], [128, 128, 128],
            [192, 192, 192], [128, 128, 0], [128, 0, 128], [0, 128, 128],
        ], dtype=np.uint8)
        palette = palette[:n_colors]
    else:
        h, w, c = image.shape
        pixels = image.reshape((-1, 3)).astype(np.float32)
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        palette = kmeans.cluster_centers_.astype(np.uint8)

    h, w, c = image.shape
    pixels = image.reshape((-1, 3))
    quantized = np.zeros_like(pixels)

    for i, pixel in enumerate(pixels):
        distances = np.linalg.norm(palette - pixel, axis=1)
        nearest_color_idx = np.argmin(distances)
        quantized[i] = palette[nearest_color_idx]

    return quantized.reshape((h, w, c))


def converter_frame_para_pixelart(frame, mask, pixel_size, n_colors, use_fixed_palette):
    h, w = frame.shape[:2]

    if pixel_size > 1:
        small_h = max(1, h // pixel_size)
        small_w = max(1, w // pixel_size)
        frame_small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
        mask_small = cv2.resize(mask, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
    else:
        frame_small = frame
        mask_small = mask

    quantized = quantize_colors(frame_small, n_colors, use_fixed_palette)

    height, width = quantized.shape[:2]
    ascii_str_lines = []
    block_char = "█"

    for y in range(height):
        line = ""
        for x in range(width):
            if mask_small[y, x] == 255:
                char = " "
                ansi_code = 232
            else:
                char = block_char
                b, g, r = quantized[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)

            line += f"{char}{COLOR_SEPARATOR}{ansi_code}{COLOR_SEPARATOR}"
        ascii_str_lines.append(line)

    return "\n".join(ascii_str_lines)


def iniciar_conversao(video_path, output_dir, config):
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')

        pixel_size = config.getint('PixelArt', 'pixel_size', fallback=2)
        n_colors = config.getint('PixelArt', 'color_palette_size', fallback=16)
        use_fixed_palette = config.getboolean('PixelArt', 'use_fixed_palette', fallback=False)

        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)

        lower_green = np.array([
            config.getint('ChromaKey', 'h_min'),
            config.getint('ChromaKey', 's_min'),
            config.getint('ChromaKey', 'v_min')
        ])
        upper_green = np.array([
            config.getint('ChromaKey', 'h_max'),
            config.getint('ChromaKey', 's_max'),
            config.getint('ChromaKey', 'v_max')
        ])
        erode_size = config.getint('ChromaKey', 'erode', fallback=2)
        dilate_size = config.getint('ChromaKey', 'dilate', fallback=2)
    except Exception as e:
        raise ValueError(f"Erro ao ler o config.ini. Erro: {e}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Erro: '{video_path}' nao encontrado.")

    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    caminho_saida = os.path.join(output_dir, f"{nome_base}.txt")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Erro: Nao abriu '{video_path}'.")

    fps = captura.get(cv2.CAP_PROP_FPS)
    frames_pixelart = []

    try:
        source_width = captura.get(cv2.CAP_PROP_FRAME_WIDTH)
        source_height = captura.get(cv2.CAP_PROP_FRAME_HEIGHT)

        config_height = config.getint('Conversor', 'target_height', fallback=0)
        if config_height > 0:
            target_height = config_height
        else:
            target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
            if target_height <= 0:
                target_height = int(target_width * (9/16) * char_aspect_ratio)

        target_dimensions = (target_width, target_height)
        manual_flag = '[altura manual]' if config_height > 0 else ''
        print(f"Video de origem: {int(source_width)}x{int(source_height)}. Convertendo para: {target_width}x{target_height} (blocos pixel art).{manual_flag}")
    except Exception as e:
        print(f"Aviso: Nao foi possivel calcular a proporcao. Usando 80x25. Erro: {e}")
        target_dimensions = (target_width, 25)

    frame_count = 0
    while True:
        sucesso, frame_colorido = captura.read()
        if not sucesso:
            break

        if sharpen_enabled:
            frame_colorido = sharpen_frame(frame_colorido, sharpen_amount)

        hsv_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)
        mask = apply_morphological_refinement(mask, erode_size, dilate_size)

        resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_LANCZOS4)
        resized_mask = cv2.resize(mask, target_dimensions, interpolation=cv2.INTER_NEAREST)

        frame_pixelart = converter_frame_para_pixelart(
            resized_color, resized_mask, pixel_size, n_colors, use_fixed_palette
        )
        frames_pixelart.append(frame_pixelart)
        frame_count += 1

    captura.release()
    print(f"Processados {frame_count} frames em pixel art.")
    
    try:
        with open(caminho_saida, 'w') as f:
            f.write(f"{fps}\n")
            f.write("[FRAME]\n".join(frames_pixelart))
        return caminho_saida
    except Exception as e:
        raise IOError(f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor de Conversao Pixel Art (CLI)")
    parser.add_argument("--video", required=True, help="Caminho do video para converter.")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Erro fatal: config.ini nao encontrado em {args.config}")
        sys.exit(1)

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    output_dir = config['Pastas']['output_dir']

    try:
        print(f"Iniciando conversao PIXEL ART (CLI) para: {args.video}")
        output_file = iniciar_conversao(args.video, output_dir, config)
        print(f"Conversao PIXEL ART (CLI) concluida: {output_file}")
    except Exception as e:
        print(f"Erro na conversao (CLI): {e}")
        sys.exit(1)
