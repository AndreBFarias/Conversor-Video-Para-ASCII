from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)


def play_audio_file(boca: Boca, audio_path: str) -> bool:
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ["mpv", "--no-video", "--really-quiet"],
        ["paplay"],
        ["aplay"],
    ]

    for player_cmd in players:
        try:
            cmd = player_cmd + [audio_path]
            boca.current_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            boca.current_process.wait()
            boca.current_process = None
            return True
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.error(f"Erro no player {player_cmd[0]}: {e}")
            boca.current_process = None
            continue

    logger.error("Nenhum player de audio disponivel")
    return False


def parar(boca: Boca) -> None:
    logger.info("Parando audio...")
    if boca.current_process:
        try:
            if boca.current_process.poll() is None:
                boca.current_process.terminate()
                try:
                    boca.current_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    boca.current_process.kill()
        except Exception as e:
            logger.error(f"Erro ao terminar processo de audio: {e}")
        finally:
            boca.current_process = None
