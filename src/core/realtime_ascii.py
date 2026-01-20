import cv2
import numpy as np
import os
import sys
import configparser
import argparse
import time

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.core.auto_segmenter import AutoSegmenter, is_available as auto_seg_available
except ImportError as e:
    print(f"Erro ao importar AutoSegmenter: {e}")
    AutoSegmenter = None
    def auto_seg_available(): return False

try:
    from src.core.matrix_rain_gpu import MatrixRainGPU
    MATRIX_RAIN_AVAILABLE = True
except ImportError:
    MATRIX_RAIN_AVAILABLE = False

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except ImportError:
    POSTFX_AVAILABLE = False

ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§"
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"
LUMINANCE_RAMP_DEFAULT = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "


def sharpen_frame(frame, sharpen_amount=0.5):
    if sharpen_amount <= 0:
        return frame
    
    gaussian = cv2.GaussianBlur(frame, (5, 5), 1.0)
    sharpened = cv2.addWeighted(frame, 1.0 + sharpen_amount, gaussian, -sharpen_amount, 0)
    
    return sharpened


def rgb_to_ansi256(r, g, b):
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return 232 + int(((r - 8) / 247) * 23)
    ansi_r = int(r / 255 * 5)
    ansi_g = int(g / 255 * 5)
    ansi_b = int(b / 255 * 5)
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b


def frame_para_ascii_rt(gray_frame, color_frame, magnitude_frame, angle_frame, sobel_threshold, luminance_ramp):
    height, width = gray_frame.shape
    output_buffer = []

    for y in range(height):
        line_buffer = []
        for x in range(width):
            if magnitude_frame[y, x] > sobel_threshold:
                angle = angle_frame[y, x]
                if (angle > 67.5 and angle <= 112.5):
                    char = "|"
                elif (angle > 112.5 and angle <= 157.5):
                    char = "/"
                elif (angle > 157.5 or angle <= 22.5):
                    char = "-"
                else:
                    char = "\\"
                b, g, r = color_frame[y, x]
                ansi_code = rgb_to_ansi256(r, g, b)
            else:
                pixel_brightness = gray_frame[y, x]
                if pixel_brightness == 0 and len(color_frame[y, x]) == 3 and np.array_equal(color_frame[y, x], [0, 0, 0]):
                     # Force background to space if perfectly black (masked)
                     char = " "
                     ansi_code = 232 # Black
                else:
                    char_index = int((pixel_brightness / 255) * (len(luminance_ramp) - 1))
                    char = luminance_ramp[char_index]
                    b, g, r = color_frame[y, x]
                    ansi_code = rgb_to_ansi256(r, g, b)

            if char:
                line_buffer.append(f"\033[38;5;{ansi_code}m{char}")
            else:
                line_buffer.append(" ")

        output_buffer.append("".join(line_buffer))

    return "\n".join(output_buffer) + ANSI_RESET


def apply_chroma_key(frame, hsv_values):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([hsv_values['h_min'], hsv_values['s_min'], hsv_values['v_min']])
    upper = np.array([hsv_values['h_max'], hsv_values['s_max'], hsv_values['v_max']])
    mask = cv2.inRange(hsv, lower, upper)

    kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.erode(mask, kernel_erode, iterations=hsv_values['erode'])
    mask = cv2.dilate(mask, kernel_dilate, iterations=hsv_values['dilate'])

    mask_inv = cv2.bitwise_not(mask)
    result = np.zeros_like(frame)
    result[mask_inv > 0] = frame[mask_inv > 0]

    return result


