import gzip
import shutil
import tempfile
from pathlib import Path


from src.core.audio_utils import (
    _decompressed_cache,
    cleanup_temp_audio,
    decompress_audio,
    get_reference_audio,
    get_temp_audio_dir,
)


class TestGetTempAudioDir:
    def test_creates_temp_directory(self):
        cleanup_temp_audio()
        temp_dir = get_temp_audio_dir()
        assert temp_dir is not None
        assert temp_dir.exists()
        assert "luna_audio_" in str(temp_dir)
        cleanup_temp_audio()

    def test_returns_same_directory_on_multiple_calls(self):
        cleanup_temp_audio()
        dir1 = get_temp_audio_dir()
        dir2 = get_temp_audio_dir()
        assert dir1 == dir2
        cleanup_temp_audio()


class TestDecompressAudio:
    def test_returns_none_for_nonexistent_file(self):
        result = decompress_audio(Path("/nonexistent/file.wav.gz"))
        assert result is None

    def test_decompresses_valid_gz_file(self):
        cleanup_temp_audio()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            test_content = b"RIFF" + b"\x00" * 100
            f.write(test_content)
            temp_wav = Path(f.name)

        gz_path = Path(str(temp_wav) + ".gz")
        with open(temp_wav, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        result = decompress_audio(gz_path)
        assert result is not None
        assert result.exists()
        with open(result, "rb") as f:
            content = f.read()
            assert content == test_content

        temp_wav.unlink()
        gz_path.unlink()
        cleanup_temp_audio()

    def test_uses_cache_for_same_file(self):
        cleanup_temp_audio()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 50)
            temp_wav = Path(f.name)

        gz_path = Path(str(temp_wav) + ".gz")
        with open(temp_wav, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        result1 = decompress_audio(gz_path)
        result2 = decompress_audio(gz_path)
        assert result1 == result2
        assert str(gz_path) in _decompressed_cache

        temp_wav.unlink()
        gz_path.unlink()
        cleanup_temp_audio()


class TestGetReferenceAudio:
    def test_returns_existing_wav_path(self):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 20)
            temp_path = Path(f.name)

        result = get_reference_audio(temp_path)
        assert result == temp_path

        temp_path.unlink()

    def test_returns_none_for_nonexistent_file(self):
        result = get_reference_audio(Path("/nonexistent/audio.wav"))
        assert result is None

    def test_decompresses_gz_when_wav_missing(self):
        cleanup_temp_audio()

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "reference.wav"
            gz_path = Path(tmpdir) / "reference.wav.gz"

            test_content = b"RIFF" + b"\x00" * 80
            with gzip.open(gz_path, "wb") as f:
                f.write(test_content)

            result = get_reference_audio(wav_path)
            assert result is not None
            assert result.exists()

            with open(result, "rb") as f:
                assert f.read() == test_content

        cleanup_temp_audio()

    def test_tries_alternative_names(self):
        cleanup_temp_audio()

        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = Path(tmpdir) / "main_audio.wav"
            alt_path = Path(tmpdir) / "reference.wav"

            alt_path.write_bytes(b"RIFF" + b"\x00" * 30)

            result = get_reference_audio(main_path)
            assert result == alt_path

        cleanup_temp_audio()


class TestCleanupTempAudio:
    def test_removes_temp_directory(self):
        cleanup_temp_audio()
        temp_dir = get_temp_audio_dir()
        assert temp_dir.exists()

        cleanup_temp_audio()
        assert not temp_dir.exists()

    def test_clears_cache(self):
        cleanup_temp_audio()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 40)
            temp_wav = Path(f.name)

        gz_path = Path(str(temp_wav) + ".gz")
        with open(temp_wav, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        decompress_audio(gz_path)
        assert len(_decompressed_cache) > 0

        cleanup_temp_audio()
        assert len(_decompressed_cache) == 0

        temp_wav.unlink()
        gz_path.unlink()

    def test_handles_already_removed_directory(self):
        cleanup_temp_audio()
        temp_dir = get_temp_audio_dir()
        shutil.rmtree(temp_dir)

        cleanup_temp_audio()
        assert not temp_dir.exists()


class TestIntegration:
    def test_full_workflow(self):
        cleanup_temp_audio()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_wav = Path(tmpdir) / "voice.wav"
            original_content = b"RIFF" + b"\x00" * 200

            original_wav.write_bytes(original_content)

            gz_path = Path(str(original_wav) + ".gz")
            with open(original_wav, "rb") as f_in:
                with gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            original_wav.unlink()

            result = get_reference_audio(original_wav)
            assert result is not None
            assert result.exists()

            with open(result, "rb") as f:
                assert f.read() == original_content

            result2 = get_reference_audio(original_wav)
            assert result == result2

            cleanup_temp_audio()
            assert not result.exists()
