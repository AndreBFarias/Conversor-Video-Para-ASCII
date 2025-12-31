import tempfile
import time
from pathlib import Path
from unittest.mock import patch


class TestSemanticCacheInit:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_init_default_values(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        assert cache.similarity_threshold == 0.85
        assert cache.max_size == 200
        assert cache.ttl_seconds == 7200
        assert cache.cache_l1 is not None
        assert len(cache.cache_l1) == 0

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_init_custom_values(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(similarity_threshold=0.9, max_size=50, ttl_seconds=3600, enable_l2=False)
        assert cache.similarity_threshold == 0.9
        assert cache.max_size == 50
        assert cache.ttl_seconds == 3600

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_stats_initialized(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0
        assert cache.stats["evictions"] == 0


class TestSemanticCacheHashText:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_hash_text_consistent(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        hash1 = cache._hash_text("test text")
        hash2 = cache._hash_text("test text")
        assert hash1 == hash2

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_hash_text_case_insensitive(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        hash1 = cache._hash_text("TEST TEXT")
        hash2 = cache._hash_text("test text")
        assert hash1 == hash2

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_hash_text_strips_whitespace(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        hash1 = cache._hash_text("  test text  ")
        hash2 = cache._hash_text("test text")
        assert hash1 == hash2

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_hash_text_different_input(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        hash1 = cache._hash_text("text one")
        hash2 = cache._hash_text("text two")
        assert hash1 != hash2


class TestSemanticCacheGetSet:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_set_and_get(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        cache.set("test query", {"response": "test response"})
        result = cache.get("test query")
        assert result == {"response": "test response"}

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_get_nonexistent(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        result = cache.get("nonexistent query")
        assert result is None
        assert cache.stats["misses"] == 1

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_get_increments_hits(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        cache.set("query", {"data": "value"})
        cache.get("query")
        assert cache.stats["hits"] == 1

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_get_expired_entry(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(ttl_seconds=1, enable_l2=False)
        cache.set("query", {"data": "value"})

        time.sleep(1.5)

        result = cache.get("query")
        assert result is None


class TestSemanticCacheEviction:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_enforce_size_limit(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(max_size=3, enable_l2=False)
        cache.set("query1", "response1")
        cache.set("query2", "response2")
        cache.set("query3", "response3")
        cache.set("query4", "response4")

        cache._enforce_size_limit()
        assert len(cache.cache_l1) <= 3

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_cleanup_expired(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(ttl_seconds=1, enable_l2=False)
        cache.set("query1", "response1")
        cache.set("query2", "response2")

        time.sleep(1.5)

        cache._cleanup_expired()
        assert len(cache.cache_l1) == 0


class TestSemanticCacheStats:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_get_stats(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        cache.set("q1", "r1")
        cache.get("q1")
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate_l1_pct" in stats

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2.db")
    def test_clear_cache(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        cache.set("q1", "r1")
        cache.set("q2", "r2")

        cache.clear()
        assert len(cache.cache_l1) == 0


class TestSemanticCacheL2:
    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2_db.db")
    def test_l2_enabled(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=True)
        assert cache.l2_enabled is True

    @patch("src.soul.semantic_cache.L2_CACHE_DB", Path(tempfile.gettempdir()) / "test_l2_db.db")
    def test_l2_disabled(self):
        from src.soul.semantic_cache import SemanticCache

        cache = SemanticCache(enable_l2=False)
        assert cache.l2_enabled is False
