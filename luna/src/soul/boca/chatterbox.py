from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger
from src.soul.boca.temp_audio import cleanup_temp_audio, get_temp_audio_path
from src.core.metricas import perf_monitor

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)


@perf_monitor("tts.gerar_chatterbox")
def gerar_chatterbox(boca: Boca, texto: str, exaggeration: float = 0.5) -> str | None:
    if not boca.chatterbox_disponivel:
        return None

    try:
        output_path = get_temp_audio_path(".wav")

        cmd = [
            boca.venv_tts_python,
            boca.chatterbox_wrapper_path,
            texto,
            output_path,
            boca.chatterbox_reference_audio,
            str(exaggeration),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            logger.error(f"Chatterbox wrapper falhou: {result.stderr}")
            return None

        if "SUCCESS:" not in result.stdout:
            logger.error(f"Chatterbox wrapper nao retornou sucesso: {result.stdout}")
            return None

        logger.info(f"[GERAR] Chatterbox audio gerado: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error("Timeout ao executar Chatterbox wrapper")
        return None
    except Exception as e:
        logger.error(f"Erro no Chatterbox TTS: {e}")
        return None


def falar_chatterbox(boca: Boca, texto: str, exaggeration: float = 0.5) -> bool:
    if not boca.chatterbox_disponivel:
        return False

    output_path = None
    try:
        output_path = get_temp_audio_path(".wav")

        logger.debug("Chamando Chatterbox wrapper isolado...")
        start_time = time.time()

        cmd = [
            boca.venv_tts_python,
            boca.chatterbox_wrapper_path,
            texto,
            output_path,
            boca.chatterbox_reference_audio,
            str(exaggeration),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            logger.error(f"Chatterbox wrapper falhou: {result.stderr}")
            return False

        if "SUCCESS:" not in result.stdout:
            logger.error(f"Chatterbox wrapper nao retornou sucesso: {result.stdout}")
            return False

        duration = time.time() - start_time
        logger.info(f"Audio Chatterbox gerado em {duration:.2f}s")

        from src.soul.boca.playback import play_audio_file

        if play_audio_file(boca, output_path):
            logger.info("Chatterbox TTS executado com sucesso")
            return True

        return False

    except subprocess.TimeoutExpired:
        logger.error("Timeout ao executar Chatterbox wrapper")
        return False
    except Exception as e:
        logger.error(f"Erro no Chatterbox TTS: {e}")
        return False
    finally:
        cleanup_temp_audio(output_path)
