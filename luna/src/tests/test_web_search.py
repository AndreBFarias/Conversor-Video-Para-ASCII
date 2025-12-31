from unittest.mock import patch


class TestSearchResultDataclass:
    def test_creates_with_all_fields(self):
        from src.tools.web_search import SearchResult

        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="duckduckgo",
            timestamp=1234567890.0,
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "duckduckgo"
        assert result.timestamp == 1234567890.0


class TestWebSearchInit:
    def test_creates_with_defaults(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch()

            assert search.cache_ttl == 3600
            assert search.max_cache_size == 100
            assert search.last_request_time == 0
            assert search.min_request_interval == 1.0

    def test_creates_with_custom_ttl(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch(cache_ttl=7200)

            assert search.cache_ttl == 7200

    def test_creates_with_custom_cache_size(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch(max_cache_size=50)

            assert search.max_cache_size == 50


class TestWebSearchCacheKey:
    def test_generates_hash(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch()
            key = search._get_cache_key("test query")

            assert isinstance(key, str)
            assert len(key) == 16

    def test_same_query_same_key(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch()
            key1 = search._get_cache_key("test query")
            key2 = search._get_cache_key("test query")

            assert key1 == key2

    def test_normalizes_case(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch()
            key1 = search._get_cache_key("Test Query")
            key2 = search._get_cache_key("test query")

            assert key1 == key2


class TestWebSearchCacheValid:
    def test_returns_false_for_missing_key(self):
        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch()

            assert search._is_cache_valid("nonexistent") is False

    def test_returns_true_for_fresh_cache(self):
        import time

        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch(cache_ttl=3600)
            search.cache["testkey"] = (["result"], time.time())

            assert search._is_cache_valid("testkey") is True

    def test_returns_false_for_expired_cache(self):
        import time

        with patch.object(
            __import__("src.tools.web_search", fromlist=["WebSearch"]).WebSearch,
            "_check_duckduckgo",
            return_value=False,
        ):
            from src.tools.web_search import WebSearch

            search = WebSearch(cache_ttl=3600)
            search.cache["testkey"] = (["result"], time.time() - 7200)

            assert search._is_cache_valid("testkey") is False
