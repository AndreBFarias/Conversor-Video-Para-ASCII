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


def iniciar_conversao(video_path, output_dir, config, chroma_override=None, force_output_path=None):
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')

        # Melhorias de nitidez
        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)

        # LER RAMPA DO CONFIG.INI (importante para caracteres personalizados!)
        luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP).rstrip('|')
        print(f"Usando rampa: {repr(luminance_ramp)} ({len(luminance_ramp)} caracteres)")

        if chroma_override:
            lower_green = np.array([
                chroma_override['h_min'],
                chroma_override['s_min'],
                chroma_override['v_min']
            ])
            upper_green = np.array([
                chroma_override['h_max'],
                chroma_override['s_max'],
                chroma_override['v_max']
            ])
            erode_size = chroma_override.get('erode', 2)
            dilate_size = chroma_override.get('dilate', 2)
        else:
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

    if force_output_path:
        caminho_saida = force_output_path
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    else:
        nome_base = os.path.splitext(os.path.basename(video_path))[0]
        caminho_saida = os.path.join(output_dir, f"{nome_base}.txt")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Erro: Nao abriu '{video_path}'.")

    fps = captura.get(cv2.CAP_PROP_FPS)
    frames_ascii = []

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
        print(f"Video de origem: {int(source_width)}x{int(source_height)}. Convertendo para: {target_width}x{target_height} (caracteres).{manual_flag}")
    except Exception as e:
        print(f"Aviso: Nao foi possivel calcular a proporcao. Usando 80x25. Erro: {e}")
        target_dimensions = (target_width, 25)

    while True:
        sucesso, frame_colorido = captura.read()
        if not sucesso:
            break

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
        frames_ascii.append(frame_ascii)

    captura.release()
    try:
        with open(caminho_saida, 'w') as f:
            f.write(f"{fps}\n")
            f.write("[FRAME]\n".join(frames_ascii))
        return caminho_saida
    except Exception as e:
        raise IOError(f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor de Conversao ASCII (CLI)")
    parser.add_argument("--video", required=True, help="Caminho do video para converter.")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    parser.add_argument("--h-min", type=int, default=None, help="ChromaKey H min override")
    parser.add_argument("--h-max", type=int, default=None, help="ChromaKey H max override")
    parser.add_argument("--s-min", type=int, default=None, help="ChromaKey S min override")
    parser.add_argument("--s-max", type=int, default=None, help="ChromaKey S max override")
    parser.add_argument("--v-min", type=int, default=None, help="ChromaKey V min override")
    parser.add_argument("--v-max", type=int, default=None, help="ChromaKey V max override")
    parser.add_argument("--erode", type=int, default=None, help="ChromaKey erode override")
    parser.add_argument("--dilate", type=int, default=None, help="ChromaKey dilate override")
    parser.add_argument("--output", default=None, help="Caminho explicito para arquivo de saida.")
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

    chroma_override = None
    if args.h_min is not None:
        chroma_override = {
            'h_min': args.h_min,
            'h_max': args.h_max if args.h_max is not None else config.getint('ChromaKey', 'h_max', fallback=85),
            's_min': args.s_min if args.s_min is not None else config.getint('ChromaKey', 's_min', fallback=40),
            's_max': args.s_max if args.s_max is not None else config.getint('ChromaKey', 's_max', fallback=255),
            'v_min': args.v_min if args.v_min is not None else config.getint('ChromaKey', 'v_min', fallback=40),
            'v_max': args.v_max if args.v_max is not None else config.getint('ChromaKey', 'v_max', fallback=255),
            'erode': args.erode if args.erode is not None else config.getint('ChromaKey', 'erode', fallback=2),
            'dilate': args.dilate if args.dilate is not None else config.getint('ChromaKey', 'dilate', fallback=2)
        }

    output_dir = config['Pastas']['output_dir']

    try:
        print(f"Iniciando conversao (CLI) para: {args.video}")
        output_file = iniciar_conversao(args.video, output_dir, config, chroma_override=chroma_override, force_output_path=args.output)
        print(f"Conversao (CLI) concluida: {output_file}")
    except Exception as e:
        print(f"Erro na conversao (CLI): {e}")
