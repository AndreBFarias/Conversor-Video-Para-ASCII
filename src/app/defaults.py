# Valores padrao centralizados - UNICA fonte de verdade
# Espelha os valores do config.ini padrao na raiz do projeto
# Todos os modulos DEVEM importar daqui em vez de usar fallback inline

DEFAULTS = {
    'Conversor': {
        'target_width': 85,
        'target_height': 44,
        'char_aspect_ratio': 1.0,
        'sobel_threshold': 10,
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
    'MatrixRain': {
        'enabled': False,
        'mode': 'user',
        'char_set': 'katakana',
        'num_particles': 2500,
        'speed_multiplier': 1.5,
    },
    'ChromaKey': {
        'h_min': 0, 'h_max': 84,
        's_min': 154, 's_max': 255,
        'v_min': 0, 'v_max': 228,
        'erode': 1, 'dilate': 1,
    },
    'OpticalFlow': {
        'enabled': False,
        'target_fps': 30,
        'quality': 'medium',
    },
    'Audio': {
        'enabled': False,
        'sample_rate': 44100,
        'chunk_size': 2048,
        'bass_sensitivity': 1.0,
        'mids_sensitivity': 1.0,
        'treble_sensitivity': 1.0,
    },
}


def get_default(section: str, key: str):
    """Retorna o valor padrao para uma chave de config."""
    return DEFAULTS.get(section, {}).get(key)


# "Quem controla as definicoes, controla o debate." - Thomas Sowell
