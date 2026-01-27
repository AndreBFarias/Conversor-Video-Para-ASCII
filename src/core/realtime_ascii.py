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


def rgb_to_truecolor(r, g, b):
    """24-bit true color ANSI escape - preserves full RGB"""
    return f"\033[38;2;{r};{g};{b}m"


def frame_para_ascii_rt(gray_frame, color_frame, magnitude_frame, angle_frame, sobel_threshold, luminance_ramp,
                        edge_boost_enabled=False, edge_boost_amount=100, use_edge_chars=True, use_truecolor=True):
    height, width = gray_frame.shape
    output_buffer = []
    ramp_len = len(luminance_ramp)

    is_edge = magnitude_frame > sobel_threshold

    if edge_boost_enabled:
        brightness = gray_frame.astype(np.int32)
        edge_boost = is_edge.astype(np.int32) * edge_boost_amount
        brightness = np.clip(brightness + edge_boost, 0, 255).astype(np.uint8)
    else:
        brightness = gray_frame

    for y in range(height):
        line_buffer = []
        for x in range(width):
            if use_edge_chars and is_edge[y, x]:
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
            else:
                pixel_brightness = brightness[y, x]
                if pixel_brightness == 0 and len(color_frame[y, x]) == 3 and np.array_equal(color_frame[y, x], [0, 0, 0]):
                    char = " "
                    r, g, b = 0, 0, 0
                else:
                    char_index = int((pixel_brightness / 255) * (ramp_len - 1))
                    char = luminance_ramp[char_index]
                    b, g, r = color_frame[y, x]

            if char:
                if use_truecolor:
                    line_buffer.append(f"\033[38;2;{r};{g};{b}m{char}")
                else:
                    ansi_code = rgb_to_ansi256(r, g, b)
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


