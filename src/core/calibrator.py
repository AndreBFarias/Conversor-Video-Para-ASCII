import cv2
import numpy as np
import configparser
import argparse
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.color import rgb_to_ansi256
from src.core.utils.image import sharpen_frame, apply_morphological_refinement
from src.core.utils.ascii_converter import converter_frame_para_ascii, LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR

ANSI_RESET = "\033[0m"
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"

config_global = None
config_path_global = None

WINDOW_ORIGINAL = "Janela 1: Original (Webcam)"
WINDOW_RESULT = "Janela 2: Filtro Chroma ('s' Salva, 'q' Sai)"
WINDOW_CONTROLS = "Controles"


# Presets de Chroma Key
CHROMA_PRESETS = {
    'studio': {'h_min': 35, 'h_max': 85, 's_min': 50, 's_max': 255, 'v_min': 50, 'v_max': 255},  # Verde estúdio profissional
    'natural': {'h_min': 35, 'h_max': 90, 's_min': 30, 's_max': 255, 'v_min': 30, 'v_max': 255}, # Verde natural (outdoor)
    'bright': {'h_min': 40, 'h_max': 80, 's_min': 80, 's_max': 255, 'v_min': 80, 'v_max': 255},  # Verde vibrante/brilhante
}


def auto_detect_green(frame):
    """Detecta automaticamente valores HSV ideais para chroma key verde
    
    Args:
        frame: Frame BGR do OpenCV
    
    Returns:
        dict com keys: h_min, h_max, s_min, s_max, v_min, v_max
    """
    # Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define filtro inicial amplo para verdes
    lower_broad = np.array([30, 40, 40])
    upper_broad = np.array([90, 255, 255])
    
    # Máscara inicial
    mask_broad = cv2.inRange(hsv, lower_broad, upper_broad)
    
    # Pega apenas pixels verdes
    green_pixels = hsv[mask_broad > 0]
    
    if len(green_pixels) == 0:
        # Sem verde detectado, retorna valores padrão studio
        print("Aviso: Nenhum verde detectado. Usando preset Studio.")
        return CHROMA_PRESETS['studio'].copy()
    
    # Calcula médias e desvios
    h_mean = np.mean(green_pixels[:, 0])
    s_mean = np.mean(green_pixels[:, 1])
    v_mean = np.mean(green_pixels[:, 2])
    
    h_std = np.std(green_pixels[:, 0])
    s_std = np.std(green_pixels[:, 1])
    v_std = np.std(green_pixels[:, 2])
    
    # Define ranges baseados em média ± 1.5*desvio
    h_min = max(0, int(h_mean - 1.5 * h_std))
    h_max = min(179, int(h_mean + 1.5 * h_std))
    s_min = max(0, int(s_mean - 1.5 * s_std))
    s_max = 255
    v_min = max(0, int(v_mean - 1.5 * v_std))
    v_max = 255
    
    print(f"Auto-detectado: H={h_min}-{h_max}, S={s_min}-{s_max}, V={v_min}-{v_max}")
    
    return {'h_min': h_min, 'h_max': h_max, 's_min': s_min, 's_max': s_max, 'v_min': v_min, 'v_max': v_max}


def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"Erro: config.ini nao encontrado em: {config_path}", file=sys.stderr)
        return None

    config = configparser.ConfigParser(interpolation=None)

    try:
        config.add_section('Conversor')
        config.set('Conversor', 'luminance_ramp', LUMINANCE_RAMP_DEFAULT)
        config.read(config_path, encoding='utf-8')
        return config
    except Exception as e:
        print(f"Erro ao ler config.ini: {e}", file=sys.stderr)
        return None


def get_initial_values(config):
    defaults = {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255, 'erode': 2, 'dilate': 2}
    if 'ChromaKey' not in config:
        print("Secao [ChromaKey] nao encontrada, usando padroes.")
        return defaults
    try:
        return {
            'h_min': config.getint('ChromaKey', 'h_min', fallback=defaults['h_min']),
            'h_max': config.getint('ChromaKey', 'h_max', fallback=defaults['h_max']),
            's_min': config.getint('ChromaKey', 's_min', fallback=defaults['s_min']),
            's_max': config.getint('ChromaKey', 's_max', fallback=defaults['s_max']),
            'v_min': config.getint('ChromaKey', 'v_min', fallback=defaults['v_min']),
            'v_max': config.getint('ChromaKey', 'v_max', fallback=defaults['v_max']),
            'erode': config.getint('ChromaKey', 'erode', fallback=defaults['erode']),
            'dilate': config.getint('ChromaKey', 'dilate', fallback=defaults['dilate'])
        }
    except Exception as e:
        print(f"Erro ao ler valores [ChromaKey]: {e}. Usando padroes.")
        return defaults


