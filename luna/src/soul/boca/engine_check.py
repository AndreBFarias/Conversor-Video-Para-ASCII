from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import TYPE_CHECKING

import config
from src.core.audio_utils import get_reference_audio
from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)

TTS_SOCKET_PATH = "/tmp/luna_tts_daemon.sock"


def check_daemon(boca: Boca) -> None:
    if not os.path.exists(TTS_SOCKET_PATH):
        logger.info("TTS Daemon nao esta rodando (socket nao existe)")
        return

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(TTS_SOCKET_PATH)
        sock.close()
        boca.daemon_disponivel = True
        logger.info("TTS Daemon conectado com sucesso")
    except Exception as e:
        logger.warning(f"TTS Daemon nao disponivel: {e}")


def _check_elevenlabs_internal(boca: Boca) -> bool:
    if not config.ELEVENLABS_API_KEY:
        return False

    elevenlabs_config = boca.entity_voice_config.get("elevenlabs", {})
    voice_id = elevenlabs_config.get("voice_id")

    if not voice_id:
        voice_id = config.ELEVENLABS_VOICE_ID

    if not voice_id or voice_id == "YOUR_ELEVENLABS_VOICE_ID":
        return False

    boca.elevenlabs_voice_id = voice_id
    boca.elevenlabs_stability = elevenlabs_config.get("stability", 0.5)
    boca.elevenlabs_similarity = elevenlabs_config.get("similarity_boost", 0.75)
    boca.elevenlabs_style = elevenlabs_config.get("style", 0.5)
    return True


def check_elevenlabs(boca: Boca) -> None:
    if _check_elevenlabs_internal(boca):
        boca.elevenlabs_disponivel = True
        logger.info(f"ElevenLabs configurado para {boca.active_entity_id}")
    else:
        logger.warning("ElevenLabs nao configurado")


def _check_coqui_internal(boca: Boca) -> bool:
    venv_tts = Path("venv_tts")
    tts_wrapper = Path("src/tools/tts_wrapper.py")

    coqui_config = boca.entity_voice_config.get("coqui", {})
    reference_audio = coqui_config.get("reference_audio")

    if not reference_audio:
        reference_audio = config.COQUI_REFERENCE_AUDIO

    if reference_audio and not os.path.isabs(reference_audio):
        reference_audio = str(config.APP_DIR / reference_audio)

    if not venv_tts.exists():
        return False

    if not tts_wrapper.exists():
        return False

    resolved_audio = get_reference_audio(Path(reference_audio)) if reference_audio else None
    if not resolved_audio:
        return False

    boca.venv_tts_python = str(venv_tts / "bin" / "python")
    boca.tts_wrapper_path = str(tts_wrapper)
    boca.coqui_reference_audio = str(resolved_audio)
    return True


def check_coqui(boca: Boca) -> None:
    if _check_coqui_internal(boca):
        boca.coqui_disponivel = True
        logger.info(f"Coqui TTS configurado para {boca.active_entity_id}")
    else:
        logger.warning("Coqui TTS nao disponivel")


def _check_chatterbox_internal(boca: Boca) -> bool:
    venv_tts = Path("venv_tts")
    chatterbox_wrapper = Path("src/tools/chatterbox_wrapper.py")

    chatterbox_config = boca.entity_voice_config.get("chatterbox", {})
    reference_audio = chatterbox_config.get("reference_audio")

    if not reference_audio:
        reference_audio = config.CHATTERBOX_REFERENCE_AUDIO

    if reference_audio and not os.path.isabs(reference_audio):
        reference_audio = str(config.APP_DIR / reference_audio)

    if not venv_tts.exists():
        return False

    if not chatterbox_wrapper.exists():
        return False

    resolved_audio = get_reference_audio(Path(reference_audio)) if reference_audio else None
    if not resolved_audio:
        return False

    boca.venv_tts_python = str(venv_tts / "bin" / "python")
    boca.chatterbox_wrapper_path = str(chatterbox_wrapper)
    boca.chatterbox_reference_audio = str(resolved_audio)

    boca.chatterbox_exaggeration = chatterbox_config.get("exaggeration", config.CHATTERBOX_EXAGGERATION)
    boca.chatterbox_cfg_weight = chatterbox_config.get("cfg_weight", config.CHATTERBOX_CFG_WEIGHT)
    return True


def check_chatterbox(boca: Boca) -> None:
    if _check_chatterbox_internal(boca):
        boca.chatterbox_disponivel = True
        logger.info(f"Chatterbox TTS configurado para {boca.active_entity_id}")
    else:
        logger.warning("Chatterbox TTS nao disponivel")


def get_effective_engine(boca: Boca) -> str:
    configured = config.TTS_ENGINE.lower()

    if configured == "chatterbox" and boca.chatterbox_disponivel:
        return "chatterbox"
    if configured == "coqui" and boca.coqui_disponivel:
        return "coqui"
    if configured == "elevenlabs" and boca.elevenlabs_disponivel:
        return "elevenlabs"

    if boca.chatterbox_disponivel:
        logger.info(f"Engine {configured} indisponivel, usando chatterbox")
        return "chatterbox"
    if boca.coqui_disponivel:
        logger.info(f"Engine {configured} indisponivel, usando coqui")
        return "coqui"
    if boca.elevenlabs_disponivel:
        logger.info(f"Engine {configured} indisponivel, usando elevenlabs")
        return "elevenlabs"

    logger.warning("Nenhum engine TTS disponivel")
    return "none"
