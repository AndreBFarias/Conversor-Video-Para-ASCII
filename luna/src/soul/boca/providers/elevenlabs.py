from __future__ import annotations

from typing import TYPE_CHECKING

import requests

import config
from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.soul.boca.providers.base import TTSParams, TTSProvider
from src.soul.boca.temp_audio import cleanup_temp_audio, get_temp_audio_path

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)


class ElevenLabsProvider(TTSProvider):
    name = "elevenlabs"
    priority = 10

    def __init__(self, boca: Boca) -> None:
        super().__init__(boca)
        self._voice_id: str | None = None
        self._api_key: str | None = None

    def check_availability(self) -> bool:
        from src.soul.boca.engine_check import _check_elevenlabs_internal

        result = _check_elevenlabs_internal(self._boca)
        if result:
            self._voice_id = self._boca.elevenlabs_voice_id
            self._api_key = config.ELEVENLABS_API_KEY
            self._available = True
        else:
            self._available = False
        return self._available

    @perf_monitor("tts.provider.elevenlabs.generate")
    def generate(self, text: str, params: TTSParams) -> str | None:
        if not self._available:
            return None

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"

            headers = {
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
            }

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": params.stability,
                    "similarity_boost": 0.75,
                    "style": params.style,
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

            logger.info(f"[ElevenLabs] Audio gerado: {output_path}")
            return output_path

        except requests.exceptions.Timeout:
            logger.error("Timeout ao chamar ElevenLabs API")
            return None
        except Exception as e:
            logger.error(f"Erro no ElevenLabs: {e}")
            return None

    def speak(self, text: str, params: TTSParams) -> bool:
        if not self._available:
            return False

        output_path = None
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"

            headers = {
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
            }

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": params.stability,
                    "similarity_boost": 0.85,
                    "style": params.style,
                    "use_speaker_boost": True,
                    "speed": params.speed,
                },
            }

            logger.debug(
                f"Chamando ElevenLabs: speed={params.speed}, " f"stability={params.stability}, style={params.style}"
            )
            response = requests.post(url, json=payload, headers=headers, timeout=20)

            if response.status_code != 200:
                logger.error(f"ElevenLabs API erro: {response.status_code} - {response.text}")
                return False

            output_path = get_temp_audio_path(".mp3")
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info("[ElevenLabs] Audio recebido")

            from src.soul.boca.playback import play_audio_file

            if play_audio_file(self._boca, output_path):
                logger.info("[ElevenLabs] TTS executado com sucesso")
                return True

            return False

        except requests.exceptions.Timeout:
            logger.error("Timeout ao chamar ElevenLabs API")
            return False
        except Exception as e:
            logger.error(f"Erro no ElevenLabs speak: {e}")
            return False
        finally:
            cleanup_temp_audio(output_path)
