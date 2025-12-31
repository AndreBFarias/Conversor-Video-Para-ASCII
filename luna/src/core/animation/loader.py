from __future__ import annotations

import gzip
import pathlib
from functools import lru_cache

from rich.markup import escape

import config
from src.core.logging_config import get_logger

from .constants import sanitize_frame

logger = get_logger(__name__)


@lru_cache(maxsize=50)
def _load_animation_cached(file_path_str: str) -> tuple[list[str], float]:
    file_path = pathlib.Path(file_path_str)
    return _load_animation_frames_uncached(file_path)


def _load_animation_frames_uncached(file_path: pathlib.Path) -> tuple[list[str], float]:
    try:
        gz_path = pathlib.Path(str(file_path) + ".gz")
        if gz_path.exists():
            try:
                with gzip.open(gz_path, "rt", encoding="utf-8") as f:
                    content = f.read()
                logger.debug(f"Carregando animacao comprimida: {gz_path.name}")
            except gzip.BadGzipFile:
                content = _fix_fake_gzip(gz_path)
        elif file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            _compress_to_gzip(file_path)
        else:
            raise FileNotFoundError(f"Nem {file_path} nem {gz_path} encontrados")

        lines = content.splitlines()
        frames_raw_content = content

        rate = config.FRAME_RATE
        if lines and lines[0].replace(".", "", 1).isdigit():
            try:
                file_rate = float(lines[0])
                if 1.0 <= file_rate <= 120.0:
                    rate = file_rate
                    logger.debug(f"FPS do arquivo {file_path.name}: {rate}")
                frames_raw_content = "\n".join(lines[1:])
            except ValueError:
                pass

        frames_raw = frames_raw_content.split("[FRAME]")
        frames = [sanitize_frame(frame.strip("\n")) for frame in frames_raw if frame.strip()]
        if not frames and content.strip():
            frames = [sanitize_frame(content.strip())]
        return frames or [f"(Vazio: {escape(file_path.name)})"], rate
    except FileNotFoundError:
        logger.error(f"Arquivo de animacao nao encontrado em: {file_path}")
        return [f"(Nao encontrado: {escape(file_path.name)})"], config.FRAME_RATE
    except Exception as e:
        logger.error(f"Erro ao carregar animacao de {file_path}: {e}")
        return [f"(Erro ao carregar: {escape(file_path.name)})"], config.FRAME_RATE


def clear_animation_cache():
    _load_animation_cached.cache_clear()
    logger.info("Animation cache cleared")


def get_animation_cache_info():
    return _load_animation_cached.cache_info()


def _compress_to_gzip(txt_path: pathlib.Path) -> None:
    import subprocess

    try:
        subprocess.run(["gzip", "-9", "-f", str(txt_path)], check=True)
        logger.info(f"[AUTOFIX] {txt_path.name} compactado para .gz")
    except Exception as e:
        logger.warning(f"[AUTOFIX] Falha ao compactar {txt_path.name}: {e}")


_compression_done = False


def auto_compress_all_animations() -> int:
    global _compression_done
    if _compression_done:
        return 0

    compressed_count = 0
    animation_dirs = []

    panteao_dir = config.APP_DIR / "src" / "assets" / "panteao" / "entities"
    if panteao_dir.exists():
        for entity_dir in panteao_dir.iterdir():
            if entity_dir.is_dir():
                anim_dir = entity_dir / "animations"
                if anim_dir.exists():
                    animation_dirs.append(anim_dir)

    legacy_dir = config.APP_DIR / "src" / "assets" / "panteao" / "entities" / "luna" / "animations"
    if legacy_dir.exists():
        animation_dirs.append(legacy_dir)

    for anim_dir in animation_dirs:
        for txt_file in anim_dir.glob("*.txt"):
            gz_file = txt_file.with_suffix(".txt.gz")
            if not gz_file.exists():
                _compress_to_gzip(txt_file)
                compressed_count += 1

    if compressed_count > 0:
        logger.info(f"[AUTOFIX] {compressed_count} animacoes comprimidas automaticamente")

    _compression_done = True
    return compressed_count


def _fix_fake_gzip(gz_path: pathlib.Path) -> str:
    logger.warning(f"[AUTOFIX] {gz_path.name} nao e gzip valido, corrigindo...")

    with open(gz_path, encoding="utf-8") as f:
        content = f.read()

    txt_path = gz_path.with_suffix("")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    gz_path.unlink()
    _compress_to_gzip(txt_path)

    return content


def load_animation_frames_from_file(file_path: pathlib.Path) -> tuple[list[str], float]:
    return _load_animation_cached(str(file_path))
