#!/usr/bin/env python3
import cv2
import numpy as np
import cupy as cp
import os
import sys
import configparser
import subprocess
import shutil
import tempfile
import pickle
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.utils.ascii_converter import LUMINANCE_RAMP_DEFAULT, COLOR_SEPARATOR
from src.core.renderer import ASCII_FONT, ASCII_FONT_SCALE, ASCII_FONT_THICKNESS, ASCII_CHAR_WIDTH, ASCII_CHAR_HEIGHT
from src.core.utils import color as color_module
from src.core.utils.color import rgb_to_ansi256_vectorized
from src.app.constants import USER_CACHE_DIR

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except ImportError:
    POSTFX_AVAILABLE = False


def _load_postfx_config(config: configparser.ConfigParser) -> 'PostFXConfig':
    if not POSTFX_AVAILABLE:
        return None

    return PostFXConfig(
        bloom_enabled=config.getboolean('PostFX', 'bloom_enabled', fallback=False),
        bloom_intensity=config.getfloat('PostFX', 'bloom_intensity', fallback=1.2),
        bloom_radius=config.getint('PostFX', 'bloom_radius', fallback=21),
        bloom_threshold=config.getint('PostFX', 'bloom_threshold', fallback=80),
        chromatic_enabled=config.getboolean('PostFX', 'chromatic_enabled', fallback=False),
        chromatic_shift=config.getint('PostFX', 'chromatic_shift', fallback=12),
        scanlines_enabled=config.getboolean('PostFX', 'scanlines_enabled', fallback=False),
        scanlines_intensity=config.getfloat('PostFX', 'scanlines_intensity', fallback=0.7),
        scanlines_spacing=config.getint('PostFX', 'scanlines_spacing', fallback=2),
        glitch_enabled=config.getboolean('PostFX', 'glitch_enabled', fallback=False),
        glitch_intensity=config.getfloat('PostFX', 'glitch_intensity', fallback=0.6),
        glitch_block_size=config.getint('PostFX', 'glitch_block_size', fallback=8)
    )

RENDER_KERNEL = cp.RawKernel(r'''
extern "C" __global__
void render_ascii(
    const int* char_indices,
    const int* color_codes,
    const unsigned char* atlas,
    unsigned char* output,
    int grid_w, int grid_h,
    int char_w, int char_h,
    int n_chars,
    const unsigned char* palette
) {
    int px = blockDim.x * blockIdx.x + threadIdx.x;
    int py = blockDim.y * blockIdx.y + threadIdx.y;
    int out_w = grid_w * char_w;
    int out_h = grid_h * char_h;

    if (px >= out_w || py >= out_h) return;

    int gx = px / char_w;
    int gy = py / char_h;

    int lx = px % char_w;
    int ly = py % char_h;

    int char_idx = char_indices[gy * grid_w + gx];
    if (char_idx < 0 || char_idx >= n_chars) char_idx = 0;

    int atlas_offset = (char_idx * char_h * char_w) + (ly * char_w) + lx;
    unsigned char val = atlas[atlas_offset];

    int color_code = color_codes[gy * grid_w + gx];
    if (color_code < 0) color_code = 0;
    if (color_code > 255) color_code = 255;

    unsigned char b = palette[color_code * 3 + 0];
    unsigned char g = palette[color_code * 3 + 1];
    unsigned char r = palette[color_code * 3 + 2];

    int out_idx = (py * out_w + px) * 3;

    if (val > 0) {
        output[out_idx + 0] = (unsigned char)((int)b * val / 255);
        output[out_idx + 1] = (unsigned char)((int)g * val / 255);
        output[out_idx + 2] = (unsigned char)((int)r * val / 255);
    } else {
        output[out_idx + 0] = 0;
        output[out_idx + 1] = 0;
        output[out_idx + 2] = 0;
    }
}
''', 'render_ascii')

MATCH_KERNEL = cp.RawKernel(r'''
extern "C" __global__
void match_texture_mse(
    const unsigned char* input_image,
    const unsigned char* atlas,
    int* output_indices,
    int grid_w, int grid_h,
    int char_w, int char_h,
    int n_chars,
    int stride_input
) {
    int gx = blockDim.x * blockIdx.x + threadIdx.x;
    int gy = blockDim.y * blockIdx.y + threadIdx.y;

    if (gx >= grid_w || gy >= grid_h) return;

    int best_char = 32;
    float min_mse = 9999999.0f;

    int base_input_y = gy * char_h;
    int base_input_x = gx * char_w;

    for (int c = 0; c < n_chars; c++) {
        float current_mse = 0.0f;
        int atlas_base = c * char_h * char_w;

        for (int y = 0; y < char_h; y++) {
            for (int x = 0; x < char_w; x++) {
                int in_idx = (base_input_y + y) * stride_input + (base_input_x + x);
                unsigned char p_in = input_image[in_idx];
                unsigned char p_atlas = atlas[atlas_base + y * char_w + x];

                float diff = (float)p_in - (float)p_atlas;
                current_mse += diff * diff;
            }
        }

        if (current_mse < min_mse) {
            min_mse = current_mse;
            best_char = c;
        }
    }

    output_indices[gy * grid_w + gx] = best_char;
}
''', 'match_texture_mse')

