# -*- coding: utf-8 -*-
import cv2
import numpy as np
import configparser
import argparse
import sys
import os
import time

# --- #1. LÓGICA IMPORTADA DO 'realtime_ascii.py' ---

ANSI_RESET = "\033[0m"
ANSI_CLEAR_AND_HOME = "\033[2J\033[H" 

def rgb_to_ansi256(r, g, b):
    """ Converte RGB para código ANSI 256. """
    if r == g == b: # Escala de Cinza
        if r < 8: return 16
        if r > 248: return 231
        return 232 + int(((r - 8) / 247) * 23)
    # Cubo de Cores 6x6x6
    ansi_r = int(r / 255 * 5); ansi_g = int(g / 255 * 5); ansi_b = int(b / 255 * 5)
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b

def frame_para_ascii_calibrador(gray_frame, color_frame, mask, magnitude_frame, angle_frame, sobel_threshold, luminance_ramp):
    """
    Função híbrida: Lógica do 'realtime_ascii.py' 
    fundida com a lógica de máscara do 'converter.py'.
    """
    height, width = gray_frame.shape
    output_buffer = []
    
    for y in range(height):
        line_buffer = []
        for x in range(width):
            
            # --- #2. LÓGICA DE MÁSCARA ADICIONADA ---
            # Prioridade 0: Máscara de Chroma Key
            if mask[y, x] == 255:
                char = " "
                ansi_code = 232 # Um cinza escuro/preto para o "fundo"
            
            # Prioridade 1: Bordas (Sobel)
            elif magnitude_frame[y, x] > sobel_threshold:
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
            if char:
                 line_buffer.append(f"\033[38;5;{ansi_code}m{char}")
            else:
                 line_buffer.append(" ") 
                 
        output_buffer.append("".join(line_buffer))
        
    # Retorna string completa com reset no final
    return "\n".join(output_buffer) + ANSI_RESET

# --- Fim da lógica importada ---


# Variáveis globais para os trackbars
config_global = None
config_path_global = None

# Nomes das Janelas
WINDOW_ORIGINAL = "Janela 1: Original (Webcam)"
WINDOW_RESULT = "Janela 2: Filtro Chroma ('s' Salva, 'q' Sai)"
WINDOW_CONTROLS = "Controles"
# Janela 3 é o próprio terminal

def load_config(config_path):
    """ Lê o arquivo de configuração. """
    if not os.path.exists(config_path):
        print(f"Erro: config.ini não encontrado em: {config_path}", file=sys.stderr)
        return None
        
    # --- #A CORREÇÃO ESTÁ AQUI ---
    # Desliga a "mágica" do '%' (interpolação)
    config = configparser.ConfigParser(interpolation=None)
    
    try:
        # Adiciona padrões seguros
        config.add_section('Conversor')
        config.set('Conversor', 'LUMINANCE_RAMP', "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")
        
        config.read(config_path, encoding='utf-8')
        return config
    except Exception as e:
        print(f"Erro ao ler config.ini: {e}", file=sys.stderr)
        return None

def get_initial_values(config):
    """ Busca os valores H, S, V do config, ou retorna padrões. """
    defaults = {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255}
    if 'ChromaKey' not in config:
        print("Seção [ChromaKey] não encontrada, usando padrões.")
        return defaults
    try:
        return {
            'h_min': config.getint('ChromaKey', 'h_min', fallback=defaults['h_min']),
            'h_max': config.getint('ChromaKey', 'h_max', fallback=defaults['h_max']),
            's_min': config.getint('ChromaKey', 's_min', fallback=defaults['s_min']),
            's_max': config.getint('ChromaKey', 's_max', fallback=defaults['s_max']),
            'v_min': config.getint('ChromaKey', 'v_min', fallback=defaults['v_min']),
            'v_max': config.getint('ChromaKey', 'v_max', fallback=defaults['v_max'])
        }
    except Exception as e:
        print(f"Erro ao ler valores [ChromaKey]: {e}. Usando padrões.")
        return defaults

def on_trackbar(val):
    pass

