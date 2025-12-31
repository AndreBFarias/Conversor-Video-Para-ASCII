from src.soul.boca.providers.base import TTSParams, TTSProvider
from src.soul.boca.providers.chatterbox import ChatterboxProvider
from src.soul.boca.providers.coqui import CoquiProvider
from src.soul.boca.providers.daemon import DaemonProvider
from src.soul.boca.providers.elevenlabs import ElevenLabsProvider

__all__ = [
    "TTSProvider",
    "TTSParams",
    "CoquiProvider",
    "ChatterboxProvider",
    "ElevenLabsProvider",
    "DaemonProvider",
]
