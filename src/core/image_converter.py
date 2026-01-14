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
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT as LUMINANCE_RAMP, COLOR_SEPARATOR


def iniciar_conversao_imagem(image_path, output_dir, config):
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
        luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP).rstrip('|')
        print(f"Usando rampa: {repr(luminance_ramp)} ({len(luminance_ramp)} caracteres)")
        
        # Melhorias de nitidez
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
    print(f"Imagem: {source_width}x{source_height}. Convertendo para: {target_width}x{target_height} (caracteres).")

    hsv_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, lower_green, upper_green)
    mask = apply_morphological_refinement(mask, erode_size, dilate_size)
    grayscale_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)

    resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_AREA)
    resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)
    resized_mask = cv2.resize(mask, target_dimensions, interpolation=cv2.INTER_NEAREST)

    if sharpen_enabled:
        resized_color = sharpen_frame(resized_color, sharpen_amount)
        resized_gray = cv2.cvtColor(resized_color, cv2.COLOR_BGR2GRAY)

    sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.hypot(sobel_x, sobel_y)
    angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
    angle = (angle + 180) % 180
    magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

    frame_ascii = converter_frame_para_ascii(
        resized_gray, resized_color, resized_mask, magnitude_norm, angle, sobel_threshold, luminance_ramp,
        output_format="file"
    )

    try:
        with open(caminho_saida, 'w') as f:
            f.write("0\n")
            f.write(frame_ascii)
        return caminho_saida
    except Exception as e:
        raise IOError(f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor de Conversao de Imagem para ASCII (CLI)")
    parser.add_argument("--image", required=True, help="Caminho da imagem para converter.")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Erro fatal: config.ini nao encontrado em {args.config}")
        sys.exit(1)

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    if not config.has_option('Conversor', 'luminance_ramp'):
        if not config.has_section('Conversor'):
            config.add_section('Conversor')
        config.set('Conversor', 'luminance_ramp', LUMINANCE_RAMP)

    output_dir = config['Pastas']['output_dir']

    try:
        print(f"Iniciando conversao de imagem (CLI) para: {args.image}")
        output_file = iniciar_conversao_imagem(args.image, output_dir, config)
        print(f"Conversao (CLI) concluida: {output_file}")
    except Exception as e:
        print(f"Erro na conversao (CLI): {e}")
        sys.exit(1)