def on_trackbar(val):
    pass


def save_values(trackbar_values):
    global config_global, config_path_global
    if config_global is None or config_path_global is None:
        return

    print("\nSalvando valores...")
    try:
        if 'ChromaKey' not in config_global:
            config_global.add_section('ChromaKey')

        config_global.set('ChromaKey', 'h_min', str(trackbar_values['h_min']))
        config_global.set('ChromaKey', 'h_max', str(trackbar_values['h_max']))
        config_global.set('ChromaKey', 's_min', str(trackbar_values['s_min']))
        config_global.set('ChromaKey', 's_max', str(trackbar_values['s_max']))
        config_global.set('ChromaKey', 'v_min', str(trackbar_values['v_min']))
        config_global.set('ChromaKey', 'v_max', str(trackbar_values['v_max']))
        config_global.set('ChromaKey', 'erode', str(trackbar_values.get('erode', 2)))
        config_global.set('ChromaKey', 'dilate', str(trackbar_values.get('dilate', 2)))

        with open(config_path_global, 'w', encoding='utf-8') as configfile:
            config_global.write(configfile)
        print(f"Valores salvos com sucesso em {config_path_global}")
        print(f"H: {trackbar_values['h_min']}-{trackbar_values['h_max']}, S: {trackbar_values['s_min']}-{trackbar_values['s_max']}, V: {trackbar_values['v_min']}-{trackbar_values['v_max']}")
        print(f"Erode: {trackbar_values.get('erode', 2)}, Dilate: {trackbar_values.get('dilate', 2)}")

    except Exception as e:
        print(f"Erro fatal ao salvar config: {e}", file=sys.stderr)


def reset_defaults():
    defaults = {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255, 'erode': 2, 'dilate': 2}
    print("\nResetando para os valores padrao...")
    cv2.setTrackbarPos("H Min", WINDOW_CONTROLS, defaults['h_min'])
    cv2.setTrackbarPos("H Max", WINDOW_CONTROLS, defaults['h_max'])
    cv2.setTrackbarPos("S Min", WINDOW_CONTROLS, defaults['s_min'])
    cv2.setTrackbarPos("S Max", WINDOW_CONTROLS, defaults['s_max'])
    cv2.setTrackbarPos("V Min", WINDOW_CONTROLS, defaults['v_min'])
    cv2.setTrackbarPos("V Max", WINDOW_CONTROLS, defaults['v_max'])
    cv2.setTrackbarPos("Erode", WINDOW_CONTROLS, defaults['erode'])
    cv2.setTrackbarPos("Dilate", WINDOW_CONTROLS, defaults['dilate'])
    print("Valores resetados. Pressione 's' para salvar se desejar.")


