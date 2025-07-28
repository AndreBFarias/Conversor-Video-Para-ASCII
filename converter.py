# O núcleo do feitiço, converter.py. Processa vídeo via --video, aplica chroma key com valores do antigo, converte pra ASCII rico – espaços pro fundo zerado, nuances pros detalhes. Salva .txt como antigo Luna_feliz.

# #1. Invocações e Sigilos: cv2, os, numpy, configparser, argparse. Define LOWER/UPPER_GREEN do antigo, ASCII_CHARS rico, dimensões fixas.

# #2. Função de Transmutação: Pra pixel cinza: se máscara branca, espaço; senão, mapeia brilho pra caractere.

# #3. Círculo Principal: Parseia --video, lê config, constrói caminhos, captura, lê FPS, loop: máscara verde, redimensiona cinza e máscara, converte, coleta. Sela .txt.

import cv2
import os
import numpy as np
import configparser
import argparse

LOWER_GREEN = np.array([35, 40, 40])
UPPER_GREEN = np.array([85, 255, 255])

ASCII_CHARS = "@%#*+=-:. "
TARGET_WIDTH = 90
TARGET_HEIGHT = 25

def converter_frame_para_ascii(grayscale_frame, mask):
    height, width = grayscale_frame.shape
    ascii_str = ""
    for y in range(height):
        for x in range(width):
            if mask[y, x] == 255:
                ascii_str += " "
            else:
                pixel_brightness = grayscale_frame[y, x]
                char_index = int(pixel_brightness) * len(ASCII_CHARS) // 256
                ascii_str += ASCII_CHARS[char_index]
        ascii_str += "\n"
    return ascii_str

def main():
    parser = argparse.ArgumentParser(description="Converte vídeos pra ASCII.")
    parser.add_argument("--video", required=True, help="Vídeo a processar.")
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read('config.ini')
    pasta_saida = config['Pastas']['output_dir']
    caminho_video = os.path.join(config['Pastas']['input_dir'], args.video)
    if not os.path.exists(caminho_video):
        print(f"Erro: '{caminho_video}' não encontrado.")
        return
    nome_base = os.path.splitext(args.video)[0]
    caminho_saida = os.path.join(pasta_saida, f"{nome_base}.txt")
    captura = cv2.VideoCapture(caminho_video)
    if not captura.isOpened():
        print(f"Erro: Não abriu '{caminho_video}'.")
        return
    fps = captura.get(cv2.CAP_PROP_FPS)
    frames_ascii = []
    while True:
        sucesso, frame_colorido = captura.read()
        if not sucesso:
            break
        hsv_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, LOWER_GREEN, UPPER_GREEN)
        grayscale_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
        target_dimensions = (TARGET_WIDTH, TARGET_HEIGHT)
        resized_gray = cv2.resize(grayscale_frame, target_dimensions)
        resized_mask = cv2.resize(mask, target_dimensions, interpolation=cv2.INTER_NEAREST)
        frame_ascii = converter_frame_para_ascii(resized_gray, resized_mask)
        frames_ascii.append(frame_ascii)
    captura.release()
    try:
        with open(caminho_saida, 'w') as f:
            f.write(f"{fps}\n")
            f.write("[FRAME]\n".join(frames_ascii))
        print(f"Evocação de '{args.video}' selada em: {caminho_saida}")
    except Exception as e:
        print(f"Selamento falhou: {e}")

if __name__ == '__main__':
    main()

# "A simplicidade é a suprema sofisticação." - Leonardo da Vinci, sussurrando que no retorno ao essencial reside o eterno poder.