def save_values(trackbar_values):
    """ Salva os valores atuais no config.ini """
    global config_global, config_path_global
    if config_global is None or config_path_global is None: return

    print("\nSalvando valores...") # Adiciona \n para não sobrepor o ASCII
    try:
        # Recarrega o config para garantir que temos a versão mais recente (caso algo tenha mudado)
        # Mas mantemos a instância config_global para preservar comentários se possível?
        # ConfigParser do Python não preserva comentários por padrão.
        # Vamos apenas garantir que a seção existe e escrever.
        
        if 'ChromaKey' not in config_global:
            config_global.add_section('ChromaKey')
            
        config_global.set('ChromaKey', 'h_min', str(trackbar_values['h_min']))
        config_global.set('ChromaKey', 'h_max', str(trackbar_values['h_max']))
        config_global.set('ChromaKey', 's_min', str(trackbar_values['s_min']))
        config_global.set('ChromaKey', 's_max', str(trackbar_values['s_max']))
        config_global.set('ChromaKey', 'v_min', str(trackbar_values['v_min']))
        config_global.set('ChromaKey', 'v_max', str(trackbar_values['v_max']))
        
        with open(config_path_global, 'w', encoding='utf-8') as configfile:
            config_global.write(configfile)
        print(f"Valores salvos com sucesso em {config_path_global}")
        print(f"H: {trackbar_values['h_min']}-{trackbar_values['h_max']}, S: {trackbar_values['s_min']}-{trackbar_values['s_max']}, V: {trackbar_values['v_min']}-{trackbar_values['v_max']}")
        
    except Exception as e:
        print(f"Erro fatal ao salvar config: {e}", file=sys.stderr)

def reset_defaults():
    """ Reseta os trackbars para os valores padrão. """
    defaults = {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255}
    print("\nResetando para os valores padrão...")
    cv2.setTrackbarPos("H Min", WINDOW_CONTROLS, defaults['h_min'])
    cv2.setTrackbarPos("H Max", WINDOW_CONTROLS, defaults['h_max'])
    cv2.setTrackbarPos("S Min", WINDOW_CONTROLS, defaults['s_min'])
    cv2.setTrackbarPos("S Max", WINDOW_CONTROLS, defaults['s_max'])
    cv2.setTrackbarPos("V Min", WINDOW_CONTROLS, defaults['v_min'])
    cv2.setTrackbarPos("V Max", WINDOW_CONTROLS, defaults['v_max'])
    print("Valores resetados. Pressione 's' para salvar se desejar.")