def run_realtime_ascii(config_path, video_path=None):
    config = configparser.ConfigParser(interpolation=None)

    config.add_section('Conversor')
    config.set('Conversor', 'luminance_ramp', LUMINANCE_RAMP_DEFAULT)

    if not config.read(config_path):
        print(f"Erro fatal: config.ini nao encontrado em {config_path}")
        return

    is_video_file = video_path is not None

    # Load Chroma settings
    chroma_enabled = False
    hsv_values = {}
    if 'ChromaKey' in config:
        try:
            hsv_values = {
                'h_min': config.getint('ChromaKey', 'h_min', fallback=35),
                'h_max': config.getint('ChromaKey', 'h_max', fallback=85),
                's_min': config.getint('ChromaKey', 's_min', fallback=40),
                's_max': config.getint('ChromaKey', 's_max', fallback=255),
                'v_min': config.getint('ChromaKey', 'v_min', fallback=40),
                'v_max': config.getint('ChromaKey', 'v_max', fallback=255),
                'erode': config.getint('ChromaKey', 'erode', fallback=2),
                'dilate': config.getint('ChromaKey', 'dilate', fallback=2)
            }
            chroma_enabled = True
            print(f"Chroma Key ativado: H={hsv_values['h_min']}-{hsv_values['h_max']}")
        except Exception as e:
            print(f"Aviso: Erro ao carregar ChromaKey: {e}")
            chroma_enabled = False

    # Load Auto Segmenter settings
    auto_seg_enabled = False
    segmenter = None
    if config.getboolean('Conversor', 'auto_seg_enabled', fallback=False):
        if auto_seg_available():
            try:
                print("Iniciando Auto Segmentation (MediaPipe)...")
                segmenter = AutoSegmenter(threshold=0.5, use_gpu=True)
                auto_seg_enabled = True
                print("Auto Segmentation ativado.")
            except Exception as e:
                print(f"Erro ao iniciar Auto Segmentation: {e}")
        else:
            print("Auto Segmentation habilitado no config mas nao disponivel (falta mediapipe).")

    # Setup Matrix Rain
    matrix_enabled = config.getboolean('MatrixRain', 'enabled', fallback=False)
    matrix_rain = None
    if matrix_enabled and MATRIX_RAIN_AVAILABLE:
        try:
            print("Iniciando Matrix Rain...")
            charset = config.get('MatrixRain', 'char_set', fallback='katakana')
            mode = config.get('MatrixRain', 'mode', fallback='user')
            particles = config.getint('MatrixRain', 'num_particles', fallback=2000)
            speed = config.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)
            matrix_rain = MatrixRainGPU(width=1280, height=720, char_set=charset)
            matrix_rain.mode = mode
            matrix_rain.num_particles = particles
            matrix_rain.speed_multiplier = speed
            print("Matrix Rain ativado.")
        except Exception as e:
            print(f"Erro ao iniciar Matrix Rain: {e}")

    # Setup PostFX
    postfx = None
    if POSTFX_AVAILABLE:
        try:
            bloom = config.getboolean('PostFX', 'bloom_enabled', fallback=False)
            chromatic = config.getboolean('PostFX', 'chromatic_enabled', fallback=False)
            scanlines = config.getboolean('PostFX', 'scanlines_enabled', fallback=False)
            glitch = config.getboolean('PostFX', 'glitch_enabled', fallback=False)
            
            if bloom or chromatic or scanlines or glitch:
                print("Iniciando PostFX...")
                p_config = PostFXConfig()
                p_config.bloom_enabled = bloom
                p_config.bloom_intensity = config.getfloat('PostFX', 'bloom_intensity', fallback=1.2)
                p_config.bloom_radius = config.getint('PostFX', 'bloom_radius', fallback=20)
                p_config.chromatic_enabled = chromatic
                p_config.chromatic_shift = config.getint('PostFX', 'chromatic_shift', fallback=5)
                p_config.scanlines_enabled = scanlines
                p_config.scanlines_intensity = config.getfloat('PostFX', 'scanlines_intensity', fallback=0.5)
                p_config.glitch_enabled = glitch
                p_config.glitch_intensity = config.getfloat('PostFX', 'glitch_intensity', fallback=0.3)
                
                postfx = PostFXProcessor(config=p_config)
                print("PostFX ativado.")
        except Exception as e:
             print(f"Erro ao iniciar PostFX: {e}")

    # Prioridade para Config do Usuario
    try:
        config_width = config.getint('Conversor', 'target_width', fallback=0)
        config_height = config.getint('Conversor', 'target_height', fallback=0)
        
        target_width = config_width if config_width > 0 else 180
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio', fallback=0.48)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        target_width = 180
        char_aspect_ratio = 0.48
        
    try:
        term_size = os.get_terminal_size()
        terminal_cols = term_size.columns
        terminal_lines = term_size.lines
        print(f"Terminal detectado: {terminal_cols}x{terminal_lines}")
        
        if config_width <= 0:
            target_width = max(40, terminal_cols - 2)
            target_height = max(20, terminal_lines - 5)
            print(f"Usando resolucao maxima do terminal: {target_width}x{target_height}")
        else:
             print(f"Usando resolucao do config: {target_width} (AspectRatio: {char_aspect_ratio})")

    except OSError:
        pass

    try:
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
        luminance_ramp = config.get('Conversor', 'luminance_ramp').rstrip('|')
        
        # Inverter rampa para renderizacao em terminal (Light-on-Dark)
        # Check if user specifically requested NO reversal? Usually terminal is always dark.
        luminance_ramp = luminance_ramp[::-1]

        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Erro ao ler config.ini: {e}. Usando valores padrao.")
        target_width = 180
        char_aspect_ratio = 0.48
        sobel_threshold = 70
        luminance_ramp = LUMINANCE_RAMP_DEFAULT[::-1]

    capture_source = video_path if is_video_file else 0
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        source_name = video_path if is_video_file else "webcam"
        print(f"Erro: Nao foi possivel abrir {source_name}.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    try:
        ret, frame_teste = cap.read()
        if not ret or frame_teste is None:
            raise ValueError("Nao foi possivel ler o primeiro frame.")
        source_height, source_width, _ = frame_teste.shape

        if 'target_height' not in locals() or target_height <= 0:
            target_height = int((target_width * source_height * char_aspect_ratio) / source_width)
            if target_height <= 0:
                target_height = int(target_width * (9/16) * char_aspect_ratio)

        target_dimensions = (target_width, target_height)
        source_name = f"Video: {os.path.basename(video_path)}" if is_video_file else "Webcam"
        print(f"{source_name} detectado: {source_width}x{source_height}. Convertendo para: {target_width}x{target_height} chars.")
        print("Pressione Ctrl+C para sair.")

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    except Exception as e:
        print(f"Erro ao calcular dimensoes: {e}. Usando 80x{int(80*0.45*(9/16))}.")
        target_dimensions = (target_width, int(target_width * 0.45 * (9/16)))

    try:
        while True:
            ret, frame_colorido = cap.read()
            if not ret or frame_colorido is None:
                if is_video_file:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                print("Erro ao ler frame.")
                time.sleep(0.5)
                continue

            if not is_video_file:
                frame_colorido = cv2.flip(frame_colorido, 1)

            if sharpen_enabled:
                frame_colorido = sharpen_frame(frame_colorido, sharpen_amount)

            # Apply Segmentation / Chroma
            mask = None
            if auto_seg_enabled and segmenter:
                # Auto Segmentation
                mask = segmenter.process(frame_colorido)
                # seg_mask: 0=Foreground, 255=Background
                # Set Background to Black
                frame_colorido[mask > 127] = 0
            elif chroma_enabled:
                frame_colorido = apply_chroma_key(frame_colorido, hsv_values)
                # Create mask from chroma result for Matrix Rain if needed
                if matrix_rain:
                    gray_tmp = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
                    _, user_mask_chroma = cv2.threshold(gray_tmp, 10, 255, cv2.THRESH_BINARY)
                    # For Matrix Rain 'user' mode, we usually want mask of USER (255)
                    mask = cv2.bitwise_not(user_mask_chroma) # Hack: invert to match seg mask style?
                    # Wait, Seg Mask: 0=FG, 255=BG. 
                    # Matrix Rain usually expects: None or specific mask dependent on implementation.
                    # Looking at gtk_calibrator logic might be safer, but let's assume standard behavior first.
                    # Actually, for matrix rain 'user' mode, it usually falls BEHIND user.
            
            # Matrix Rain
            if matrix_rain:
                 user_mask_for_rain = None
                 if mask is not None:
                     # If mask has 0 for FG and 255 for BG.
                     # We usually want a mask where 255 is where rain SHOULD NOT be (the user).
                     # Or 255 is where rain SHOULD be. 
                     # Let's assume user_mask needs 255 for User.
                     # Seg Mask: 0=User. So bitwise_not converts 0->255 (User).
                     user_mask_for_rain = cv2.bitwise_not(mask)
                 elif chroma_enabled:
                     # We already computed it above or need to.
                     gray_tmp = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)
                     _, user_mask_for_rain = cv2.threshold(gray_tmp, 1, 255, cv2.THRESH_BINARY)
                 
                 frame_colorido = matrix_rain.render(frame_colorido, user_mask_for_rain)

            # PostFX
            if postfx:
                frame_colorido = postfx.process(frame_colorido)

            grayscale_frame = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2GRAY)

            resized_gray = cv2.resize(grayscale_frame, target_dimensions, interpolation=cv2.INTER_LANCZOS4)
            resized_color = cv2.resize(frame_colorido, target_dimensions, interpolation=cv2.INTER_LANCZOS4)

            sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.hypot(sobel_x, sobel_y)
            angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
            angle = (angle + 180) % 180
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            frame_ascii = frame_para_ascii_rt(
                resized_gray, resized_color, magnitude_norm, angle,
                sobel_threshold, luminance_ramp
            )

            sys.stdout.write(ANSI_CLEAR_AND_HOME + frame_ascii)
            sys.stdout.flush()

            time.sleep(1.0 / fps)

    except KeyboardInterrupt:
        print("\nSaindo do modo Real-Time...")
    except Exception as e:
        print(f"\nErro inesperado no loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if segmenter: segmenter.close()
        if matrix_rain: matrix_rain.close()
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        time.sleep(0.3)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(ANSI_RESET)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conversor Video/Webcam -> ASCII em Tempo Real")
    parser.add_argument("--config", required=True, help="Caminho para o config.ini.")
    parser.add_argument("--video", required=False, default=None, help="Caminho para arquivo de video (opcional).")
    args = parser.parse_args()

    run_realtime_ascii(config_path=args.config, video_path=args.video)
