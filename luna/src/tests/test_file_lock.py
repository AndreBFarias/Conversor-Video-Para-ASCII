import json
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFileLockContextManager:
    def test_file_lock_creates_file_if_not_exists(self):
        from src.core.file_lock import file_lock

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "new_file.json"
            assert not filepath.exists()

            with file_lock(filepath, "r+") as f:
                content = f.read()
                assert content == "{}"

            assert filepath.exists()

    def test_file_lock_reads_existing_file(self):
        from src.core.file_lock import file_lock

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "existing.json"
            filepath.write_text('{"key": "value"}')

            with file_lock(filepath, "r") as f:
                content = f.read()
                assert '"key"' in content

    def test_file_lock_creates_parent_dirs(self):
        from src.core.file_lock import file_lock

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "file.json"

            with file_lock(filepath, "r+") as f:
                f.read()

            assert filepath.parent.exists()


class TestReadJsonSafe:
    def test_read_json_safe_returns_dict(self):
        from src.core.file_lock import read_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            filepath.write_text('{"name": "Luna", "age": 1}')

            result = read_json_safe(filepath)
            assert isinstance(result, dict)
            assert result["name"] == "Luna"
            assert result["age"] == 1

    def test_read_json_safe_empty_file(self):
        from src.core.file_lock import read_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.json"
            filepath.write_text("")

            result = read_json_safe(filepath)
            assert result == {}

    def test_read_json_safe_whitespace_only(self):
        from src.core.file_lock import read_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "whitespace.json"
            filepath.write_text("   \n  ")

            result = read_json_safe(filepath)
            assert result == {}

    def test_read_json_safe_creates_if_missing(self):
        from src.core.file_lock import read_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "missing.json"

            result = read_json_safe(filepath)
            assert result == {}
            assert filepath.exists()


class TestWriteJsonSafe:
    def test_write_json_safe_creates_file(self):
        from src.core.file_lock import write_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"

            write_json_safe(filepath, {"status": "ok"})

            assert filepath.exists()
            content = json.loads(filepath.read_text())
            assert content["status"] == "ok"

    def test_write_json_safe_overwrites_existing(self):
        from src.core.file_lock import write_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "overwrite.json"
            filepath.write_text('{"old": "data"}')

            write_json_safe(filepath, {"new": "data"})

            content = json.loads(filepath.read_text())
            assert "new" in content
            assert "old" not in content

    def test_write_json_safe_preserves_unicode(self):
        from src.core.file_lock import write_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "unicode.json"

            write_json_safe(filepath, {"mensagem": "Olá mundo"})

            content = filepath.read_text()
            assert "Olá" in content


class TestUpdateJsonSafe:
    def test_update_json_safe_adds_keys(self):
        from src.core.file_lock import update_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "update.json"
            filepath.write_text('{"existing": "value"}')

            result = update_json_safe(filepath, {"new_key": "new_value"})

            assert result["existing"] == "value"
            assert result["new_key"] == "new_value"

    def test_update_json_safe_overwrites_keys(self):
        from src.core.file_lock import update_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "overwrite.json"
            filepath.write_text('{"key": "old_value"}')

            result = update_json_safe(filepath, {"key": "new_value"})

            assert result["key"] == "new_value"

    def test_update_json_safe_creates_file(self):
        from src.core.file_lock import update_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "new.json"

            result = update_json_safe(filepath, {"first": "value"})

            assert result["first"] == "value"
            assert filepath.exists()

    def test_update_json_safe_returns_merged_dict(self):
        from src.core.file_lock import update_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "merge.json"
            filepath.write_text('{"a": 1, "b": 2}')

            result = update_json_safe(filepath, {"b": 3, "c": 4})

            assert result == {"a": 1, "b": 3, "c": 4}


class TestFileLockConcurrency:
    def test_concurrent_reads_dont_corrupt(self):
        import threading

        from src.core.file_lock import read_json_safe

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "concurrent.json"
            filepath.write_text('{"counter": 100}')

            results = []
            errors = []

            def reader():
                try:
                    data = read_json_safe(filepath)
                    results.append(data.get("counter"))
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=reader) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
            assert all(r == 100 for r in results)
