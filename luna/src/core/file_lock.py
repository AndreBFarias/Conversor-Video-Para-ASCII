import fcntl
import json
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(filepath: Path, mode: str = "r+"):
    filepath = Path(filepath)

    if not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("{}")

    with open(filepath, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield f
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def read_json_safe(filepath: Path) -> dict:
    with file_lock(filepath, "r") as f:
        content = f.read()
        return json.loads(content) if content.strip() else {}


def write_json_safe(filepath: Path, data: dict):
    with file_lock(filepath, "r+") as f:
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_json_safe(filepath: Path, updates: dict) -> dict:
    with file_lock(filepath, "r+") as f:
        content = f.read()
        data = json.loads(content) if content.strip() else {}
        data.update(updates)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2, ensure_ascii=False)
        return data
