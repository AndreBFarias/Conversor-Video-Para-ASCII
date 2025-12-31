import os
import uuid
from pathlib import Path


RAM_DISK_PATH = Path("/dev/shm")
FALLBACK_PATH = Path("/tmp")
AUDIO_PREFIX = "luna_audio_"


def get_temp_audio_path(suffix: str = ".wav") -> str:
    if RAM_DISK_PATH.exists() and os.access(RAM_DISK_PATH, os.W_OK):
        base_dir = RAM_DISK_PATH
    else:
        base_dir = FALLBACK_PATH

    filename = f"{AUDIO_PREFIX}{uuid.uuid4()}{suffix}"
    return str(base_dir / filename)


def cleanup_temp_audio(path: str) -> bool:
    if not path:
        return False

    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except OSError:
        pass

    return False


def cleanup_all_temp_audio() -> int:
    count = 0

    for base_dir in [RAM_DISK_PATH, FALLBACK_PATH]:
        if not base_dir.exists():
            continue

        try:
            for file in base_dir.glob(f"{AUDIO_PREFIX}*"):
                try:
                    file.unlink()
                    count += 1
                except OSError:
                    pass
        except OSError:
            pass

    return count


def is_using_ram_disk() -> bool:
    return RAM_DISK_PATH.exists() and os.access(RAM_DISK_PATH, os.W_OK)
