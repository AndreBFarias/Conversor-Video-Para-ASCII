import gzip
import shutil
import tempfile
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)

_temp_dir: Path | None = None
_decompressed_cache: dict[str, Path] = {}


def get_temp_audio_dir() -> Path:
    global _temp_dir
    if _temp_dir is None:
        _temp_dir = Path(tempfile.mkdtemp(prefix="luna_audio_"))
        logger.debug(f"Diretorio temporario de audio criado: {_temp_dir}")
    return _temp_dir


def get_reference_audio(path: Path) -> Path | None:
    if path.exists():
        return path

    gz_path = Path(str(path) + ".gz")
    if gz_path.exists():
        return decompress_audio(gz_path)

    alt_names = [
        path.with_name("reference.wav"),
        path.with_name("reference_speaker.wav"),
    ]
    for alt in alt_names:
        if alt.exists():
            return alt
        alt_gz = Path(str(alt) + ".gz")
        if alt_gz.exists():
            return decompress_audio(alt_gz)

    logger.warning(f"Audio de referencia nao encontrado: {path}")
    return None


def decompress_audio(gz_path: Path) -> Path | None:
    cache_key = str(gz_path)
    if cache_key in _decompressed_cache:
        cached = _decompressed_cache[cache_key]
        if cached.exists():
            return cached

    try:
        temp_dir = get_temp_audio_dir()
        output_name = gz_path.stem
        output_path = temp_dir / output_name

        with gzip.open(gz_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        _decompressed_cache[cache_key] = output_path
        logger.debug(f"Audio descompactado: {gz_path.name} -> {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Erro ao descompactar audio {gz_path}: {e}")
        return None


def cleanup_temp_audio() -> None:
    global _temp_dir, _decompressed_cache
    if _temp_dir and _temp_dir.exists():
        try:
            shutil.rmtree(_temp_dir)
            logger.debug(f"Diretorio temporario de audio removido: {_temp_dir}")
        except Exception as e:
            logger.warning(f"Erro ao remover temp audio: {e}")
    _temp_dir = None
    _decompressed_cache.clear()
