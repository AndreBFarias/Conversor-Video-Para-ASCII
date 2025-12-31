import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestTempAudioPath(unittest.TestCase):
    def test_get_temp_audio_path_default_suffix(self):
        from src.soul.boca.temp_audio import get_temp_audio_path

        path = get_temp_audio_path()
        assert path.endswith(".wav")

    def test_get_temp_audio_path_custom_suffix(self):
        from src.soul.boca.temp_audio import get_temp_audio_path

        path = get_temp_audio_path(".mp3")
        assert path.endswith(".mp3")

    def test_get_temp_audio_path_has_prefix(self):
        from src.soul.boca.temp_audio import AUDIO_PREFIX, get_temp_audio_path

        path = get_temp_audio_path()
        filename = Path(path).name
        assert filename.startswith(AUDIO_PREFIX)

    def test_get_temp_audio_path_unique(self):
        from src.soul.boca.temp_audio import get_temp_audio_path

        path1 = get_temp_audio_path()
        path2 = get_temp_audio_path()
        assert path1 != path2

    def test_get_temp_audio_path_uses_ram_disk_when_available(self):
        from src.soul.boca.temp_audio import RAM_DISK_PATH, get_temp_audio_path

        if RAM_DISK_PATH.exists() and os.access(RAM_DISK_PATH, os.W_OK):
            path = get_temp_audio_path()
            assert path.startswith(str(RAM_DISK_PATH))
        else:
            pytest.skip("RAM disk not available")

    @patch("os.access", return_value=False)
    def test_get_temp_audio_path_fallback_to_tmp(self, mock_access):
        from src.soul.boca.temp_audio import FALLBACK_PATH, get_temp_audio_path

        path = get_temp_audio_path()
        assert path.startswith(str(FALLBACK_PATH))


class TestCleanupTempAudio(unittest.TestCase):
    def test_cleanup_temp_audio_removes_file(self):
        from src.soul.boca.temp_audio import cleanup_temp_audio, get_temp_audio_path

        path = get_temp_audio_path()
        with open(path, "w") as f:
            f.write("test")

        assert os.path.exists(path)
        result = cleanup_temp_audio(path)
        assert result is True
        assert not os.path.exists(path)

    def test_cleanup_temp_audio_handles_missing_file(self):
        from src.soul.boca.temp_audio import cleanup_temp_audio

        result = cleanup_temp_audio("/nonexistent/path/file.wav")
        assert result is False

    def test_cleanup_temp_audio_handles_none(self):
        from src.soul.boca.temp_audio import cleanup_temp_audio

        result = cleanup_temp_audio(None)
        assert result is False

    def test_cleanup_temp_audio_handles_empty_string(self):
        from src.soul.boca.temp_audio import cleanup_temp_audio

        result = cleanup_temp_audio("")
        assert result is False


class TestCleanupAllTempAudio(unittest.TestCase):
    def test_cleanup_all_removes_audio_files(self):
        from src.soul.boca.temp_audio import cleanup_all_temp_audio, get_temp_audio_path

        paths = []
        for _ in range(3):
            path = get_temp_audio_path()
            with open(path, "w") as f:
                f.write("test")
            paths.append(path)

        for path in paths:
            assert os.path.exists(path)

        count = cleanup_all_temp_audio()
        assert count >= 3

        for path in paths:
            assert not os.path.exists(path)

    def test_cleanup_all_returns_count(self):
        from src.soul.boca.temp_audio import cleanup_all_temp_audio

        count = cleanup_all_temp_audio()
        assert isinstance(count, int)


class TestIsUsingRamDisk(unittest.TestCase):
    def test_is_using_ram_disk_returns_bool(self):
        from src.soul.boca.temp_audio import is_using_ram_disk

        result = is_using_ram_disk()
        assert isinstance(result, bool)

    def test_is_using_ram_disk_on_linux(self):
        from src.soul.boca.temp_audio import RAM_DISK_PATH, is_using_ram_disk

        result = is_using_ram_disk()
        expected = RAM_DISK_PATH.exists() and os.access(RAM_DISK_PATH, os.W_OK)
        assert result == expected


class TestDaemonTempAudioPath(unittest.TestCase):
    def test_daemon_get_temp_audio_path(self):
        from src.tools.tts_daemon.daemon import get_temp_audio_path

        path = get_temp_audio_path()
        assert path.endswith(".wav")

    def test_daemon_get_temp_audio_path_unique(self):
        from src.tools.tts_daemon.daemon import get_temp_audio_path

        path1 = get_temp_audio_path()
        path2 = get_temp_audio_path()
        assert path1 != path2

    def test_daemon_uses_different_prefix(self):
        from src.tools.tts_daemon.daemon import AUDIO_PREFIX, get_temp_audio_path

        path = get_temp_audio_path()
        filename = Path(path).name
        assert filename.startswith(AUDIO_PREFIX)
        assert "luna_daemon_" in filename


class TestConstants(unittest.TestCase):
    def test_ram_disk_path(self):
        from src.soul.boca.temp_audio import RAM_DISK_PATH

        assert RAM_DISK_PATH == Path("/dev/shm")

    def test_fallback_path(self):
        from src.soul.boca.temp_audio import FALLBACK_PATH

        assert FALLBACK_PATH == Path("/tmp")

    def test_audio_prefix(self):
        from src.soul.boca.temp_audio import AUDIO_PREFIX

        assert AUDIO_PREFIX == "luna_audio_"


if __name__ == "__main__":
    unittest.main()