BRAILLE_KERNEL = cp.RawKernel(r'''
extern "C" __global__
void convert_to_braille(
    const unsigned char* gray_image,
    int* braille_output,
    int img_w, int img_h,
    int grid_w, int grid_h,
    unsigned char threshold
) {
    int cx = blockDim.x * blockIdx.x + threadIdx.x;
    int cy = blockDim.y * blockIdx.y + threadIdx.y;

    if (cx >= grid_w || cy >= grid_h) return;

    int base_x = cx * 2;
    int base_y = cy * 4;

    if (base_x + 1 >= img_w || base_y + 3 >= img_h) {
        braille_output[cy * grid_w + cx] = 0x2800;
        return;
    }

    int braille_code = 0x2800;

    unsigned char p0 = gray_image[(base_y + 0) * img_w + (base_x + 0)];
    unsigned char p1 = gray_image[(base_y + 1) * img_w + (base_x + 0)];
    unsigned char p2 = gray_image[(base_y + 2) * img_w + (base_x + 0)];
    unsigned char p3 = gray_image[(base_y + 0) * img_w + (base_x + 1)];
    unsigned char p4 = gray_image[(base_y + 1) * img_w + (base_x + 1)];
    unsigned char p5 = gray_image[(base_y + 2) * img_w + (base_x + 1)];
    unsigned char p6 = gray_image[(base_y + 3) * img_w + (base_x + 0)];
    unsigned char p7 = gray_image[(base_y + 3) * img_w + (base_x + 1)];

    if (p0 < threshold) braille_code |= 0x01;
    if (p1 < threshold) braille_code |= 0x02;
    if (p2 < threshold) braille_code |= 0x04;
    if (p3 < threshold) braille_code |= 0x08;
    if (p4 < threshold) braille_code |= 0x10;
    if (p5 < threshold) braille_code |= 0x20;
    if (p6 < threshold) braille_code |= 0x40;
    if (p7 < threshold) braille_code |= 0x80;

    braille_output[cy * grid_w + cx] = braille_code;
}
''', 'convert_to_braille')

TEMPORAL_COHERENCE_KERNEL = cp.RawKernel(r'''
extern "C" __global__
void apply_temporal_coherence(
    const int* char_indices_current,
    const int* char_indices_previous,
    const unsigned char* gray_current,
    const unsigned char* gray_previous,
    int* char_indices_output,
    int w, int h,
    int threshold
) {
    int x = blockDim.x * blockIdx.x + threadIdx.x;
    int y = blockDim.y * blockIdx.y + threadIdx.y;

    if (x >= w || y >= h) return;

    int idx = y * w + x;

    unsigned char curr_lum = gray_current[idx];
    unsigned char prev_lum = gray_previous[idx];

    int diff = curr_lum > prev_lum ? curr_lum - prev_lum : prev_lum - curr_lum;

    if (diff < threshold) {
        char_indices_output[idx] = char_indices_previous[idx];
    } else {
        char_indices_output[idx] = char_indices_current[idx];
    }
}
''', 'apply_temporal_coherence')

def generate_atlas_cpu():
    cache_dir = USER_CACHE_DIR
    cache_file = os.path.join(cache_dir, 'gpu_atlas.pkl')

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                atlas = pickle.load(f)
            print(f"Atlas carregado do cache: {cache_file}")
            return atlas
        except Exception as e:
            print(f"Erro ao carregar cache, regenerando: {e}")

    print("Gerando atlas de caracteres...")
    chars = [chr(i) for i in range(256)]
    atlas_h = ASCII_CHAR_HEIGHT
    atlas_w = ASCII_CHAR_WIDTH

    atlas = np.zeros((256, atlas_h, atlas_w), dtype=np.uint8)

    for i, char in enumerate(chars):
        if not char.isprintable() and i != 32:
             pass

        img = np.zeros((atlas_h, atlas_w), dtype=np.uint8)

        if char.strip():
             text_y = atlas_h - 4
             cv2.putText(img, char, (0, text_y), ASCII_FONT, ASCII_FONT_SCALE, 255, ASCII_FONT_THICKNESS, cv2.LINE_AA)
        elif i == 32:
             pass

        atlas[i] = img

    os.makedirs(cache_dir, exist_ok=True)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(atlas, f)
        print(f"Atlas salvo em cache: {cache_file}")
    except Exception as e:
        print(f"Erro ao salvar cache: {e}")

    return atlas

