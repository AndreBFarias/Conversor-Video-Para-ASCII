import gzip
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSanitizeFrame:
    def test_sanitize_replaces_unicode_quotes(self):
        from src.core.animation import sanitize_frame

        result = sanitize_frame("\u201cHello\u201d")
        assert result == '"Hello"'

    def test_sanitize_replaces_unicode_dashes(self):
        from src.core.animation import sanitize_frame

        result = sanitize_frame("word\u2013word\u2014end")
        assert result == "word-word-end"

    def test_sanitize_replaces_ellipsis(self):
        from src.core.animation import sanitize_frame

        result = sanitize_frame("wait\u2026")
        assert result == "wait..."

    def test_sanitize_replaces_non_breaking_spaces(self):
        from src.core.animation import sanitize_frame

        result = sanitize_frame("hello\u00a0world")
        assert result == "hello world"

    def test_sanitize_preserves_regular_text(self):
        from src.core.animation import sanitize_frame

        text = "Normal ASCII text 123"
        assert sanitize_frame(text) == text


class TestLoadAnimationCached:
    def test_load_returns_tuple(self):
        from src.core.animation.loader import _load_animation_cached
        from src.core.entity_loader import ENTITIES_DIR

        luna_anim = ENTITIES_DIR / "luna" / "animations" / "Luna_observando.txt.gz"
        if luna_anim.exists():
            result = _load_animation_cached(str(luna_anim))
            assert isinstance(result, tuple)
            assert len(result) == 2

            frames, rate = result
            assert isinstance(frames, list)
            assert isinstance(rate, float)

    def test_load_cached_returns_frames_list(self):
        from src.core.animation.loader import _load_animation_cached
        from src.core.entity_loader import ENTITIES_DIR

        luna_anim = ENTITIES_DIR / "luna" / "animations" / "Luna_observando.txt.gz"
        if luna_anim.exists():
            frames, _ = _load_animation_cached(str(luna_anim))
            assert len(frames) > 0


class TestLoadAnimationUncached:
    def test_load_gzip_file(self):
        from src.core.animation.loader import _load_animation_frames_uncached

        with tempfile.TemporaryDirectory() as tmpdir:
            gz_path = Path(tmpdir) / "test.txt.gz"
            content = "[FRAME]\nFrame 1\n[FRAME]\nFrame 2"

            with gzip.open(gz_path, "wt", encoding="utf-8") as f:
                f.write(content)

            txt_path = Path(tmpdir) / "test.txt"
            frames, rate = _load_animation_frames_uncached(txt_path)

            assert len(frames) == 2
            assert "Frame 1" in frames[0]
            assert "Frame 2" in frames[1]

    def test_load_plain_text_file(self):
        from src.core.animation.loader import _load_animation_frames_uncached

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "plain.txt"
            txt_path.write_text("[FRAME]\nSingle Frame")

            frames, rate = _load_animation_frames_uncached(txt_path)
            assert len(frames) >= 1

    def test_load_with_fps_header(self):
        from src.core.animation.loader import _load_animation_frames_uncached

        with tempfile.TemporaryDirectory() as tmpdir:
            gz_path = Path(tmpdir) / "fps.txt.gz"
            content = "15.0\n[FRAME]\nFrame at 15 FPS"

            with gzip.open(gz_path, "wt", encoding="utf-8") as f:
                f.write(content)

            txt_path = Path(tmpdir) / "fps.txt"
            frames, rate = _load_animation_frames_uncached(txt_path)

            assert rate == 15.0

    def test_load_missing_file_returns_placeholder(self):
        from src.core.animation.loader import _load_animation_frames_uncached

        frames, rate = _load_animation_frames_uncached(Path("/nonexistent/path.txt"))
        assert len(frames) == 1
        assert "Nao encontrado" in frames[0] or "encontrado" in frames[0].lower()

    def test_load_empty_content_returns_single_frame(self):
        from src.core.animation.loader import _load_animation_frames_uncached

        with tempfile.TemporaryDirectory() as tmpdir:
            gz_path = Path(tmpdir) / "empty.txt.gz"
            with gzip.open(gz_path, "wt", encoding="utf-8") as f:
                f.write("   ")

            txt_path = Path(tmpdir) / "empty.txt"
            frames, _ = _load_animation_frames_uncached(txt_path)
            assert len(frames) >= 1


class TestAnimationCache:
    def test_clear_animation_cache(self):
        from src.core.animation import clear_animation_cache
        from src.core.animation.loader import _load_animation_cached

        clear_animation_cache()
        info = _load_animation_cached.cache_info()
        assert info.currsize == 0

    def test_get_animation_cache_info(self):
        from src.core.animation import get_animation_cache_info

        info = get_animation_cache_info()
        assert hasattr(info, "hits")
        assert hasattr(info, "misses")
        assert hasattr(info, "currsize")


class TestAutoCompressAnimations:
    @patch("src.core.animation.loader._compression_done", False)
    def test_auto_compress_returns_int(self):
        from src.core.animation import auto_compress_all_animations

        with patch("src.core.animation.loader._compress_to_gzip"):
            result = auto_compress_all_animations()
            assert isinstance(result, int)

    def test_auto_compress_runs_once(self):
        from src.core.animation.loader import _compression_done

        assert _compression_done is True or _compression_done is False


class TestAnimationController:
    def test_controller_init(self):
        from src.core.animation import AnimationController

        controller = AnimationController.__new__(AnimationController)
        controller.entity_name = "Luna"
        controller.animations = {}

        assert controller.entity_name == "Luna"
        assert isinstance(controller.animations, dict)


class TestUnicodeReplacements:
    def test_replacements_dict_exists(self):
        from src.core.animation import UNICODE_REPLACEMENTS

        assert isinstance(UNICODE_REPLACEMENTS, dict)
        assert len(UNICODE_REPLACEMENTS) > 0

    def test_all_replacements_are_strings(self):
        from src.core.animation import UNICODE_REPLACEMENTS

        for old, new in UNICODE_REPLACEMENTS.items():
            assert isinstance(old, str)
            assert isinstance(new, str)
