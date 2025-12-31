from src.soul.boca.chatterbox import falar_chatterbox, gerar_chatterbox
from src.soul.boca.coqui import falar_coqui, gerar_coqui
from src.soul.boca.core import Boca
from src.soul.boca.daemon import gerar_via_daemon
from src.soul.boca.elevenlabs import falar_elevenlabs, gerar_elevenlabs
from src.soul.boca.engine_check import (
    TTS_SOCKET_PATH,
    check_chatterbox,
    check_coqui,
    check_daemon,
    check_elevenlabs,
    get_effective_engine,
)
from src.soul.boca.playback import parar, play_audio_file
from src.soul.boca.sanitizer import TextSanitizer, sanitize_text

__all__ = [
    "Boca",
    "TextSanitizer",
    "sanitize_text",
    "TTS_SOCKET_PATH",
    "check_daemon",
    "check_elevenlabs",
    "check_coqui",
    "check_chatterbox",
    "get_effective_engine",
    "gerar_via_daemon",
    "gerar_coqui",
    "falar_coqui",
    "gerar_chatterbox",
    "falar_chatterbox",
    "gerar_elevenlabs",
    "falar_elevenlabs",
    "play_audio_file",
    "parar",
]