def main():
    global config_global, config_path_global
    
    parser = argparse.ArgumentParser(description="Calibrador de Chroma Key (OpenCV)")
    parser.add_argument('--config', required=True, help="Caminho para o config.ini")
    parser.add_argument('--video', required=False, default=None, help="Caminho opcional para um vídeo")
    args = parser.parse_args()

    config_path_global = args.config
    config_global = load_config(config_path_global)
    if config_global is None:
        sys.exit(1)
        
    initial_values = get_initial_values(config_global)

    # --- #3. LÊ AS CONFIGS DE CONVERSÃO (do realtime_ascii.py) ---
    try:
        target_width = config_global.getint('Conversor', 'target_width', fallback=80)
        char_aspect_ratio = config_global.getfloat('Conversor', 'char_aspect_ratio', fallback=0.45)
        sobel_threshold = config_global.getint('Conversor', 'sobel_threshold', fallback=50)
        luminance_ramp = config_global.get('Conversor', 'LUMINANCE_RAMP') 
    except Exception as e:
        print(f"Aviso: Erro ao ler [Conversor] do config: {e}. Usando padrões.")
        target_width = 80; char_aspect_ratio = 0.45; sobel_threshold = 50
        luminance_ramp = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

    is_video_file = args.video is not None
    capture_source = args.video if is_video_file else 0
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir a fonte de vídeo: {capture_source}", file=sys.stderr)
        sys.exit(1)
    print(f"Fonte de vídeo aberta: {capture_source}")

    # --- #4. CALCULA AS DIMENSÕES DO ASCII ---
    target_dimensions = (target_width, 25) # Padrão
    try:
        ret, frame_teste = cap.read()
        if not ret or frame_teste is None:
             raise ValueError("Não foi possível ler o primeiro frame.")
        source_height, source_width, _ = frame_teste.shape
        target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
        if target_height <= 0: target_height = int(target_width * (9/16) * char_aspect_ratio)
        target_dimensions = (target_width, target_height)
        print(f"Dimensões ASCII calculadas: {target_width}x{target_height} chars.")
    except Exception as e:
        print(f"Aviso: Erro ao calcular dimensões ASCII: {e}. Usando {target_dimensions}.")

    # Cria as 3 janelas
    cv2.namedWindow(WINDOW_ORIGINAL)
    cv2.namedWindow(WINDOW_RESULT)
    cv2.namedWindow(WINDOW_CONTROLS, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(WINDOW_ORIGINAL, 50, 50)
    cv2.moveWindow(WINDOW_RESULT, 700, 50)
    cv2.moveWindow(WINDOW_CONTROLS, 50, 550)

    # Cria os 6 trackbars
    cv2.createTrackbar("H Min", WINDOW_CONTROLS, initial_values['h_min'], 179, on_trackbar)
    cv2.createTrackbar("H Max", WINDOW_CONTROLS, initial_values['h_max'], 179, on_trackbar)
    cv2.createTrackbar("S Min", WINDOW_CONTROLS, initial_values['s_min'], 255, on_trackbar)
    cv2.createTrackbar("S Max", WINDOW_CONTROLS, initial_values['s_max'], 255, on_trackbar)
    cv2.createTrackbar("V Min", WINDOW_CONTROLS, initial_values['v_min'], 255, on_trackbar)
    cv2.createTrackbar("V Max", WINDOW_CONTROLS, initial_values['v_max'], 255, on_trackbar)

    print("Controles criados. Loop iniciado.")
    print("COMANDOS:")
    print("  's' : Salvar configurações no config.ini")
    print("  'r' : Resetar para valores padrão")
    print("  'q' : Sair")
    
    os.system('cls' if os.name == 'nt' else 'clear') # Limpa o terminal para o ASCII

    while True:
        ret, frame = cap.read()
        if not ret:
            if is_video_file:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
            else:
                print("Erro ao ler frame da webcam.", file=sys.stderr); break
        
        if not is_video_file: frame = cv2.flip(frame, 1)

        # --- JANELA 2 (FILTRO) ---
        h_min = cv2.getTrackbarPos("H Min", WINDOW_CONTROLS)
        h_max = cv2.getTrackbarPos("H Max", WINDOW_CONTROLS)
        s_min = cv2.getTrackbarPos("S Min", WINDOW_CONTROLS)
        s_max = cv2.getTrackbarPos("S Max", WINDOW_CONTROLS)
        v_min = cv2.getTrackbarPos("V Min", WINDOW_CONTROLS)
        v_max = cv2.getTrackbarPos("V Max", WINDOW_CONTROLS)
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask_original_size = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(frame, frame, mask=mask_original_size)

        # --- JANELA 3 (ASCII - Processamento) ---
        # Processamento (similar ao realtime_ascii.py)
        grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_AREA)
        resized_color = cv2.resize(frame, target_dimensions, interpolation=cv2.INTER_AREA)
        # Redimensiona a máscara que acabamos de calcular
        resized_mask = cv2.resize(mask_original_size, target_dimensions, interpolation=cv2.INTER_NEAREST)

        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        frame_ascii = frame_para_ascii_calibrador(
            resized_gray, resized_color, resized_mask, # Passa a máscara
            magnitude_norm, angle, 
            sobel_threshold, luminance_ramp
        )

        # --- MOSTRA AS 3 JANELAS ---
        cv2.imshow(WINDOW_ORIGINAL, frame)   # Janela 1
        cv2.imshow(WINDOW_RESULT, result) # Janela 2
        
        # Janela 3 (Terminal)
        sys.stdout.write(ANSI_CLEAR_AND_HOME + frame_ascii)
        sys.stdout.flush()

        # Checa os controles
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q'): 
            print("Tecla 'q' pressionada. Saindo sem salvar.")
            break
            
        if key == ord('s'): 
            print("Tecla 's' pressionada. Salvando...")
            current_values = {'h_min': h_min, 'h_max': h_max, 's_min': s_min, 's_max': s_max, 'v_min': v_min, 'v_max': v_max}
            save_values(current_values)
            
        if key == ord('r'):
            reset_defaults()
            
        try:
            if cv2.getWindowProperty(WINDOW_ORIGINAL, cv2.WND_PROP_VISIBLE) < 1: break
            if cv2.getWindowProperty(WINDOW_RESULT, cv2.WND_PROP_VISIBLE) < 1: break
            if cv2.getWindowProperty(WINDOW_CONTROLS, cv2.WND_PROP_VISIBLE) < 1: break
        except cv2.error:
            break

    # Limpeza
    print("\nFinalizando...")
    cap.release()
    cv2.destroyAllWindows()
    # Limpa o terminal ao sair
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ANSI_RESET) 
    sys.exit(0)


if __name__ == "__main__":
    main()
