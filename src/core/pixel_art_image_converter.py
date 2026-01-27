#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import os
import sys
import numpy as np
import configparser
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement

COLOR_SEPARATOR = "§"

DEFAULT_PALETTE_16 = np.array([
    [0, 0, 0],
    [255, 255, 255],
    [255, 0, 0],
    [0, 255, 0],
    [0, 0, 255],
    [255, 255, 0],
    [255, 0, 255],
    [0, 255, 255],
    [128, 0, 0],
    [0, 128, 0],
    [0, 0, 128],
    [128, 128, 128],
    [192, 192, 192],
    [128, 128, 0],
    [128, 0, 128],
    [0, 128, 128],
], dtype=np.float32)


def quantize_colors(image, n_colors=16, use_fixed_palette=False):
    h, w, c = image.shape
    pixels = image.reshape((-1, 3)).astype(np.float32)

    if use_fixed_palette:
        palette = DEFAULT_PALETTE_16[:min(n_colors, 16)]
        dists = np.sum((pixels[:, np.newaxis, :] - palette[np.newaxis, :, :]) ** 2, axis=2)
        labels = np.argmin(dists, axis=1)
        quantized = palette[labels].astype(np.uint8)
    else:
        n_colors = min(max(2, n_colors), 64)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
        quantized = centers[labels.flatten()].astype(np.uint8)

    return quantized.reshape((h, w, c))


def converter_imagem_para_pixelart(frame, mask, pixel_size, n_colors, use_fixed_palette):
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


def iniciar_conversao_imagem(image_path, output_dir, config):
    """
    Convert an image to pixel art format
    
    Args:
        image_path: Path to input image
        output_dir: Directory to save output
        config: ConfigParser object with settings
    
    Returns:
        Path to output file
    """
    try:
        # Read converter settings
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        
        # Read pixel art settings
        pixel_size = config.getint('PixelArt', 'pixel_size', fallback=2)
        n_colors = config.getint('PixelArt', 'color_palette_size', fallback=16)
        use_fixed_palette = config.getboolean('PixelArt', 'use_fixed_palette', fallback=False)
        
        # Melhorias de nitidez
        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        
        # Read chroma key settings
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

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Erro: '{image_path}' nao encontrado.")

    nome_base = os.path.splitext(os.path.basename(image_path))[0]
    caminho_saida = os.path.join(output_dir, f"{nome_base}.txt")

    frame_colorido = cv2.imread(image_path)
    if frame_colorido is None:
        raise IOError(f"Erro: Nao foi possivel ler a imagem '{image_path}'.")

    source_height, source_width = frame_colorido.shape[:2]
    target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
    if target_height <= 0:
        target_height = int(target_width * (9/16) * char_aspect_ratio)
    target_dimensions = (target_width, target_height)
    print(f"Imagem: {source_width}x{source_height}. Convertendo para: {target_width}x{target_height} (blocos pixel art).")

    # Aplica sharpen ANTES de redimensionar (melhor resultado para Pixel Art)
    if sharpen_enabled:
        frame_colorido = sharpen_frame(frame_colorido, sharpen_amount)
    
    # Apply chroma key
    hsv_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, lower_green, upper_green)
    mask = apply_morphological_refinement(mask, erode_size, dilate_size)

    # Resize (usa INTER_LANCZOS4 para melhor qualidade)
    resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_LANCZOS4)
    resized_mask = cv2.resize(mask, target_dimensions, interpolation=cv2.INTER_NEAREST)

    # Convert to pixel art
    frame_pixelart = converter_imagem_para_pixelart(
        resized_color, resized_mask, pixel_size, n_colors, use_fixed_palette
    )

    try:
        with open(caminho_saida, 'w') as f:
            f.write("0\n")  # FPS = 0 for static image
            f.write(frame_pixelart)
        return caminho_saida
    except Exception as e:
        raise IOError(f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor de Conversao de Imagem para Pixel Art (CLI)")
    parser.add_argument("--image", required=True, help="Caminho da imagem para converter.")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    parser.add_argument("--output-dir", required=False, help="Diretorio de saida (override).")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Erro fatal: config.ini nao encontrado em {args.config}")
        sys.exit(1)

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = config.get('Pastas', 'output_dir', fallback='')
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(args.image), 'output')
            os.makedirs(output_dir, exist_ok=True)

    try:
        print(f"Iniciando conversao de imagem PIXEL ART (CLI) para: {args.image}")
        print(f"Diretorio de saida: {output_dir}")
        output_file = iniciar_conversao_imagem(args.image, output_dir, config)
        print(f"Conversao PIXEL ART (CLI) concluida: {output_file}")
    except Exception as e:
        print(f"Erro na conversao (CLI): {e}")
        sys.exit(1)