def generate_braille_atlas_cpu():
    cache_dir = USER_CACHE_DIR
    cache_file = os.path.join(cache_dir, 'gpu_braille_atlas.pkl')

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                atlas = pickle.load(f)
            print(f"Braille atlas carregado do cache: {cache_file}")
            return atlas
        except Exception as e:
            print(f"Erro ao carregar braille cache, regenerando: {e}")

    print("Gerando atlas Braille (256 padroes)...")
    atlas_h = ASCII_CHAR_HEIGHT
    atlas_w = ASCII_CHAR_WIDTH
    atlas = np.zeros((256, atlas_h, atlas_w), dtype=np.uint8)

    for i in range(256):
        braille_char = chr(0x2800 + i)
        img = np.zeros((atlas_h, atlas_w), dtype=np.uint8)

        try:
            text_y = atlas_h - 4
            cv2.putText(img, braille_char, (0, text_y), ASCII_FONT, ASCII_FONT_SCALE, 255, ASCII_FONT_THICKNESS, cv2.LINE_AA)
        except:
            pass

        atlas[i] = img

    os.makedirs(cache_dir, exist_ok=True)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(atlas, f)
        print(f"Braille atlas salvo em cache: {cache_file}")
    except Exception as e:
        print(f"Erro ao salvar braille cache: {e}")

    return atlas

def generate_palette_cpu():
    palette = np.zeros((256, 3), dtype=np.uint8)

    from src.core.renderer import ansi256_to_bgr
    for i in range(256):
        b, g, r = ansi256_to_bgr(i)
        palette[i] = [b, g, r]

    return palette

