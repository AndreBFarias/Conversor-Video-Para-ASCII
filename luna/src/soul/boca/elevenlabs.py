from __future__ import annotations

from typing import TYPE_CHECKING

import requests

import config
from src.core.logging_config import get_logger
from src.soul.boca.temp_audio import cleanup_temp_audio, get_temp_audio_path
from src.core.metricas import perf_monitor

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)


@perf_monitor("tts.gerar_elevenlabs")
def gerar_elevenlabs(
    boca: Boca, texto: str, speed: float = 1.0, stability: float = 0.5, style: float = 0.0
) -> str | None:
    if not boca.elevenlabs_disponivel:
        return None

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{boca.elevenlabs_voice_id}"

        headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}

        payload = {
            "text": texto,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.75,
                "style": style,
                "use_speaker_boost": True,
            },
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.error(f"ElevenLabs API erro: {response.status_code}")
            return None

        output_path = get_temp_audio_path(".mp3")
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"[GERAR] ElevenLabs audio gerado: {output_path}")
        return output_path

    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar ElevenLabs API")
        return None
    except Exception as e:
        logger.error(f"Erro no ElevenLabs: {e}")
        return None


def falar_elevenlabs(
    boca: Boca,
    texto: str,
    speed: float = 1.0,
    stability: float = 0.25,
    style: float = 0.7,
    similarity: float = 0.85,
) -> bool:
    if not boca.elevenlabs_disponivel:
        return False

    output_path = None
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{boca.elevenlabs_voice_id}"

        headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}

        payload = {
            "text": texto,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
                "style": style,
                "use_speaker_boost": True,
                "speed": speed,
            },
        }

        logger.debug(f"Chamando ElevenLabs: speed={speed}, stability={stability}, style={style}")
        response = requests.post(url, json=payload, headers=headers, timeout=20)

        if response.status_code != 200:
            logger.error(f"ElevenLabs API erro: {response.status_code} - {response.text}")
            return False

        output_path = get_temp_audio_path(".mp3")
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Audio recebido do ElevenLabs")

        from src.soul.boca.playback import play_audio_file

        if play_audio_file(boca, output_path):
            logger.info("ElevenLabs executado com sucesso")
            return True

        return False

    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar ElevenLabs API")
        return False
    except Exception as e:
        logger.error(f"Erro no ElevenLabs: {e}")
        return False
    finally:
        cleanup_temp_audio(output_path)
