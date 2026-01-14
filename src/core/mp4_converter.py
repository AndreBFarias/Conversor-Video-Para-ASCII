#!/usr/bin/env python3
import cv2
import os
import sys
import numpy as np
import configparser
import subprocess
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT as LUMINANCE_RAMP
from src.core.renderer import render_ascii_as_image


def converter_video_para_mp4(video_path: str, output_dir: str, config: configparser.ConfigParser, progress_callback=None, chroma_override=None) -> str:
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP).rstrip('|')

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
        raise ValueError(f"Erro ao ler config.ini: {e}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video nao encontrado: {video_path}")

    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    output_mp4 = os.path.join(output_dir, f"{nome_base}_ascii.mp4")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Erro ao abrir video: {video_path}")

    fps = captura.get(cv2.CAP_PROP_FPS)
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))

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

    print(f"Video: {int(source_width)}x{int(source_height)} -> ASCII: {target_width}x{target_height}")
    print(f"FPS: {fps}, Total frames: {total_frames}")

    temp_dir = tempfile.mkdtemp(prefix="ascii_mp4_")
    print(f"Frames temporarios em: {temp_dir}")

    try:
        frame_count = 0
        while True:
            sucesso, frame_colorido = captura.read()
            if not sucesso:
                break

            hsv = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
            mask_green = cv2.inRange(hsv, lower_green, upper_green)

            if erode_size > 0:
                kernel_erode = np.ones((erode_size, erode_size), np.uint8)
                mask_green = cv2.erode(mask_green, kernel_erode, iterations=1)
            if dilate_size > 0:
                kernel_dilate = np.ones((dilate_size, dilate_size), np.uint8)
                mask_green = cv2.dilate(mask_green, kernel_dilate, iterations=1)

            mask_refined = apply_morphological_refinement(mask_green)

            frame_gray = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)

            if sharpen_enabled:
                frame_gray = sharpen_frame(frame_gray, sharpen_amount=sharpen_amount)

            resized_gray = cv2.resize(frame_gray, target_dimensions, interpolation=cv2.INTER_AREA)
            resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)
            resized_mask = cv2.resize(mask_refined, target_dimensions, interpolation=cv2.INTER_NEAREST)

            dx = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            dy = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(dx**2 + dy**2)
            magnitude_norm = np.clip(magnitude, 0, 255).astype(np.uint8)
            angle = np.arctan2(dy, dx)

            ascii_string = converter_frame_para_ascii(
                resized_gray, resized_color, resized_mask,
                magnitude_norm, angle,
                sobel_threshold, luminance_ramp,
                output_format="file"
            )

            frame_image = render_ascii_as_image(ascii_string, font_scale=0.5)

            frame_filename = os.path.join(temp_dir, f"frame_{frame_count:06d}.png")
            cv2.imwrite(frame_filename, frame_image)

            frame_count += 1

            if progress_callback:
                if frame_count % 30 == 0:
                    progress_callback(frame_count, total_frames, frame_image)
                else:
                    progress_callback(frame_count, total_frames)

            if frame_count % 30 == 0:
                print(f"Processado: {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")

        captura.release()
        print(f"Total de frames renderizados: {frame_count}")

        print("Criando video ASCII (sem audio)...")
        temp_video = os.path.join(temp_dir, "temp_video.mp4")
        cmd_video = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', os.path.join(temp_dir, 'frame_%06d.png'),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            temp_video
        ]

        result = subprocess.run(cmd_video, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            raise RuntimeError(f"Erro ao criar video: {result.stderr}")

        print("Extraindo audio do video original...")
        temp_audio = os.path.join(temp_dir, "audio.aac")
        cmd_audio = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'copy',
            temp_audio
        ]

        result = subprocess.run(cmd_audio, capture_output=True, text=True, encoding='utf-8', errors='replace')
        has_audio = result.returncode == 0 and os.path.exists(temp_audio)

        if has_audio:
            print("Muxando video + audio...")
            cmd_mux = [
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', temp_audio,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_mp4
            ]
            result = subprocess.run(cmd_mux, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                raise RuntimeError(f"Erro ao muxar: {result.stderr}")
        else:
            print("Video sem audio, copiando video ASCII...")
            shutil.copy(temp_video, output_mp4)

        print(f"Video ASCII criado: {output_mp4}")
        return output_mp4

    finally:
        print(f"Limpando arquivos temporarios...")
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Converte video para ASCII MP4")
    parser.add_argument("--video", required=True, help="Caminho do video de entrada")
    parser.add_argument("--output", default="data_output", help="Diretorio de saida")
    parser.add_argument("--config", default="config.ini", help="Arquivo de configuracao")
    args = parser.parse_args()

    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)

    try:
        output_file = converter_video_para_mp4(args.video, args.output, config)
        print(f"\nSucesso! Video salvo em: {output_file}")
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
