import configparser

try:
    from src.core.post_fx_gpu import PostFXProcessor, PostFXConfig
    POSTFX_AVAILABLE = True
except ImportError:
    POSTFX_AVAILABLE = False
    PostFXProcessor = None
    PostFXConfig = None


def load_postfx_config(config: configparser.ConfigParser):
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
