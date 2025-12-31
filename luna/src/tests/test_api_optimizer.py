from unittest.mock import MagicMock


class TestAPIOptimizerInit:
    def test_creates_instance(self):
        from src.soul.api_optimizer import APIOptimizer

        consciencia = MagicMock()
        rate_limiter = MagicMock()
        semantic_cache = MagicMock()
        deduplicator = MagicMock()

        optimizer = APIOptimizer(consciencia, rate_limiter, semantic_cache, deduplicator)

        assert optimizer.consciencia == consciencia
        assert optimizer.rate_limiter == rate_limiter
        assert optimizer.semantic_cache == semantic_cache
        assert optimizer.deduplicator == deduplicator

    def test_initializes_stats(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert optimizer.stats["total_requests"] == 0
        assert optimizer.stats["cache_hits"] == 0
        assert optimizer.stats["dedup_hits"] == 0
        assert optimizer.stats["api_calls"] == 0
        assert optimizer.stats["quota_saved"] == 0


class TestAPIOptimizerBuildCacheKey:
    def test_basic_key(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        key = optimizer._build_cache_key("Hello World")

        assert key == "hello world"

    def test_with_visual_context(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        key = optimizer._build_cache_key("Hello", visual_context="Person smiling")

        assert "|v:" in key
        assert "person smiling" in key.lower()

    def test_strips_whitespace(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        key = optimizer._build_cache_key("  Hello World  ")

        assert key == "hello world"


class TestAPIOptimizerBuildRequestHash:
    def test_returns_md5_hash(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        hash1 = optimizer._build_request_hash("test key")

        assert len(hash1) == 32
        assert hash1.isalnum()

    def test_consistent_hashing(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        hash1 = optimizer._build_request_hash("same key")
        hash2 = optimizer._build_request_hash("same key")

        assert hash1 == hash2

    def test_different_keys_different_hashes(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        hash1 = optimizer._build_request_hash("key one")
        hash2 = optimizer._build_request_hash("key two")

        assert hash1 != hash2


class TestAPIOptimizerProcessRequest:
    def test_increments_total_requests(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        cache.get.return_value = None
        dedup = MagicMock()
        dedup.get_cached.return_value = None
        limiter = MagicMock()
        limiter.can_request_now.return_value = (True, 0)

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)

        optimizer.process_request("test")

        assert optimizer.stats["total_requests"] == 1

    def test_returns_cached_response(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        cache.get.return_value = {"fala_tts": "Cached response"}

        optimizer = APIOptimizer(MagicMock(), MagicMock(), cache, MagicMock())

        result = optimizer.process_request("test")

        assert result == {"fala_tts": "Cached response"}
        assert optimizer.stats["cache_hits"] == 1
        assert optimizer.stats["quota_saved"] == 1

    def test_returns_dedup_response(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        cache.get.return_value = None
        dedup = MagicMock()
        dedup.get_cached.return_value = {"fala_tts": "Dedup response"}

        optimizer = APIOptimizer(MagicMock(), MagicMock(), cache, dedup)

        result = optimizer.process_request("test")

        assert result == {"fala_tts": "Dedup response"}
        assert optimizer.stats["dedup_hits"] == 1

    def test_returns_none_on_cache_miss(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        cache.get.return_value = None
        dedup = MagicMock()
        dedup.get_cached.return_value = None
        limiter = MagicMock()
        limiter.can_request_now.return_value = (True, 0)

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)

        result = optimizer.process_request("test")

        assert result is None


class TestAPIOptimizerCacheResponse:
    def test_caches_in_semantic_cache(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        dedup = MagicMock()

        optimizer = APIOptimizer(MagicMock(), MagicMock(), cache, dedup)

        optimizer.cache_response("test", {"response": "data"})

        cache.set.assert_called_once()

    def test_records_in_deduplicator(self):
        from src.soul.api_optimizer import APIOptimizer

        cache = MagicMock()
        dedup = MagicMock()

        optimizer = APIOptimizer(MagicMock(), MagicMock(), cache, dedup)

        optimizer.cache_response("test", {"response": "data"})

        dedup.record.assert_called_once()

    def test_increments_api_calls(self):
        from src.soul.api_optimizer import APIOptimizer

        optimizer = APIOptimizer(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        optimizer.cache_response("test", {"response": "data"})

        assert optimizer.stats["api_calls"] == 1


class TestAPIOptimizerGetOptimizationStats:
    def test_returns_dict(self):
        from src.soul.api_optimizer import APIOptimizer

        limiter = MagicMock()
        limiter.get_usage.return_value = (10, 60)
        limiter.get_remaining_quota.return_value = 50
        cache = MagicMock()
        cache.get_stats.return_value = {"l1_size": 5, "hit_rate_pct": 50.0}
        dedup = MagicMock()
        dedup.get_stats.return_value = {"cached_requests": 3}

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)

        stats = optimizer.get_optimization_stats()

        assert "total_requests" in stats
        assert "api_calls" in stats
        assert "cache_hits" in stats
        assert "quota_reduction_pct" in stats
        assert "rate_usage" in stats

    def test_calculates_quota_reduction(self):
        from src.soul.api_optimizer import APIOptimizer

        limiter = MagicMock()
        limiter.get_usage.return_value = (10, 60)
        limiter.get_remaining_quota.return_value = 50
        cache = MagicMock()
        cache.get_stats.return_value = {"l1_size": 5, "hit_rate_pct": 50.0}
        dedup = MagicMock()
        dedup.get_stats.return_value = {"cached_requests": 3}

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)
        optimizer.stats["total_requests"] = 100
        optimizer.stats["quota_saved"] = 50

        stats = optimizer.get_optimization_stats()

        assert stats["quota_reduction_pct"] == 50.0

    def test_handles_zero_requests(self):
        from src.soul.api_optimizer import APIOptimizer

        limiter = MagicMock()
        limiter.get_usage.return_value = (0, 60)
        limiter.get_remaining_quota.return_value = 60
        cache = MagicMock()
        cache.get_stats.return_value = {"l1_size": 0, "hit_rate_pct": 0.0}
        dedup = MagicMock()
        dedup.get_stats.return_value = {"cached_requests": 0}

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)

        stats = optimizer.get_optimization_stats()

        assert stats["quota_reduction_pct"] == 0


class TestAPIOptimizerLogStats:
    def test_does_not_raise(self):
        from src.soul.api_optimizer import APIOptimizer

        limiter = MagicMock()
        limiter.get_usage.return_value = (10, 60)
        limiter.get_remaining_quota.return_value = 50
        cache = MagicMock()
        cache.get_stats.return_value = {"l1_size": 5, "hit_rate_pct": 50.0}
        dedup = MagicMock()
        dedup.get_stats.return_value = {"cached_requests": 3}

        optimizer = APIOptimizer(MagicMock(), limiter, cache, dedup)

        result = optimizer.log_stats()

        assert result is None
