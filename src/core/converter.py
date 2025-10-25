# Importações
import cv2
import os
import sys
import numpy as np
import configparser
import argparse 

# Constantes Globais
LUMINANCE_RAMP = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. " # '%' removido
COLOR_SEPARATOR = "§" 

def rgb_to_ansi256(r, g, b):
    # ... (código da função sem alteração) ...
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return 232 + int(((r - 8) / 247) * 23)
    ansi_r = int(r / 255 * 5)
    ansi_g = int(g / 255 * 5)
    ansi_b = int(b / 255 * 5)
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b

def converter_frame_para_ascii(gray_frame, color_frame, mask, magnitude_frame, angle_frame, sobel_threshold):
    # ... (código da função sem alteração) ...
    height, width = gray_frame.shape
    ascii_str_lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            if mask[y, x] == 255:
                char = " "
                ansi_code = 232
            elif magnitude_frame[y, x] > sobel_threshold:
                angle = angle_frame[y, x]
                if (angle > 67.5 and angle <= 112.5): char = "|"
                elif (angle > 112.5 and angle <= 157.5): char = "/"
                elif (angle > 157.5 or angle <= 22.5): char = "-"
                else: char = "\\"
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)
            else:
                pixel_brightness = gray_frame[y, x]
                char_index = int((pixel_brightness / 255) * (len(LUMINANCE_RAMP) - 1))
                char = LUMINANCE_RAMP[char_index]
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)
            line += f"{char}{COLOR_SEPARATOR}{ansi_code}{COLOR_SEPARATOR}"
        ascii_str_lines.append(line)
    return "\n".join(ascii_str_lines)

# Ponto de entrada da biblioteca
def iniciar_conversao(video_path, output_dir, config):
    # ... (código da função sem alteração) ...
    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
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
    except Exception as e:
        raise ValueError(f"Erro ao ler o config.ini. Erro: {e}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Erro: '{video_path}' não encontrado.")
    
    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    caminho_saida = os.path.join(output_dir, f"{nome_base}.txt")
    
    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Erro: Não abriu '{video_path}'.")
        
    fps = captura.get(cv2.CAP_PROP_FPS)
    frames_ascii = []
    
    try:
        source_width = captura.get(cv2.CAP_PROP_FRAME_WIDTH)
        source_height = captura.get(cv2.CAP_PROP_FRAME_HEIGHT)
        target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
        if target_height <= 0:
             target_height = int(target_width * (9/16) * char_aspect_ratio)
        target_dimensions = (target_width, target_height)
        print(f"Vídeo de origem: {int(source_width)}x{int(source_height)}. Convertendo para: {target_width}x{target_height} (caracteres).")
    except Exception as e:
        print(f"Aviso: Não foi possível calcular a proporção. Usando 80x25. Erro: {e}")
        target_dimensions = (target_width, 25)

    while True:
        sucesso, frame_colorido = captura.read()
        if not sucesso:
            break
        hsv_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)
        grayscale_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
        resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_AREA)
        resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(mask, target_dimensions, interpolation=cv2.INTER_NEAREST)
        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        frame_ascii = converter_frame_para_ascii(
            resized_gray, resized_color, resized_mask, magnitude_norm, angle, sobel_threshold
        )
        frames_ascii.append(frame_ascii)
        
    captura.release()
    try:
        with open(caminho_saida, 'w') as f:
            f.write(f"{fps}\n")
            f.write("[FRAME]\n".join(frames_ascii))
        return caminho_saida
    except Exception as e:
        raise IOError(f"Selamento falhou: {e}")

# (NOVO) Bloco de execução para subprocesso
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor de Conversão ASCII (CLI)")
    parser.add_argument("--video", required=True, help="Caminho do vídeo para converter.")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Erro fatal: config.ini não encontrado em {args.config}")
        sys.exit(1)

    # --- #CORREÇÃO DE INTERPOLAÇÃO ---
    config = configparser.ConfigParser(interpolation=None)
    config.read(args.config)
    
    # Adiciona a rampa padrão caso esteja faltando
    if not config.has_option('Conversor', 'LUMINANCE_RAMP'):
        if not config.has_section('Conversor'):
            config.add_section('Conversor')
        config.set('Conversor', 'LUMINANCE_RAMP', LUMINANCE_RAMP)
        
    output_dir = config['Pastas']['output_dir']

    try:
        print(f"Iniciando conversão (CLI) para: {args.video}")
        output_file = iniciar_conversao(args.video, output_dir, config)
        print(f"Conversão (CLI) concluída: {output_file}")
    except Exception as e:
        print(f"Erro na conversão (CLI): {e}")
