import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEmbeddingsCacheInit:
    def test_init_creates_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()

                assert cache.conn is not None
                cursor = cache.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
                assert cursor.fetchone() is not None


class TestHashText:
    def test_hash_returns_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                result = cache._hash_text("test")

                assert isinstance(result, str)
                assert len(result) == 32

    def test_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                hash1 = cache._hash_text("same text")
                hash2 = cache._hash_text("same text")

                assert hash1 == hash2

    def test_different_texts_different_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                hash1 = cache._hash_text("text one")
                hash2 = cache._hash_text("text two")

                assert hash1 != hash2


class TestGetSet:
    def test_get_returns_none_for_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                result = cache.get("nonexistent text")

                assert result is None

    def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                embedding = np.array([0.1, 0.2, 0.3, 0.4])

                cache.set("test text", embedding)
                result = cache.get("test text")

                assert result is not None
                assert np.allclose(result, embedding)

    def test_set_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                old_emb = np.array([1.0, 2.0])
                new_emb = np.array([3.0, 4.0])

                cache.set("key", old_emb)
                cache.set("key", new_emb)
                result = cache.get("key")

                assert np.allclose(result, new_emb)


class TestGetOrCompute:
    def test_returns_cached_on_hit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                embedding = np.array([0.5, 0.5])
                cache.set("cached text", embedding)

                compute_fn = MagicMock(return_value=np.array([9.9, 9.9]))
                result = cache.get_or_compute("cached text", compute_fn)

                compute_fn.assert_not_called()
                assert np.allclose(result, embedding)

    def test_computes_on_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                expected = np.array([1.0, 2.0, 3.0])
                compute_fn = MagicMock(return_value=expected)

                result = cache.get_or_compute("new text", compute_fn)

                compute_fn.assert_called_once_with("new text")
                assert np.allclose(result, expected)

    def test_caches_computed_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                expected = np.array([1.0, 2.0])
                compute_fn = MagicMock(return_value=expected)

                cache.get_or_compute("text", compute_fn)
                cached = cache.get("text")

                assert cached is not None
                assert np.allclose(cached, expected)


class TestClearOld:
    def test_clear_old_runs_without_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                cache.set("test", np.array([1.0]))

                cache.clear_old(days=0)
                assert cache.conn is not None


class TestGetStats:
    def test_get_stats_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                stats = cache.get_stats()

                assert isinstance(stats, dict)
                assert "total_entries" in stats
                assert "db_path" in stats

    def test_stats_count_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache = EmbeddingsCache()
                cache.set("text1", np.array([1.0]))
                cache.set("text2", np.array([2.0]))
                cache.set("text3", np.array([3.0]))

                stats = cache.get_stats()
                assert stats["total_entries"] == 3


class TestGetEmbeddingsCache:
    def test_returns_singleton(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                import src.data_memory.embeddings_cache as ec

                ec._cache_instance = None

                cache1 = ec.get_embeddings_cache()
                cache2 = ec.get_embeddings_cache()

                assert cache1 is cache2


class TestEmbeddingsPersistence:
    def test_data_persists_after_reopen(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache" / "embeddings.db"

            with patch("src.data_memory.embeddings_cache.CACHE_PATH", cache_path):
                from src.data_memory.embeddings_cache import EmbeddingsCache

                cache1 = EmbeddingsCache()
                cache1.set("persistent", np.array([1.0, 2.0, 3.0]))
                del cache1

                cache2 = EmbeddingsCache()
                result = cache2.get("persistent")

                assert result is not None
                assert np.allclose(result, [1.0, 2.0, 3.0])