class GPUConverter:
    def __init__(
        self,
        target_width,
        target_height,
        braille_enabled=False,
        temporal_coherence=False,
        matrix_rain_enabled=False,
        matrix_num_particles=5000,
        matrix_char_set='katakana',
        matrix_speed=1.0,
        luminance_ramp=None
    ):
        print("Inicializando GPU Converter (Cupy)...")

        if luminance_ramp is None:
            luminance_ramp = LUMINANCE_RAMP_DEFAULT
        ramp_array = np.array([ord(c) for c in luminance_ramp], dtype=np.int32)
        self.ramp_gpu = cp.array(ramp_array)
        self.renderer_module = color_module
        self.target_width = target_width
        self.target_height = target_height
        self.braille_enabled = braille_enabled
        self.temporal_coherence = temporal_coherence
        self.matrix_rain_enabled = matrix_rain_enabled

        if braille_enabled:
            print("Modo Braille Ativado: Resolucao 4x maior")
            self.atlas_cpu = generate_braille_atlas_cpu()
        else:
            self.atlas_cpu = generate_atlas_cpu()

        self.palette_cpu = generate_palette_cpu()

        self.atlas_gpu = cp.array(self.atlas_cpu, dtype=cp.uint8)
        self.palette_gpu = cp.array(self.palette_cpu, dtype=cp.uint8)

        self.char_w = ASCII_CHAR_WIDTH
        self.char_h = ASCII_CHAR_HEIGHT
        self.n_chars = 256

        self.out_w = target_width * ASCII_CHAR_WIDTH
        self.out_h = target_height * ASCII_CHAR_HEIGHT

        self.block = (16, 16)
        self.grid = ((self.out_w + self.block[0] - 1) // self.block[0],
                     (self.out_h + self.block[1] - 1) // self.block[1])

        self.match_block = (16, 16)
        self.match_grid = ((target_width + self.match_block[0] - 1) // self.match_block[0],
                           (target_height + self.match_block[1] - 1) // self.match_block[1])

        self.output_buffer_gpu = cp.zeros((self.out_h, self.out_w, 3), dtype=cp.uint8)
        print(f"GPU Memory pooling: Pre-allocated {self.out_w}x{self.out_h}x3 buffer")

        if temporal_coherence:
            print("Temporal Coherence Ativado: Anti-flicker")
            self.prev_char_indices = None
            self.prev_gray = None
        else:
            self.prev_char_indices = None
            self.prev_gray = None

        if matrix_rain_enabled:
            print(f"Matrix Rain: Tentando inicializar {matrix_num_particles} particulas (char_set={matrix_char_set})")
            try:
                from .matrix_rain_gpu import MatrixRainGPU
                self.matrix_rain = MatrixRainGPU(
                    target_width,
                    target_height,
                    num_particles=matrix_num_particles,
                    char_set=matrix_char_set,
                    speed_multiplier=matrix_speed
                )
                print("Matrix Rain inicializado com sucesso")
            except Exception as e:
                print(f"AVISO: Matrix Rain desabilitado (erro ao inicializar): {e}")
                self.matrix_rain = None
        else:
            self.matrix_rain = None

    def render_high_fidelity(self, input_gray_gpu):
        char_indices = cp.zeros((self.target_height, self.target_width), dtype=cp.int32)
        stride = input_gray_gpu.shape[1]

        MATCH_KERNEL(
            self.match_grid, self.match_block,
            (
                input_gray_gpu,
                self.atlas_gpu,
                char_indices,
                self.target_width, self.target_height,
                self.char_w, self.char_h,
                self.n_chars,
                stride
            )
        )
        return char_indices

    def convert_to_braille(self, gray_gpu, threshold=128):
        img_h, img_w = gray_gpu.shape
        grid_w = img_w // 2
        grid_h = img_h // 4

        braille_indices = cp.zeros((grid_h, grid_w), dtype=cp.int32)

        braille_block = (16, 16)
        braille_grid = ((grid_w + braille_block[0] - 1) // braille_block[0],
                        (grid_h + braille_block[1] - 1) // braille_block[1])

        BRAILLE_KERNEL(
            braille_grid, braille_block,
            (
                gray_gpu,
                braille_indices,
                img_w, img_h,
                grid_w, grid_h,
                threshold
            )
        )

        braille_indices_base = braille_indices - 0x2800
        braille_indices_base = cp.clip(braille_indices_base, 0, 255)

        return braille_indices_base.astype(cp.int32)

    def apply_temporal_coherence(self, char_indices_gpu, gray_gpu, threshold=20):
        if self.prev_char_indices is None or self.prev_gray is None:
            self.prev_char_indices = char_indices_gpu.copy()
            self.prev_gray = gray_gpu.copy()
            return char_indices_gpu

        h, w = char_indices_gpu.shape
        output_indices = cp.zeros_like(char_indices_gpu)

        temp_block = (16, 16)
        temp_grid = ((w + temp_block[0] - 1) // temp_block[0],
                     (h + temp_block[1] - 1) // temp_block[1])

        TEMPORAL_COHERENCE_KERNEL(
            temp_grid, temp_block,
            (
                char_indices_gpu,
                self.prev_char_indices,
                gray_gpu,
                self.prev_gray,
                output_indices,
                w, h,
                threshold
            )
        )

        self.prev_char_indices = output_indices.copy()
        self.prev_gray = gray_gpu.copy()

        return output_indices

    def process_batch(self, gray_frames, color_frames, char_indices, color_indices):
        pass

    def render_frame_batch(self, char_indices_batch, color_indices_batch):
        pass

    def render_frame(self, char_indices_gpu, color_indices_gpu):
        self.output_buffer_gpu.fill(0)

        RENDER_KERNEL(
            self.grid, self.block,
            (
                char_indices_gpu,
                color_indices_gpu,
                self.atlas_gpu,
                self.output_buffer_gpu,
                self.target_width, self.target_height,
                self.char_w, self.char_h,
                self.n_chars,
                self.palette_gpu
            )
        )

        return self.output_buffer_gpu

    def render_fast_with_matrix(
        self,
        input_gray_gpu,
        input_color_gpu,
        chroma_mask=None,
        matrix_mode='overlay',
        dt=0.033
    ):
        if self.braille_enabled:
            char_indices = self.convert_to_braille(input_gray_gpu)
        else:
            char_indices = self.render_high_fidelity(input_gray_gpu)

        if self.temporal_coherence:
            char_indices = self.apply_temporal_coherence(char_indices, input_gray_gpu)

        h, w, _ = input_color_gpu.shape
        color_flat = input_color_gpu.reshape(-1, 3)

        grid_h, grid_w = char_indices.shape
        samples_per_cell_h = h // grid_h
        samples_per_cell_w = w // grid_w

        if samples_per_cell_h < 1:
            samples_per_cell_h = 1
        if samples_per_cell_w < 1:
            samples_per_cell_w = 1

        sampled_colors = input_color_gpu[::samples_per_cell_h, ::samples_per_cell_w, :]
        sampled_colors_resized = cp.zeros((grid_h, grid_w, 3), dtype=cp.uint8)

        actual_sample_h, actual_sample_w = sampled_colors.shape[:2]
        min_h = min(grid_h, actual_sample_h)
        min_w = min(grid_w, actual_sample_w)
        sampled_colors_resized[:min_h, :min_w, :] = sampled_colors[:min_h, :min_w, :]

        color_indices = rgb_to_ansi256_vectorized(sampled_colors_resized)

        if self.matrix_rain:
            self.matrix_rain.update(dt=dt)

            if matrix_mode == 'overlay':
                self.matrix_rain.render(char_indices, sampled_colors_resized)

            elif matrix_mode == 'replace' and chroma_mask is not None:
                mask_resized = chroma_mask[::samples_per_cell_h, ::samples_per_cell_w]
                mask_resized_final = cp.zeros((grid_h, grid_w), dtype=cp.bool_)
                mask_resized_final[:min_h, :min_w] = mask_resized[:min_h, :min_w]
                self.matrix_rain.render_with_mask(char_indices, sampled_colors_resized, mask_resized_final)

            elif matrix_mode == 'blend':
                self.matrix_rain.render_blend(char_indices, sampled_colors_resized, alpha=0.3)

            color_indices = rgb_to_ansi256_vectorized(sampled_colors_resized)

        return char_indices, color_indices

def converter_video_para_mp4_gpu(video_path, output_dir, config, progress_callback=None, chroma_override=None, async_mode=None):
    if async_mode is None:
        async_mode = config.getboolean('Conversor', 'gpu_async_enabled', fallback=False)

    if async_mode:
        return _converter_video_para_mp4_gpu_async(
            video_path, output_dir, config, progress_callback, chroma_override
        )

    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        sobel_threshold = config.getint('Conversor', 'sobel_threshold')
        sharpen_enabled = config.getboolean('Conversor', 'sharpen_enabled', fallback=True)
        sharpen_amount = config.getfloat('Conversor', 'sharpen_amount', fallback=0.5)
        luminance_ramp_str = config.get('Conversor', 'luminance_ramp', fallback=LUMINANCE_RAMP_DEFAULT).rstrip('|')
        ramp_array = np.array([ord(c) for c in luminance_ramp_str], dtype=np.int32)
        ramp_gpu = cp.array(ramp_array)
        ramp_len = len(ramp_array)

        render_mode = config.get('Conversor', 'gpu_render_mode', fallback='fast')
        is_hifi = (render_mode == 'high_fidelity')

        braille_enabled = config.getboolean('Conversor', 'braille_enabled', fallback=False)
        braille_threshold = config.getint('Conversor', 'braille_threshold', fallback=128)
        temporal_enabled = config.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
        temporal_threshold = config.getint('Conversor', 'temporal_threshold', fallback=20)

        matrix_rain_enabled = config.getboolean('MatrixRain', 'enabled', fallback=False)
        matrix_num_particles = config.getint('MatrixRain', 'num_particles', fallback=5000)
        matrix_char_set = config.get('MatrixRain', 'char_set', fallback='katakana')
        matrix_speed = config.getfloat('MatrixRain', 'speed', fallback=1.0)
        matrix_mode = config.get('MatrixRain', 'mode', fallback='overlay')

        if braille_enabled:
            print(f"Braille Mode: Threshold={braille_threshold}")
        if temporal_enabled:
            print(f"Temporal Coherence: Threshold={temporal_threshold}")
        if is_hifi:
            print("Mode High Fidelity Activated: Texture Matching.")
        if matrix_rain_enabled:
            print(f"Matrix Rain Enabled: {matrix_num_particles} particles (mode={matrix_mode})")

        postfx_processor = None
        postfx_config = _load_postfx_config(config)
        if postfx_config and POSTFX_AVAILABLE:
            has_any_fx = any([
                postfx_config.bloom_enabled,
                postfx_config.chromatic_enabled,
                postfx_config.scanlines_enabled,
                postfx_config.glitch_enabled
            ])
            if has_any_fx:
                postfx_processor = PostFXProcessor(postfx_config, use_gpu=True)
                fx_list = []
                if postfx_config.bloom_enabled:
                    fx_list.append("Bloom")
                if postfx_config.chromatic_enabled:
                    fx_list.append("Chromatic")
                if postfx_config.scanlines_enabled:
                    fx_list.append("Scanlines")
                if postfx_config.glitch_enabled:
                    fx_list.append("Glitch")
                print(f"PostFX habilitado (GPU): {', '.join(fx_list)}")

        if chroma_override:
            lower_green = cp.array([
                chroma_override['h_min'], chroma_override['s_min'], chroma_override['v_min']
            ])
            upper_green = cp.array([
                chroma_override['h_max'], chroma_override['s_max'], chroma_override['v_max']
            ])
        else:
            lower_green = cp.array([
                config.getint('ChromaKey', 'h_min'), config.getint('ChromaKey', 's_min'), config.getint('ChromaKey', 'v_min')
            ])
            upper_green = cp.array([
                config.getint('ChromaKey', 'h_max'), config.getint('ChromaKey', 's_max'), config.getint('ChromaKey', 'v_max')
            ])
    except Exception as e:
         raise ValueError(f"Config Error: {e}")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
         raise IOError(f"Cannot open video: {video_path}")

    fps = captura.get(cv2.CAP_PROP_FPS)
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    source_w = captura.get(cv2.CAP_PROP_FRAME_WIDTH)
    source_h = captura.get(cv2.CAP_PROP_FRAME_HEIGHT)

    config_height = config.getint('Conversor', 'target_height', fallback=0)
    if config_height > 0:
        target_height = config_height
    else:
        target_height = int((target_width * source_h * char_aspect_ratio) / source_w)

    if braille_enabled:
        braille_grid_h = target_height // 4
        braille_grid_w = target_width // 2
        display_width = braille_grid_w
        display_height = braille_grid_h
        print(f"Braille Grid: {display_width}x{display_height} chars (from {target_width}x{target_height} pixels)")
    else:
        display_width = target_width
        display_height = target_height

    target_dim = (target_width, target_height)
    try:
        device_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode('utf-8')
    except:
        device_name = "CUDA Device"

    print(f"GPU Mode: {display_width}x{display_height}, Device: {device_name}")

    gpu_renderer = GPUConverter(
        display_width, display_height,
        braille_enabled=braille_enabled,
        temporal_coherence=temporal_enabled,
        matrix_rain_enabled=matrix_rain_enabled,
        matrix_num_particles=matrix_num_particles,
        matrix_char_set=matrix_char_set,
        matrix_speed=matrix_speed,
        luminance_ramp=luminance_ramp_str
    )

    temp_dir = tempfile.mkdtemp(prefix="gpu_ascii_")

    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    temp_video_no_audio = os.path.join(temp_dir, "video_no_audio.mp4")
    output_mp4 = os.path.join(output_dir, f"{nome_base}_ascii.mp4")

    if is_hifi:
        resize_target = (target_width * ASCII_CHAR_WIDTH, target_height * ASCII_CHAR_HEIGHT)
        print(f"High Fidelity: Resizing to full char resolution {resize_target}")
    else:
        resize_target = target_dim

    cmd_ffmpeg = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{gpu_renderer.out_w}x{gpu_renderer.out_h}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        temp_video_no_audio
    ]

    proc = subprocess.Popen(cmd_ffmpeg, stdin=subprocess.PIPE)

    processed_count = 0

    try:
        while True:
            sucesso, frame_img = captura.read()
            if not sucesso:
                break

            resized = cv2.resize(frame_img, resize_target, interpolation=cv2.INTER_AREA)

            if matrix_rain_enabled:
                if is_hifi:
                    full_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    full_gray_gpu = cp.array(full_gray)
                    resized_color = cv2.resize(resized, target_dim, interpolation=cv2.INTER_AREA)
                else:
                    full_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    full_gray_gpu = cp.array(full_gray)
                    resized_color = resized

                resized_color_gpu = cp.array(resized_color)

                hsv_cpu = cv2.cvtColor(resized_color, cv2.COLOR_BGR2HSV)
                l_g_cpu = lower_green.get()
                u_g_cpu = upper_green.get()
                mask_cpu = cv2.inRange(hsv_cpu, l_g_cpu, u_g_cpu)
                chroma_mask_gpu = cp.array(mask_cpu > 127)

                char_indices, ansi_gpu = gpu_renderer.render_fast_with_matrix(
                    full_gray_gpu,
                    resized_color_gpu,
                    chroma_mask=chroma_mask_gpu,
                    matrix_mode=matrix_mode,
                    dt=1.0/fps
                )

                is_masked = chroma_mask_gpu
                if braille_enabled:
                    downsampled_mask = is_masked[::4, ::2]
                    char_indices[downsampled_mask] = 32
                else:
                    char_indices[is_masked] = 32

                output_gpu = gpu_renderer.render_frame(char_indices, ansi_gpu)

            else:
                if is_hifi:
                    full_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    full_gray_gpu = cp.array(full_gray)
                    char_indices = gpu_renderer.render_high_fidelity(full_gray_gpu)

                    resized_color = cv2.resize(resized, target_dim, interpolation=cv2.INTER_AREA)
                else:
                    resized_color = resized

                hsv_cpu = cv2.cvtColor(resized_color, cv2.COLOR_BGR2HSV)
                l_g_cpu = lower_green.get()
                u_g_cpu = upper_green.get()
                mask_cpu = cv2.inRange(hsv_cpu, l_g_cpu, u_g_cpu)

                mask_gpu = cp.array(mask_cpu)
                is_masked = mask_gpu > 127

                ansi_cpu = rgb_to_ansi256_vectorized(resized_color)
                ansi_gpu = cp.array(ansi_cpu, dtype=cp.int32)
                ansi_gpu[is_masked] = 232

                if not is_hifi:
                    frame_gpu = cp.array(resized_color)
                    b, g, r = frame_gpu[:,:,0], frame_gpu[:,:,1], frame_gpu[:,:,2]
                    gray_gpu = 0.114*b + 0.587*g + 0.299*r
                    gray_gpu = gray_gpu.astype(cp.uint8)

                    if braille_enabled:
                        char_indices = gpu_renderer.convert_to_braille(gray_gpu, braille_threshold)

                        downsampled_gray = gray_gpu[::4, ::2]
                        downsampled_ansi = ansi_gpu[::4, ::2]
                        downsampled_mask = is_masked[::4, ::2]

                        char_indices[downsampled_mask] = 0
                        ansi_gpu = downsampled_ansi
                        is_masked = downsampled_mask
                    else:
                        gy, gx = cp.gradient(gray_gpu.astype(cp.float32))
                        mag = cp.sqrt(gx**2 + gy**2)
                        mag_norm = cp.clip(mag, 0, 255).astype(cp.uint8)

                        angle = cp.arctan2(gy, gx)
                        angle_deg = angle * (180 / cp.pi)
                        angle_deg = (angle_deg + 180) % 180

                        lum_indices = ((gray_gpu / 255.0) * (ramp_len - 1)).astype(cp.int32)
                        char_indices = ramp_gpu[lum_indices]

                        is_edge = mag_norm > sobel_threshold

                        slash = is_edge & (((angle_deg >= 22.5) & (angle_deg < 67.5)) | ((angle_deg >= 157.5) & (angle_deg < 202.5)))
                        pipe = is_edge & (((angle_deg >= 67.5) & (angle_deg < 112.5)) | ((angle_deg >= 247.5) & (angle_deg < 292.5)))
                        backslash = is_edge & (((angle_deg >= 112.5) & (angle_deg < 157.5)) | ((angle_deg >= 292.5) & (angle_deg < 337.5)))
                        dash = is_edge & (~(slash | pipe | backslash))

                        char_indices[slash] = 47
                        char_indices[pipe] = 124
                        char_indices[backslash] = 92
                        char_indices[dash] = 45

                if temporal_enabled:
                    if braille_enabled:
                        downsampled_gray_for_temp = gray_gpu[::4, ::2]
                        char_indices = gpu_renderer.apply_temporal_coherence(char_indices, downsampled_gray_for_temp, temporal_threshold)
                    else:
                        char_indices = gpu_renderer.apply_temporal_coherence(char_indices, gray_gpu, temporal_threshold)

                char_indices[is_masked] = 32
                output_gpu = gpu_renderer.render_frame(char_indices, ansi_gpu)

            output_cpu = output_gpu.get()

            if postfx_processor:
                output_cpu = postfx_processor.process(output_cpu)

            proc.stdin.write(output_cpu.tobytes())

            processed_count += 1
            if processed_count % 30 == 0:
                print(f"GPU Processed: {processed_count}/{total_frames}")

            if progress_callback and processed_count % 30 == 0:
                progress_callback(processed_count, total_frames, output_cpu)

    except BrokenPipeError:
        print("FFmpeg pipe broke.")
    finally:
        if proc:
            proc.stdin.close()
            proc.wait()
        captura.release()

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
            '-i', temp_video_no_audio,
            '-i', temp_audio,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_mp4
        ]
        result = subprocess.run(cmd_mux, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            print(f"Aviso ao muxar audio: {result.stderr}")
            shutil.copy(temp_video_no_audio, output_mp4)
    else:
        print("Video sem audio, copiando video ASCII...")
        shutil.copy(temp_video_no_audio, output_mp4)

    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"GPU Video ASCII criado: {output_mp4}")
    return output_mp4


def _converter_video_para_mp4_gpu_async(video_path, output_dir, config, progress_callback=None, chroma_override=None):
    from .async_gpu_converter import AsyncGPUConverter

    batch_size = config.getint('Conversor', 'gpu_async_batch_size', fallback=8)
    num_streams = config.getint('Conversor', 'gpu_async_num_streams', fallback=4)

    print(f"[ASYNC MODE] Streams: {num_streams}, Batch size: {batch_size}")

    try:
        target_width = config.getint('Conversor', 'target_width')
        char_aspect_ratio = config.getfloat('Conversor', 'char_aspect_ratio')
        braille_enabled = config.getboolean('Conversor', 'braille_enabled', fallback=False)
        braille_threshold = config.getint('Conversor', 'braille_threshold', fallback=128)
        temporal_enabled = config.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
        luminance_ramp_str = config.get('Conversor', 'luminance_ramp', fallback='').rstrip('|')

        if chroma_override:
            lower_green = cp.array([
                chroma_override['h_min'], chroma_override['s_min'], chroma_override['v_min']
            ])
            upper_green = cp.array([
                chroma_override['h_max'], chroma_override['s_max'], chroma_override['v_max']
            ])
        else:
            lower_green = cp.array([
                config.getint('ChromaKey', 'h_min'),
                config.getint('ChromaKey', 's_min'),
                config.getint('ChromaKey', 'v_min')
            ])
            upper_green = cp.array([
                config.getint('ChromaKey', 'h_max'),
                config.getint('ChromaKey', 's_max'),
                config.getint('ChromaKey', 'v_max')
            ])
    except Exception as e:
        raise ValueError(f"Config Error: {e}")

    captura = cv2.VideoCapture(video_path)
    if not captura.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    fps = captura.get(cv2.CAP_PROP_FPS)
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    source_w = captura.get(cv2.CAP_PROP_FRAME_WIDTH)
    source_h = captura.get(cv2.CAP_PROP_FRAME_HEIGHT)

    config_height = config.getint('Conversor', 'target_height', fallback=0)
    if config_height > 0:
        target_height = config_height
    else:
        target_height = int((target_width * source_h * char_aspect_ratio) / source_w)

    if braille_enabled:
        display_width = target_width // 2
        display_height = target_height // 4
    else:
        display_width = target_width
        display_height = target_height

    target_dim = (target_width, target_height)

    async_converter = AsyncGPUConverter(
        display_width,
        display_height,
        num_streams=num_streams,
        braille_enabled=braille_enabled,
        temporal_coherence=temporal_enabled,
        luminance_ramp=luminance_ramp_str if luminance_ramp_str else None
    )

    temp_dir = tempfile.mkdtemp(prefix="gpu_async_")
    nome_base = os.path.splitext(os.path.basename(video_path))[0]
    temp_video_no_audio = os.path.join(temp_dir, "video_no_audio.mp4")
    output_mp4 = os.path.join(output_dir, f"{nome_base}_ascii.mp4")

    cmd_ffmpeg = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{async_converter.gpu_converter.out_w}x{async_converter.gpu_converter.out_h}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        temp_video_no_audio
    ]

    proc = subprocess.Popen(cmd_ffmpeg, stdin=subprocess.PIPE)

    processed_count = 0
    gray_batch = []
    color_batch = []

    try:
        while True:
            sucesso, frame_img = captura.read()
            if not sucesso:
                break

            resized = cv2.resize(frame_img, target_dim, interpolation=cv2.INTER_AREA)

            hsv_cpu = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            l_g_cpu = lower_green.get()
            u_g_cpu = upper_green.get()
            mask_cpu = cv2.inRange(hsv_cpu, l_g_cpu, u_g_cpu)

            resized[mask_cpu > 127] = [0, 0, 0]

            b, g, r = resized[:,:,0], resized[:,:,1], resized[:,:,2]
            gray = (0.114*b + 0.587*g + 0.299*r).astype(np.uint8)

            gray_batch.append(gray)
            color_batch.append(resized)

            if len(gray_batch) >= batch_size:
                results = async_converter.process_batch(gray_batch, color_batch)

                for char_indices_cpu, color_indices_cpu in results:
                    char_indices_gpu = cp.array(char_indices_cpu)
                    color_indices_gpu = cp.array(color_indices_cpu)

                    output_cpu = async_converter.gpu_converter.render_frame(
                        char_indices_gpu,
                        color_indices_gpu
                    ).get()

                    proc.stdin.write(output_cpu.tobytes())
                    processed_count += 1

                    if progress_callback and processed_count % 30 == 0:
                        progress_callback(processed_count, total_frames, output_cpu)

                gray_batch = []
                color_batch = []

        if gray_batch:
            results = async_converter.process_batch(gray_batch, color_batch)

            for char_indices_cpu, color_indices_cpu in results:
                char_indices_gpu = cp.array(char_indices_cpu)
                color_indices_gpu = cp.array(color_indices_cpu)

                output_cpu = async_converter.gpu_converter.render_frame(
                    char_indices_gpu,
                    color_indices_gpu
                ).get()

                proc.stdin.write(output_cpu.tobytes())
                processed_count += 1

                if progress_callback and processed_count % 30 == 0:
                    progress_callback(processed_count, total_frames, output_cpu)

    except Exception as e:
        proc.stdin.close()
        proc.wait()
        captura.release()
        raise e

    proc.stdin.close()
    proc.wait()
    captura.release()

    if os.path.exists(temp_video_no_audio):
        result = subprocess.run(
            ['ffprobe', '-i', video_path, '-show_streams', '-select_streams', 'a', '-loglevel', 'error'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.stdout:
            cmd_mux = [
                'ffmpeg', '-y',
                '-i', temp_video_no_audio,
                '-i', video_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_mp4
            ]
            result = subprocess.run(cmd_mux, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                shutil.copy(temp_video_no_audio, output_mp4)
        else:
            shutil.copy(temp_video_no_audio, output_mp4)
    else:
        raise RuntimeError("FFmpeg failed to create temp video")

    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[ASYNC] GPU Video ASCII criado: {output_mp4}")
    return output_mp4


if __name__ == "__main__":
    pass