def run_realtime_ascii(config_path, video_path=None, overrides=None):
    config = configparser.ConfigParser(interpolation=None)

    config.add_section('Conversor')
    config.set('Conversor', 'luminance_ramp', LUMINANCE_RAMP_DEFAULT)

    if not config.read(config_path):
        print(f"Erro fatal: config.ini nao encontrado em {config_path}")
        return

    if overrides:
        print(f"Overrides recebidos: {list(overrides.keys())}")

    is_video_file = video_path is not None

    # Load Chroma settings (com overrides)
    chroma_enabled = False
    hsv_values = {}
    if 'ChromaKey' in config:
        try:
            hsv_values = {
                'h_min': overrides.get('h_min') if overrides and 'h_min' in overrides else config.getint('ChromaKey', 'h_min', fallback=35),
                'h_max': overrides.get('h_max') if overrides and 'h_max' in overrides else config.getint('ChromaKey', 'h_max', fallback=85),
                's_min': overrides.get('s_min') if overrides and 's_min' in overrides else config.getint('ChromaKey', 's_min', fallback=40),
                's_max': overrides.get('s_max') if overrides and 's_max' in overrides else config.getint('ChromaKey', 's_max', fallback=255),
                'v_min': overrides.get('v_min') if overrides and 'v_min' in overrides else config.getint('ChromaKey', 'v_min', fallback=40),
                'v_max': overrides.get('v_max') if overrides and 'v_max' in overrides else config.getint('ChromaKey', 'v_max', fallback=255),
                'erode': overrides.get('erode') if overrides and 'erode' in overrides else config.getint('ChromaKey', 'erode', fallback=2),
                'dilate': overrides.get('dilate') if overrides and 'dilate' in overrides else config.getint('ChromaKey', 'dilate', fallback=2)
            }
            chroma_enabled = True
            print(f"Chroma Key ativado: H={hsv_values['h_min']}-{hsv_values['h_max']}")
        except Exception as e:
            print(f"Aviso: Erro ao carregar ChromaKey: {e}")
            chroma_enabled = False

    # Load Auto Segmenter settings (com override)
    auto_seg_enabled = False
    segmenter = None
    auto_seg_from_override = overrides.get('auto_seg_enabled') if overrides else None
    auto_seg_from_config = config.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
    should_enable_auto_seg = auto_seg_from_override if auto_seg_from_override is not None else auto_seg_from_config

    if should_enable_auto_seg:
        if auto_seg_available():
            try:
                print("Iniciando Auto Segmentation (MediaPipe)...")
                segmenter = AutoSegmenter(threshold=0.5, use_gpu=True)
                auto_seg_enabled = True
                print("Auto Segmentation ativado.")
            except Exception as e:
                print(f"Erro ao iniciar Auto Segmentation: {e}")
        else:
            print("Auto Segmentation habilitado mas nao disponivel (falta mediapipe).")

    # Load Temporal Coherence settings (com overrides)
    temporal_from_override = overrides.get('temporal_enabled') if overrides else None
    temporal_from_config = config.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
    temporal_enabled = temporal_from_override if temporal_from_override is not None else temporal_from_config

    temporal_threshold = overrides.get('temporal_threshold') if overrides and 'temporal_threshold' in overrides else config.getint('Conversor', 'temporal_threshold', fallback=50)
    prev_gray_frame = None
    if temporal_enabled:
        print(f"Temporal Coherence ativado: threshold={temporal_threshold}")

    # Setup Matrix Rain (com overrides)
    matrix_from_override = overrides.get('matrix_enabled') if overrides else None
    matrix_from_config = config.getboolean('MatrixRain', 'enabled', fallback=False)
    matrix_enabled = matrix_from_override if matrix_from_override is not None else matrix_from_config

    matrix_rain = None
    matrix_mode = 'user'
    if matrix_enabled and MATRIX_RAIN_AVAILABLE:
        try:
            print("Iniciando Matrix Rain...")
            charset = overrides.get('matrix_charset') if overrides and 'matrix_charset' in overrides else config.get('MatrixRain', 'char_set', fallback='katakana')
            matrix_mode = overrides.get('matrix_mode') if overrides and 'matrix_mode' in overrides else config.get('MatrixRain', 'mode', fallback='user')
            particles = overrides.get('matrix_particles') if overrides and 'matrix_particles' in overrides else config.getint('MatrixRain', 'num_particles', fallback=2000)
            speed = overrides.get('matrix_speed') if overrides and 'matrix_speed' in overrides else config.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)
            matrix_rain = MatrixRainGPU(width=1280, height=720, char_set=charset)
            matrix_rain.mode = matrix_mode
            matrix_rain.num_particles = particles
            matrix_rain.speed_multiplier = speed
            print(f"Matrix Rain ativado: mode={matrix_mode}, charset={charset}, particles={particles}")
        except Exception as e:
            print(f"Erro ao iniciar Matrix Rain: {e}")

    # Setup PostFX (com overrides)
    postfx = None
    if POSTFX_AVAILABLE:
        try:
            bloom = overrides.get('bloom_enabled') if overrides and 'bloom_enabled' in overrides else config.getboolean('PostFX', 'bloom_enabled', fallback=False)
            chromatic = overrides.get('chromatic_enabled') if overrides and 'chromatic_enabled' in overrides else config.getboolean('PostFX', 'chromatic_enabled', fallback=False)
            scanlines = overrides.get('scanlines_enabled') if overrides and 'scanlines_enabled' in overrides else config.getboolean('PostFX', 'scanlines_enabled', fallback=False)
            glitch = overrides.get('glitch_enabled') if overrides and 'glitch_enabled' in overrides else config.getboolean('PostFX', 'glitch_enabled', fallback=False)

            if bloom or chromatic or scanlines or glitch:
                print(f"Iniciando PostFX: bloom={bloom}, chromatic={chromatic}, scanlines={scanlines}, glitch={glitch}")
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

    # Prioridade para Overrides > Config > Terminal
    override_width = overrides.get('target_width') if overrides else None
    override_height = overrides.get('target_height') if overrides else None

    try:
        config_width = config.getint('Conversor', 'target_width', fallback=0)
        config_height = config.getint('Conversor', 'target_height', fallback=0)
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio', fallback=0.48)
    except (configparser.NoSectionError, configparser.NoOptionError):
        config_width = 0
        config_height = 0
        char_aspect_ratio = 0.48

    if override_width is not None:
        target_width = override_width
        target_height = override_height if override_height else int(override_width * 0.45 * char_aspect_ratio)
        print(f"Usando resolucao do calibrador: {target_width}x{target_height}")
    elif config_width > 0:
        target_width = config_width
        target_height = config_height if config_height > 0 else int(config_width * 0.45 * char_aspect_ratio)
        print(f"Usando resolucao do config: {target_width}x{target_height}")
    else:
        try:
            term_size = os.get_terminal_size()
            target_width = max(40, term_size.columns - 2)
            target_height = max(20, term_size.lines - 5)
            print(f"Usando resolucao do terminal: {target_width}x{target_height}")
        except OSError:
            target_width = 180
            target_height = int(180 * 0.45 * char_aspect_ratio)

    # Sobel, Sharpen, Edge Boost, Temporal (com overrides)
    sobel_threshold = overrides.get('sobel_threshold') if overrides and 'sobel_threshold' in overrides else config.getint('Conversor', 'sobel_threshold', fallback=70)
    luminance_ramp = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')[::-1]

    sharpen_enabled = overrides.get('sharpen_enabled') if overrides and 'sharpen_enabled' in overrides else config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
    sharpen_amount = overrides.get('sharpen_amount') if overrides and 'sharpen_amount' in overrides else config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)

    edge_boost_enabled = overrides.get('edge_boost_enabled') if overrides and 'edge_boost_enabled' in overrides else config.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
    edge_boost_amount = overrides.get('edge_boost_amount') if overrides and 'edge_boost_amount' in overrides else config.getint('Conversor', 'edge_boost_amount', fallback=100)
    use_edge_chars = overrides.get('use_edge_chars') if overrides and 'use_edge_chars' in overrides else config.getboolean('Conversor', 'use_edge_chars', fallback=True)

    if edge_boost_enabled:
        print(f"Edge Boost ativado: {edge_boost_amount}")

    # Render Target (user/background/both)
    render_target = overrides.get('render_target') if overrides and 'render_target' in overrides else config.get('Conversor', 'render_mode', fallback='both')
    if render_target not in ('user', 'background', 'both'):
        render_target = 'both'
    print(f"Render target: {render_target}")

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
                # seg_mask: 0=Foreground/User, 255=Background
            elif chroma_enabled:
                # Create mask from chroma BEFORE applying it
                hsv = cv2.cvtColor(frame_colorido, cv2.COLOR_BGR2HSV)
                lower = np.array([hsv_values['h_min'], hsv_values['s_min'], hsv_values['v_min']])
                upper = np.array([hsv_values['h_max'], hsv_values['s_max'], hsv_values['v_max']])
                mask = cv2.inRange(hsv, lower, upper)
                # mask: 255=is_chroma (background), 0=not_chroma (user)
                kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                mask = cv2.erode(mask, kernel_erode, iterations=hsv_values['erode'])
                mask = cv2.dilate(mask, kernel_dilate, iterations=hsv_values['dilate'])

            # Apply render_target filtering
            # mask convention: 0=User/Foreground, 255=Background/Chroma
            if mask is not None:
                if render_target == 'user':
                    # Keep only user (where mask==0), set background to black
                    frame_colorido[mask > 127] = 0
                elif render_target == 'background':
                    # Keep only background (where mask==255), set user to black
                    frame_colorido[mask < 128] = 0
                # else 'both': keep everything, no filtering
            
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

            if temporal_enabled and prev_gray_frame is not None:
                diff = np.abs(resized_gray.astype(np.int32) - prev_gray_frame.astype(np.int32))
                temporal_mask = diff < temporal_threshold
                resized_gray = np.where(temporal_mask, prev_gray_frame, resized_gray).astype(np.uint8)

            prev_gray_frame = resized_gray.copy()

            sobel_x = cv2.Sobel(resized_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(resized_gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.hypot(sobel_x, sobel_y)
            angle = np.arctan2(sobel_y, sobel_x) * (180 / np.pi)
            angle = (angle + 180) % 180
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            frame_ascii = frame_para_ascii_rt(
                resized_gray, resized_color, magnitude_norm, angle,
                sobel_threshold, luminance_ramp,
                edge_boost_enabled, edge_boost_amount, use_edge_chars
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

    parser.add_argument("--h-min", type=int, default=None, help="HSV H min override")
    parser.add_argument("--h-max", type=int, default=None, help="HSV H max override")
    parser.add_argument("--s-min", type=int, default=None, help="HSV S min override")
    parser.add_argument("--s-max", type=int, default=None, help="HSV S max override")
    parser.add_argument("--v-min", type=int, default=None, help="HSV V min override")
    parser.add_argument("--v-max", type=int, default=None, help="HSV V max override")
    parser.add_argument("--erode", type=int, default=None, help="Erode override")
    parser.add_argument("--dilate", type=int, default=None, help="Dilate override")

    parser.add_argument("--auto-seg", type=lambda x: x.lower() == 'true', default=None, help="AutoSeg enabled (true/false)")
    parser.add_argument("--matrix-enabled", type=lambda x: x.lower() == 'true', default=None, help="Matrix Rain enabled")
    parser.add_argument("--matrix-mode", type=str, default=None, help="Matrix mode (user/background)")
    parser.add_argument("--matrix-charset", type=str, default=None, help="Matrix charset")
    parser.add_argument("--matrix-particles", type=int, default=None, help="Matrix particles count")
    parser.add_argument("--matrix-speed", type=float, default=None, help="Matrix speed multiplier")

    parser.add_argument("--bloom", type=lambda x: x.lower() == 'true', default=None, help="Bloom enabled")
    parser.add_argument("--chromatic", type=lambda x: x.lower() == 'true', default=None, help="Chromatic enabled")
    parser.add_argument("--scanlines", type=lambda x: x.lower() == 'true', default=None, help="Scanlines enabled")
    parser.add_argument("--glitch", type=lambda x: x.lower() == 'true', default=None, help="Glitch enabled")

    parser.add_argument("--render-mode", type=str, default=None, help="Render mode: ascii or pixelart")
    parser.add_argument("--render-target", type=str, default=None, help="Render target: user, background, or both")
    parser.add_argument("--width", type=int, default=None, help="Target width override")
    parser.add_argument("--height", type=int, default=None, help="Target height override")
    parser.add_argument("--sobel", type=int, default=None, help="Sobel threshold override")
    parser.add_argument("--sharpen", type=lambda x: x.lower() == 'true', default=None, help="Sharpen enabled")
    parser.add_argument("--sharpen-amount", type=float, default=None, help="Sharpen amount")
    parser.add_argument("--edge-boost", type=lambda x: x.lower() == 'true', default=None, help="Edge boost enabled")
    parser.add_argument("--edge-boost-amount", type=int, default=None, help="Edge boost amount")
    parser.add_argument("--edge-chars", type=lambda x: x.lower() == 'true', default=None, help="Use edge chars")
    parser.add_argument("--temporal", type=lambda x: x.lower() == 'true', default=None, help="Temporal coherence enabled")
    parser.add_argument("--temporal-threshold", type=int, default=None, help="Temporal threshold")
    parser.add_argument("--pixel-size", type=int, default=None, help="Pixel art pixel size")
    parser.add_argument("--palette-size", type=int, default=None, help="Pixel art palette size")
    parser.add_argument("--fixed-palette", type=lambda x: x.lower() == 'true', default=None, help="Use fixed palette")

    args = parser.parse_args()

    overrides = {}
    if args.h_min is not None:
        overrides['h_min'] = args.h_min
    if args.h_max is not None:
        overrides['h_max'] = args.h_max
    if args.s_min is not None:
        overrides['s_min'] = args.s_min
    if args.s_max is not None:
        overrides['s_max'] = args.s_max
    if args.v_min is not None:
        overrides['v_min'] = args.v_min
    if args.v_max is not None:
        overrides['v_max'] = args.v_max
    if args.erode is not None:
        overrides['erode'] = args.erode
    if args.dilate is not None:
        overrides['dilate'] = args.dilate
    if args.auto_seg is not None:
        overrides['auto_seg_enabled'] = args.auto_seg
    if args.matrix_enabled is not None:
        overrides['matrix_enabled'] = args.matrix_enabled
    if args.matrix_mode is not None:
        overrides['matrix_mode'] = args.matrix_mode
    if args.matrix_charset is not None:
        overrides['matrix_charset'] = args.matrix_charset
    if args.matrix_particles is not None:
        overrides['matrix_particles'] = args.matrix_particles
    if args.matrix_speed is not None:
        overrides['matrix_speed'] = args.matrix_speed
    if args.bloom is not None:
        overrides['bloom_enabled'] = args.bloom
    if args.chromatic is not None:
        overrides['chromatic_enabled'] = args.chromatic
    if args.scanlines is not None:
        overrides['scanlines_enabled'] = args.scanlines
    if args.glitch is not None:
        overrides['glitch_enabled'] = args.glitch
    if args.render_mode is not None:
        overrides['render_mode'] = args.render_mode
    if args.render_target is not None:
        overrides['render_target'] = args.render_target
    if args.width is not None:
        overrides['target_width'] = args.width
    if args.height is not None:
        overrides['target_height'] = args.height
    if args.sobel is not None:
        overrides['sobel_threshold'] = args.sobel
    if args.sharpen is not None:
        overrides['sharpen_enabled'] = args.sharpen
    if args.sharpen_amount is not None:
        overrides['sharpen_amount'] = args.sharpen_amount
    if args.edge_boost is not None:
        overrides['edge_boost_enabled'] = args.edge_boost
    if args.edge_boost_amount is not None:
        overrides['edge_boost_amount'] = args.edge_boost_amount
    if args.edge_chars is not None:
        overrides['use_edge_chars'] = args.edge_chars
    if args.temporal is not None:
        overrides['temporal_enabled'] = args.temporal
    if args.temporal_threshold is not None:
        overrides['temporal_threshold'] = args.temporal_threshold
    if args.pixel_size is not None:
        overrides['pixel_size'] = args.pixel_size
    if args.palette_size is not None:
        overrides['palette_size'] = args.palette_size
    if args.fixed_palette is not None:
        overrides['fixed_palette'] = args.fixed_palette

    run_realtime_ascii(config_path=args.config, video_path=args.video, overrides=overrides if overrides else None)
