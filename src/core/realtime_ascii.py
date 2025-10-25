# #1. Conversor ASCII em Tempo Real (Webcam)
import cv2
import numpy as np
import os
import sys
import configparser
import argparse
import time

# Constantes (Reutilizadas do player e converter)
ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§" 
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"
LUMINANCE_RAMP_DEFAULT = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. " # '%' removido

# --- Funções Reutilizadas (Adaptadas) ---

def rgb_to_ansi256(r, g, b):
    if r == g == b: # Escala de Cinza
        if r < 8: return 16
        if r > 248: return 231
        return 232 + int(((r - 8) / 247) * 23)
    # Cubo de Cores 6x6x6
    ansi_r = int(r / 255 * 5); ansi_g = int(g / 255 * 5); ansi_b = int(b / 255 * 5)
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b

def frame_para_ascii_rt(gray_frame, color_frame, magnitude_frame, angle_frame, sobel_threshold, luminance_ramp):
    """Versão simplificada para real-time, sem máscara."""
    height, width = gray_frame.shape
    output_buffer = []
    
    for y in range(height):
        line_buffer = []
        for x in range(width):
            # Prioridade 1: Bordas (Sobel)
            if magnitude_frame[y, x] > sobel_threshold:
                angle = angle_frame[y, x]
                if (angle > 67.5 and angle <= 112.5): char = "|"
                elif (angle > 112.5 and angle <= 157.5): char = "/"
                elif (angle > 157.5 or angle <= 22.5): char = "-"
                else: char = "\\"
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)

            # Prioridade 2: Superfície (Luminância)
            else:
                pixel_brightness = gray_frame[y, x]
                char_index = int((pixel_brightness / 255) * (len(luminance_ramp) - 1))
                char = luminance_ramp[char_index]
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)

            # Monta string ANSI diretamente
            if char: # Evita adicionar códigos para nada se o char for vazio
                 line_buffer.append(f"\033[38;5;{ansi_code}m{char}")
            else:
                 line_buffer.append(" ") # Adiciona espaço se não houver char
                 
        output_buffer.append("".join(line_buffer))
        
    # Retorna string completa com reset no final
    return "\n".join(output_buffer) + ANSI_RESET


def run_realtime_ascii(config_path):
    """Executa a conversão da webcam em tempo real."""

    # --- Leitura da Configuração ---
    
    # --- #CORREÇÃO DE INTERPOLAÇÃO ---
    config = configparser.ConfigParser(interpolation=None)
    
    # Adiciona uma rampa padrão caso o config.ini não a tenha
    config.add_section('Conversor') 
    config.set('Conversor', 'LUMINANCE_RAMP', LUMINANCE_RAMP_DEFAULT) 
    
    if not config.read(config_path):
        print(f"Erro fatal: config.ini não encontrado em {config_path}")
        return

    try:
        target_width = config.getint('Conversor', 'target_width', fallback=80)
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio', fallback=0.45)
        sobel_threshold = config.getint('Conversor', 'sobel_threshold', fallback=50)
        # Lê a rampa do config OU usa o fallback definido acima
        luminance_ramp = config.get('Conversor', 'LUMINANCE_RAMP') 
    except Exception as e:
        print(f"Erro ao ler config.ini: {e}. Usando valores padrão.")
        target_width = 80; char_aspect_ratio = 0.45; sobel_threshold = 50
        luminance_ramp = LUMINANCE_RAMP_DEFAULT


    # --- Abertura da Webcam ---
    cap = cv2.VideoCapture(0) # Fonte 0 é geralmente a webcam padrão
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam.")
        return

    # --- Cálculo Dinâmico da Altura (feito uma vez) ---
    try:
        ret, frame_teste = cap.read()
        if not ret or frame_teste is None:
             raise ValueError("Não foi possível ler o primeiro frame da webcam.")
        source_height, source_width, _ = frame_teste.shape
        target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
        if target_height <= 0: target_height = int(target_width * (9/16) * char_aspect_ratio)
        target_dimensions = (target_width, target_height)
        print(f"Webcam detectada: {source_width}x{source_height}. Convertendo para: {target_width}x{target_height} chars.")
        print("Pressione Ctrl+C para sair.")
    except Exception as e:
        print(f"Erro ao calcular dimensões: {e}. Usando 80x{int(80*0.45*(9/16))}.")
        target_dimensions = (target_width, int(target_width * 0.45 * (9/16))) # Fallback


    # --- Loop Principal ---
    try:
        while True:
            ret, frame_colorido = cap.read()
            if not ret or frame_colorido is None:
                print("Erro ao ler frame da webcam.")
                time.sleep(0.5) # Pausa antes de tentar novamente
                continue

            # Inverte horizontalmente (efeito espelho)
            frame_colorido = cv2.flip(frame_colorido, 1)

            # --- Processamento (similar ao converter.py) ---
            grayscale_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
            
            resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_AREA)
            resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_AREA)

            sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.hypot(sobel_x, sobel_y)
            angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
            angle = (angle + 180) % 180
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            # --- Geração e Impressão ---
            frame_ascii = frame_para_ascii_rt(
                resized_gray, resized_color, magnitude_norm, angle, 
                sobel_threshold, luminance_ramp
            )

            # Limpa terminal e imprime
            sys.stdout.write(ANSI_CLEAR_AND_HOME + frame_ascii)
            sys.stdout.flush()

            # Controle de FPS (aproximado)
            time.sleep(1.0 / 30) # Tenta ~30 FPS

    except KeyboardInterrupt:
        print("\nSaindo do modo Real-Time...")
    except Exception as e:
         print(f"\nErro inesperado no loop: {e}")
    finally:
        # --- Limpeza ---
        if cap.isOpened():
            cap.release()
        # Limpa o terminal ao sair
        os.system('cls' if os.name == 'nt' else 'clear')
        print(ANSI_RESET) # Garante reset da cor


# Bloco de execução INDEPENDENTE (para subprocess)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conversor Webcam -> ASCII em Tempo Real")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    args = parser.parse_args()

    run_realtime_ascii(config_path=args.config)
