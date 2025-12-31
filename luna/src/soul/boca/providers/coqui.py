from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.soul.boca.providers.base import TTSParams, TTSProvider
from src.soul.boca.temp_audio import cleanup_temp_audio, get_temp_audio_path

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)


class CoquiProvider(TTSProvider):
    name = "coqui"
    priority = 20

    def __init__(self, boca: Boca) -> None:
        super().__init__(boca)
        self._venv_python: str | None = None
        self._wrapper_path: str | None = None
        self._reference_audio: str | None = None

    def check_availability(self) -> bool:
        from src.soul.boca.engine_check import _check_coqui_internal

        result = _check_coqui_internal(self._boca)
        if result:
            self._venv_python = self._boca.venv_tts_python
            self._wrapper_path = self._boca.tts_wrapper_path
            self._reference_audio = self._boca.coqui_reference_audio
            self._available = True
        else:
            self._available = False
        return self._available

    def get_reference_audio(self) -> str | None:
        return self._reference_audio

    @perf_monitor("tts.provider.coqui.generate")
    def generate(self, text: str, params: TTSParams) -> str | None:
        if not self._available:
            return None

        try:
            output_path = get_temp_audio_path(".wav")

            cmd = [
                self._venv_python,
                self._wrapper_path,
                text,
                output_path,
                self._reference_audio,
                str(params.speed),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.error(f"Coqui wrapper falhou: {result.stderr}")
                return None

            if "SUCCESS:" not in result.stdout:
                logger.error(f"Coqui wrapper nao retornou sucesso: {result.stdout}")
                return None

            logger.info(f"[Coqui] Audio gerado: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error("Timeout ao executar Coqui wrapper")
            return None
        except Exception as e:
            logger.error(f"Erro no Coqui TTS: {e}")
            return None

    def speak(self, text: str, params: TTSParams) -> bool:
        if not self._available:
            return False

        output_path = None
        try:
            start_time = time.time()
            output_path = self.generate(text, params)

            if not output_path:
                return False

            duration = time.time() - start_time
            logger.info(f"[Coqui] Audio gerado em {duration:.2f}s")

            from src.soul.boca.playback import play_audio_file

            if play_audio_file(self._boca, output_path):
                logger.info("[Coqui] TTS executado com sucesso")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro no Coqui speak: {e}")
            return False
        finally:
            cleanup_temp_audio(output_path)
