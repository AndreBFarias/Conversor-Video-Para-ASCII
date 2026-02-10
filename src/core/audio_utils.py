#!/usr/bin/env python3
import os
import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)


def extract_audio_as_aac(video_path: str, temp_dir: str) -> str | None:
    result = subprocess.run(
        ['ffprobe', '-i', video_path, '-show_streams',
         '-select_streams', 'a', '-loglevel', 'error'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

    if not result.stdout.strip():
        logger.info("Video sem stream de audio: %s", video_path)
        return None

    temp_audio = os.path.join(temp_dir, "audio.m4a")

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',
        '-c:a', 'aac',
        '-b:a', '192k',
        temp_audio
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

    if result.returncode != 0:
        logger.warning("Falha ao extrair audio: %s", result.stderr[:200])
        return None

    if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1024:
        logger.warning("Audio extraido invalido ou muito pequeno")
        return None

    logger.info("Audio extraido com sucesso: %s", temp_audio)
    return temp_audio


def mux_video_audio(video_path: str, audio_path: str | None, output_path: str) -> bool:
    if audio_path is None:
        shutil.copy(video_path, output_path)
        logger.info("Video sem audio, copiado direto: %s", output_path)
        return True

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_path
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

    if result.returncode == 0 and os.path.exists(output_path):
        logger.info("Mux video+audio concluido: %s", output_path)
        return True

    logger.warning("Falha ao muxar audio, copiando video sem audio: %s", result.stderr[:200])
    shutil.copy(video_path, output_path)
    return False


# "O som e a voz do silencio." - Hazrat Inayat Khan