def main():
    global config_global, config_path_global

    parser = argparse.ArgumentParser(description="Calibrador de Chroma Key (OpenCV)")
    parser.add_argument('--config', required=True, help="Caminho para o config.ini")
    parser.add_argument('--video', required=False, default=None, help="Caminho opcional para um video")
    args = parser.parse_args()

    config_path_global = args.config
    config_global = load_config(config_path_global)
    if config_global is None:
        sys.exit(1)

    initial_values = get_initial_values(config_global)

    def reload_converter_config():
        global config_global
        config_global = load_config(config_path_global)
        if config_global is None:
            return None
        
        # Detectar tamanho do terminal
        try:
            term_size = os.get_terminal_size()
            target_width = term_size.columns - 2
            target_height = term_size.lines - 5
        except OSError:
            # Fallback para config.ini
            try:
                target_width = config_global.getint('Conversor', 'target_width')
                target_height = config_global.getint('Conversor', 'target_height')
            except Exception:
                target_width = 180
                target_height = 45
        
        try:
            return {
                'target_width': target_width,
                'target_height': target_height,
                'char_aspect_ratio': 0.48,
                'sobel_threshold': config_global.getint('Conversor', 'sobel_threshold'),
                'luminance_ramp': config_global.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT),
                'sharpen_enabled': config_global.getboolean('Conversor', 'sharpen_enabled', fallback=True),
                'sharpen_amount': config_global.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
            }
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"Aviso: Erro ao ler [Conversor] do config: {e}.")
            return None

    converter_config = reload_converter_config()
    if converter_config is None:
        converter_config = {
            'target_width': 180, 'target_height': 0, 'char_aspect_ratio': 0.48,
            'sobel_threshold': 70, 'luminance_ramp': LUMINANCE_RAMP_DEFAULT,
            'sharpen_enabled': True, 'sharpen_amount': 0.5
        }

    is_video_file = args.video is not None
    capture_source = args.video if is_video_file else 0
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        print(f"Erro: Nao foi possivel abrir a fonte de video: {capture_source}", file=sys.stderr)
        sys.exit(1)
    print(f"Fonte de video aberta: {capture_source}")

    def calculate_target_dimensions(cap, converter_config):
        target_width = converter_config['target_width']
        target_height_config = converter_config['target_height']
        char_aspect_ratio = converter_config['char_aspect_ratio']

        try:
            source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if target_height_config > 0:
                target_height = target_height_config
            else:
                target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
                if target_height <= 0:
                    target_height = int(target_width * (9/16) * char_aspect_ratio)

            return (target_width, max(1, target_height))
        except Exception as e:
            print(f"Aviso: Erro ao calcular dimensoes: {e}")
            return (target_width, 25)

    target_dimensions = calculate_target_dimensions(cap, converter_config)
    print(f"Dimensoes ASCII calculadas: {target_dimensions[0]}x{target_dimensions[1]} chars.")

    cv2.namedWindow(WINDOW_ORIGINAL)
    cv2.namedWindow(WINDOW_RESULT)
    cv2.namedWindow(WINDOW_CONTROLS, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(WINDOW_ORIGINAL, 50, 50)
    cv2.moveWindow(WINDOW_RESULT, 700, 50)
    cv2.moveWindow(WINDOW_CONTROLS, 50, 550)

    cv2.createTrackbar("H Min", WINDOW_CONTROLS, initial_values['h_min'], 179, on_trackbar)
    cv2.createTrackbar("H Max", WINDOW_CONTROLS, initial_values['h_max'], 179, on_trackbar)
    cv2.createTrackbar("S Min", WINDOW_CONTROLS, initial_values['s_min'], 255, on_trackbar)
    cv2.createTrackbar("S Max", WINDOW_CONTROLS, initial_values['s_max'], 255, on_trackbar)
    cv2.createTrackbar("V Min", WINDOW_CONTROLS, initial_values['v_min'], 255, on_trackbar)
    cv2.createTrackbar("V Max", WINDOW_CONTROLS, initial_values['v_max'], 255, on_trackbar)
    cv2.createTrackbar("Erode", WINDOW_CONTROLS, initial_values.get('erode', 2), 10, on_trackbar)
    cv2.createTrackbar("Dilate", WINDOW_CONTROLS, initial_values.get('dilate', 2), 10, on_trackbar)

    print("Controles criados. Loop iniciado.")
    print("COMANDOS:")
    print("  's' : Salvar configuracoes no config.ini")
    print("  'r' : Resetar para valores padrao")
    print("  'a' : Auto-detectar verde do frame atual")
    print("  'p' : Alternar presets (Studio/Natural/Bright/Custom)")
    print("  'g' : Iniciar/Parar GRAVACAO da animacao ASCII")
    print("  'q' : Sair")

    os.system('cls' if os.name == 'nt' else 'clear')

    is_recording = False
    recording_frames = []
    recording_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    
    current_preset_index = 0  # Para ciclar entre presets
    preset_names = ['custom', 'studio', 'natural', 'bright']

    last_config_reload = time.time()
    config_reload_interval = 2.0

    while True:
        ret, frame = cap.read()
        if not ret:
            if is_video_file:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                print("Erro ao ler frame da webcam.", file=sys.stderr)
                break

        if not is_video_file:
            frame = cv2.flip(frame, 1)

        if converter_config.get('sharpen_enabled', True):
            frame = sharpen_frame(frame, converter_config.get('sharpen_amount', 0.5))

        current_time = time.time()
        if current_time - last_config_reload > config_reload_interval:
            new_config = reload_converter_config()
            if new_config is not None:
                converter_config = new_config
                new_dimensions = calculate_target_dimensions(cap, converter_config)
                if new_dimensions != target_dimensions:
                    target_dimensions = new_dimensions
                    os.system('cls' if os.name == 'nt' else 'clear')
            last_config_reload = current_time

        h_min = cv2.getTrackbarPos("H Min", WINDOW_CONTROLS)
        h_max = cv2.getTrackbarPos("H Max", WINDOW_CONTROLS)
        s_min = cv2.getTrackbarPos("S Min", WINDOW_CONTROLS)
        s_max = cv2.getTrackbarPos("S Max", WINDOW_CONTROLS)
        v_min = cv2.getTrackbarPos("V Min", WINDOW_CONTROLS)
        v_max = cv2.getTrackbarPos("V Max", WINDOW_CONTROLS)
        erode_size = cv2.getTrackbarPos("Erode", WINDOW_CONTROLS)
        dilate_size = cv2.getTrackbarPos("Dilate", WINDOW_CONTROLS)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask_original_size = cv2.inRange(hsv, lower, upper)
        
        # Aplica refinamento morfológico para limpar bordas
        mask_original_size = apply_morphological_refinement(mask_original_size, erode_size, dilate_size)
        
        result = cv2.bitwise_and(frame, frame, mask=mask_original_size)

        grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_LANCZOS4)
        resized_color = cv2.resize(frame, target_dimensions, interpolation=cv2.INTER_LANCZOS4)
        resized_mask = cv2.resize(mask_original_size, target_dimensions, interpolation=cv2.INTER_NEAREST)

        sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.hypot(sobel_x, sobel_y)
        angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
        angle = (angle + 180) % 180
        magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        frame_ascii = converter_frame_para_ascii(
            resized_gray, resized_color, resized_mask,
            magnitude_norm, angle,
            converter_config['sobel_threshold'], converter_config['luminance_ramp'],
            output_format="terminal"
        )

        if is_recording:
            frame_for_file = converter_frame_para_ascii(
                resized_gray, resized_color, resized_mask,
                magnitude_norm, angle,
                converter_config['sobel_threshold'], converter_config['luminance_ramp'],
                output_format="file"
            )
            recording_frames.append(frame_for_file)

        display_frame = frame.copy()
        if is_recording:
            cv2.circle(display_frame, (30, 30), 15, (0, 0, 255), -1)
            cv2.putText(display_frame, f"REC ({len(recording_frames)} frames)", (55, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(WINDOW_ORIGINAL, display_frame)
        cv2.imshow(WINDOW_RESULT, result)

        status_line = ""
        if is_recording:
            status_line = f"\n\033[91m[REC] GRAVANDO ({len(recording_frames)} frames) - Pressione 'g' para parar\033[0m"
        sys.stdout.write(ANSI_CLEAR_AND_HOME + frame_ascii + status_line)
        sys.stdout.flush()

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q'):
            print("\nTecla 'q' pressionada. Saindo...")
            break

        if key == ord('s'):
            print("\nTecla 's' pressionada. Salvando...")
            current_values = {
                'h_min': h_min, 'h_max': h_max,
                's_min': s_min, 's_max': s_max,
                'v_min': v_min, 'v_max': v_max,
                'erode': erode_size, 'dilate': dilate_size
            }
            save_values(current_values)

        if key == ord('r'):
            reset_defaults()
        
        if key == ord('a'):
            # Auto-detect verde do frame atual
            print("\nAuto-detectando verde do frame atual...")
            detected_values = auto_detect_green(frame)
            cv2.setTrackbarPos("H Min", WINDOW_CONTROLS, detected_values['h_min'])
            cv2.setTrackbarPos("H Max", WINDOW_CONTROLS, detected_values['h_max'])
            cv2.setTrackbarPos("S Min", WINDOW_CONTROLS, detected_values['s_min'])
            cv2.setTrackbarPos("S Max", WINDOW_CONTROLS, detected_values['s_max'])
            cv2.setTrackbarPos("V Min", WINDOW_CONTROLS, detected_values['v_min'])
            cv2.setTrackbarPos("V Max", WINDOW_CONTROLS, detected_values['v_max'])
            print(f"Valores aplicados: H={detected_values['h_min']}-{detected_values['h_max']}, S={detected_values['s_min']}-{detected_values['s_max']}, V={detected_values['v_min']}-{detected_values['v_max']}")
        
        if key == ord('p'):
            # Cicla entre presets
            current_preset_index = (current_preset_index + 1) % len(preset_names)
            preset_name = preset_names[current_preset_index]
            
            if preset_name == 'custom':
                print("\nPreset: Custom (valores manuais)")
            else:
                preset_values = CHROMA_PRESETS[preset_name]
                print(f"\nPreset: {preset_name.capitalize()}")
                cv2.setTrackbarPos("H Min", WINDOW_CONTROLS, preset_values['h_min'])
                cv2.setTrackbarPos("H Max", WINDOW_CONTROLS, preset_values['h_max'])
                cv2.setTrackbarPos("S Min", WINDOW_CONTROLS, preset_values['s_min'])
                cv2.setTrackbarPos("S Max", WINDOW_CONTROLS, preset_values['s_max'])
                cv2.setTrackbarPos("V Min", WINDOW_CONTROLS, preset_values['v_min'])
                cv2.setTrackbarPos("V Max", WINDOW_CONTROLS, preset_values['v_max'])
                print(f"Valores aplicados: H={preset_values['h_min']}-{preset_values['h_max']}, S={preset_values['s_min']}-{preset_values['s_max']}, V={preset_values['v_min']}-{preset_values['v_max']}")

        if key == ord('g'):
            if not is_recording:
                is_recording = True
                recording_frames = []
                print("\n[REC] GRAVACAO INICIADA! Pressione 'g' novamente para parar e salvar.")
            else:
                is_recording = False
                if len(recording_frames) > 0:
                    output_dir = config_global.get('Pastas', 'output_dir', fallback='videos_saida')
                    if not os.path.isabs(output_dir):
                        config_dir = os.path.dirname(config_path_global)
                        output_dir = os.path.join(config_dir, output_dir)

                    os.makedirs(output_dir, exist_ok=True)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    output_file = os.path.join(output_dir, f"gravacao_{timestamp}.txt")

                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(f"{recording_fps}\n")
                            f.write("[FRAME]\n".join(recording_frames))
                        print(f"\n[OK] GRAVACAO SALVA: {output_file} ({len(recording_frames)} frames)")
                    except Exception as e:
                        print(f"\n[ERRO] Erro ao salvar gravacao: {e}")
                else:
                    print("\n[AVISO] Nenhum frame gravado.")
                recording_frames = []

        try:
            if cv2.getWindowProperty(WINDOW_ORIGINAL, cv2.WND_PROP_VISIBLE) < 1:
                break
            if cv2.getWindowProperty(WINDOW_RESULT, cv2.WND_PROP_VISIBLE) < 1:
                break
            if cv2.getWindowProperty(WINDOW_CONTROLS, cv2.WND_PROP_VISIBLE) < 1:
                break
        except cv2.error:
            break

    if is_recording and len(recording_frames) > 0:
        output_dir = config_global.get('Pastas', 'output_dir', fallback='videos_saida')
        if not os.path.isabs(output_dir):
            config_dir = os.path.dirname(config_path_global)
            output_dir = os.path.join(config_dir, output_dir)
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"gravacao_{timestamp}.txt")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{recording_fps}\n")
                f.write("[FRAME]\n".join(recording_frames))
            print(f"\n[OK] Gravacao salva automaticamente: {output_file}")
        except Exception as e:
            print(f"\n[ERRO] Erro ao salvar gravacao: {e}")

    print("\nFinalizando...")
    cap.release()
    cv2.destroyAllWindows()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ANSI_RESET)
    sys.exit(0)


if __name__ == "__main__":
    main()
