# Valores padrao centralizados - UNICA fonte de verdade
# O config.ini da raiz do projeto eh GERADO a partir deste arquivo
# Todos os modulos DEVEM importar daqui em vez de usar fallback inline
import configparser
import os

DEFAULTS = {
    'Conversor': {
        'luminance_ramp': "MWNXK0Okxdolc:;,'...",
        'target_width': 85,
        'target_height': 44,
        'sobel_threshold': 10,
        'char_aspect_ratio': 1.0,
        'sharpen_enabled': True,
        'sharpen_amount': 0.8,
        'luminance_preset': 'standard',
        'gpu_enabled': True,
        'gpu_render_mode': 'high_fidelity',
        'gpu_async_enabled': True,
        'gpu_async_num_streams': 4,
        'gpu_async_batch_size': 8,
        'braille_enabled': False,
        'braille_threshold': 128,
        'temporal_coherence_enabled': False,
        'temporal_threshold': 50,
        'auto_seg_enabled': False,
        'render_mode': 'both',
        'edge_boost_enabled': False,
        'edge_boost_amount': 100,
        'use_edge_chars': True,
    },
    'Geral': {
        'display_mode': 'window',
    },
    'Quality': {
        'preset': 'custom',
        'player_zoom': 0.7,
    },
    'Pastas': {
        'input_dir': '',
        'output_dir': '',
    },
    'Player': {
        'arquivo': 'data_output/sample.txt',
        'loop': 'nao',
        'clear_screen': True,
        'show_fps': False,
        'speed': 1.0,
    },
    'ChromaKey': {
        'h_min': 0, 'h_max': 84,
        's_min': 154, 's_max': 255,
        'v_min': 0, 'v_max': 228,
        'erode': 1, 'dilate': 1,
    },
    'Mode': {
        'conversion_mode': 'ascii',
    },
    'PixelArt': {
        'color_palette_size': 256,
        'use_fixed_palette': False,
        'pixel_size': 1,
        'fixed_palette_name': 'gameboy',
    },
    'Output': {
        'format': 'txt',
        'mp4_target_fps': 0,
    },
    'Preview': {
        'font_family': 'auto',
        'font_size': 13,
        'font_detection_enabled': True,
        'preview_during_conversion': True,
    },
    'MatrixRain': {
        'enabled': False,
        'mode': 'user',
        'char_set': 'katakana',
        'num_particles': 2500,
        'speed_multiplier': 1.5,
    },
    'PostFX': {
        'bloom_enabled': False,
        'bloom_intensity': 1.2,
        'bloom_radius': 21,
        'bloom_threshold': 80,
        'chromatic_enabled': False,
        'chromatic_shift': 12,
        'scanlines_enabled': False,
        'scanlines_intensity': 0.7,
        'scanlines_spacing': 2,
        'glitch_enabled': False,
        'glitch_intensity': 0.6,
        'glitch_block_size': 8,
    },
    'Style': {
        'style_enabled': False,
        'style_preset': 'none',
    },
    'OpticalFlow': {
        'enabled': False,
        'target_fps': 30,
        'quality': 'medium',
        'motion_blur_enabled': False,
        'motion_blur_intensity': 0.6,
        'motion_blur_samples': 5,
    },
    'Audio': {
        'enabled': False,
        'sample_rate': 44100,
        'chunk_size': 2048,
        'smoothing': 0.3,
        'bass_sensitivity': 1.0,
        'mids_sensitivity': 1.0,
        'treble_sensitivity': 1.0,
    },
    'Interface': {
        'theme': 'dark',
    },
}


def get_default(section: str, key: str):
    """Retorna o valor padrao para uma chave de config."""
    return DEFAULTS.get(section, {}).get(key)


def generate_config() -> configparser.ConfigParser:
    """Gera um ConfigParser com todos os valores padrao."""
    config = configparser.ConfigParser(interpolation=None)
    for section, keys in DEFAULTS.items():
        config.add_section(section)
        for key, value in keys.items():
            if isinstance(value, bool):
                config.set(section, key, str(value).lower())
            else:
                config.set(section, key, str(value))
    return config


def generate_config_file(output_path: str) -> None:
    """Gera o config.ini a partir dos DEFAULTS."""
    config = generate_config()
    with open(output_path, 'w', encoding='utf-8') as f:
        config.write(f)


def validate_config(config_path: str) -> list:
    """Valida um config.ini contra os DEFAULTS. Retorna lista de divergencias."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path, encoding='utf-8')

    divergencias = []
    for section, keys in DEFAULTS.items():
        if not config.has_section(section):
            divergencias.append(f'secao faltando: [{section}]')
            continue
        for key, default_val in keys.items():
            if not config.has_option(section, key):
                divergencias.append(f'chave faltando: [{section}] {key}')
                continue
            config_val = config.get(section, key).strip()
            if isinstance(default_val, bool):
                default_str = str(default_val).lower()
            else:
                default_str = str(default_val)
            if config_val != default_str:
                divergencias.append(f'diverge: [{section}] {key} = {repr(config_val)} (esperado: {repr(default_str)})')

    return divergencias


def sync_config(config_path: str) -> int:
    """Sincroniza um config.ini: adiciona chaves faltando sem sobrescrever existentes."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path, encoding='utf-8')

    added = 0
    for section, keys in DEFAULTS.items():
        if not config.has_section(section):
            config.add_section(section)
            added += 1
        for key, value in keys.items():
            if not config.has_option(section, key):
                if isinstance(value, bool):
                    config.set(section, key, str(value).lower())
                else:
                    config.set(section, key, str(value))
                added += 1

    if added > 0:
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)

    return added


# "Quem controla as definicoes, controla o debate." - Thomas Sowell
