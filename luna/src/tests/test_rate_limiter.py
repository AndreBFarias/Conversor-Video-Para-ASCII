import time
from unittest.mock import patch


class TestSmartRateLimiterInit:
    def test_default_values(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        assert limiter.quota_limit == 60
        assert limiter.safety_margin == 10
        assert limiter._effective_limit == 50

    def test_custom_values(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=100, safety_margin=20)

        assert limiter.quota_limit == 100
        assert limiter.safety_margin == 20
        assert limiter._effective_limit == 80

    def test_empty_requests_deque(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        assert len(limiter.requests) == 0


class TestSmartRateLimiterCleanup:
    def test_removes_old_requests(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()
        old_time = time.time() - 120
        limiter.requests.append(old_time)
        limiter.requests.append(time.time())

        limiter._cleanup_old_requests()

        assert len(limiter.requests) == 1

    def test_keeps_recent_requests(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()
        recent = time.time() - 30
        limiter.requests.append(recent)

        limiter._cleanup_old_requests()

        assert len(limiter.requests) == 1


class TestSmartRateLimiterShouldWait:
    def test_returns_zero_when_empty(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        result = limiter.should_wait()

        assert result == 0.0

    def test_returns_zero_below_limit(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        for _ in range(10):
            limiter.requests.append(time.time())

        result = limiter.should_wait()

        assert result == 0.0

    def test_returns_wait_time_at_limit(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        base_time = time.time() - 30
        for i in range(50):
            limiter.requests.append(base_time + i * 0.1)

        result = limiter.should_wait()

        assert result > 0


class TestSmartRateLimiterRecordRequest:
    def test_appends_timestamp(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        limiter.record_request()

        assert len(limiter.requests) == 1

    def test_multiple_records(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        limiter.record_request()
        limiter.record_request()
        limiter.record_request()

        assert len(limiter.requests) == 3


class TestSmartRateLimiterGetUsage:
    def test_returns_tuple(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        result = limiter.get_usage()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_correct_count(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()
        limiter.record_request()
        limiter.record_request()

        count, limit = limiter.get_usage()

        assert count == 2
        assert limit == 60


class TestSmartRateLimiterCanRequestNow:
    def test_returns_true_when_empty(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        can, wait = limiter.can_request_now()

        assert can is True
        assert wait == 0.0

    def test_returns_false_at_limit(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        for _ in range(50):
            limiter.requests.append(time.time())

        can, wait = limiter.can_request_now()

        assert can is False
        assert wait > 0


class TestSmartRateLimiterWaitIfNeeded:
    def test_no_wait_when_empty(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter()

        result = limiter.wait_if_needed()

        assert result == 0.0
        assert len(limiter.requests) == 1

    @patch("src.soul.rate_limiter.time.sleep")
    def test_waits_when_at_limit(self, mock_sleep):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        base_time = time.time() - 30
        for i in range(50):
            limiter.requests.append(base_time + i * 0.1)

        result = limiter.wait_if_needed()

        assert result > 0
        mock_sleep.assert_called_once()


class TestSmartRateLimiterGetRemainingQuota:
    def test_full_quota_when_empty(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)

        result = limiter.get_remaining_quota()

        assert result == 50

    def test_reduced_quota_after_requests(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        for _ in range(20):
            limiter.record_request()

        result = limiter.get_remaining_quota()

        assert result == 30

    def test_zero_at_limit(self):
        from src.soul.rate_limiter import SmartRateLimiter

        limiter = SmartRateLimiter(quota_limit=60, safety_margin=10)
        for _ in range(60):
            limiter.requests.append(time.time())

        result = limiter.get_remaining_quota()

        assert result == 0


class TestRequestDeduplicatorInit:
    def test_default_window(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        assert dedup.window_seconds == 120

    def test_custom_window(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator(window_seconds=300)

        assert dedup.window_seconds == 300

    def test_empty_requests(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        assert len(dedup.recent_requests) == 0


class TestRequestDeduplicatorCleanup:
    def test_removes_old_entries(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator(window_seconds=60)
        old_time = time.time() - 120
        dedup.recent_requests["old_hash"] = {"timestamp": old_time, "response": "old"}
        dedup.recent_requests["new_hash"] = {"timestamp": time.time(), "response": "new"}

        dedup._cleanup_old()

        assert "old_hash" not in dedup.recent_requests
        assert "new_hash" in dedup.recent_requests


class TestRequestDeduplicatorIsDuplicate:
    def test_returns_false_for_new(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        result = dedup.is_duplicate("new_hash_123")

        assert result is False

    def test_returns_true_for_existing(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()
        dedup.recent_requests["existing_hash"] = {"timestamp": time.time(), "response": "data"}

        result = dedup.is_duplicate("existing_hash")

        assert result is True


class TestRequestDeduplicatorGetCached:
    def test_returns_none_for_new(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        result = dedup.get_cached("unknown_hash")

        assert result is None

    def test_returns_response_for_existing(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()
        dedup.recent_requests["known_hash"] = {"timestamp": time.time(), "response": {"data": "cached"}}

        result = dedup.get_cached("known_hash")

        assert result == {"data": "cached"}

    def test_returns_none_for_expired(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator(window_seconds=60)
        old_time = time.time() - 120
        dedup.recent_requests["expired_hash"] = {"timestamp": old_time, "response": "old"}

        result = dedup.get_cached("expired_hash")

        assert result is None


class TestRequestDeduplicatorRecord:
    def test_stores_request(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        dedup.record("test_hash", {"response": "data"})

        assert "test_hash" in dedup.recent_requests
        assert dedup.recent_requests["test_hash"]["response"] == {"response": "data"}

    def test_updates_existing(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()
        dedup.record("hash1", {"v": 1})
        dedup.record("hash1", {"v": 2})

        assert dedup.recent_requests["hash1"]["response"] == {"v": 2}


class TestRequestDeduplicatorGetStats:
    def test_returns_dict(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator()

        stats = dedup.get_stats()

        assert isinstance(stats, dict)
        assert "cached_requests" in stats
        assert "window_seconds" in stats

    def test_correct_count(self):
        from src.soul.rate_limiter import RequestDeduplicator

        dedup = RequestDeduplicator(window_seconds=300)
        dedup.record("h1", "r1")
        dedup.record("h2", "r2")

        stats = dedup.get_stats()

        assert stats["cached_requests"] == 2
        assert stats["window_seconds"] == 300
