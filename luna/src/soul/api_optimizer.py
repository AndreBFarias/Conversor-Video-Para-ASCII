import hashlib
import logging

logger = logging.getLogger(__name__)


class APIOptimizer:
    def __init__(self, consciencia, rate_limiter, semantic_cache, deduplicator):
        self.consciencia = consciencia
        self.rate_limiter = rate_limiter
        self.semantic_cache = semantic_cache
        self.deduplicator = deduplicator

        self.stats = {"total_requests": 0, "cache_hits": 0, "dedup_hits": 0, "api_calls": 0, "quota_saved": 0}

        logger.info("APIOptimizer inicializado (quota reduction enabled)")

    def _build_cache_key(self, user_text: str, visual_context: str | None = None) -> str:
        key = user_text.strip().lower()
        if visual_context:
            key += f"|v:{visual_context[:30]}"
        return key

    def _build_request_hash(self, cache_key: str) -> str:
        return hashlib.md5(cache_key.encode()).hexdigest()

    def process_request(
        self, user_text: str, visual_context: str | None = None, attached_content: str | None = None
    ) -> dict | None:
        self.stats["total_requests"] += 1

        cache_key = self._build_cache_key(user_text, visual_context)

        cached = self.semantic_cache.get(cache_key)
        if cached:
            self.stats["cache_hits"] += 1
            self.stats["quota_saved"] += 1
            logger.info(f"APIOptimizer: Cache HIT (saved: {self.stats['quota_saved']})")
            return cached

        req_hash = self._build_request_hash(cache_key)

        dedup_result = self.deduplicator.get_cached(req_hash)
        if dedup_result:
            self.stats["dedup_hits"] += 1
            self.stats["quota_saved"] += 1
            logger.info(f"APIOptimizer: Dedup HIT (saved: {self.stats['quota_saved']})")
            return dedup_result

        can_request, wait_time = self.rate_limiter.can_request_now()
        if not can_request:
            logger.warning(f"APIOptimizer: Rate limit, aguardando {wait_time:.1f}s")

        return None

    def cache_response(self, user_text: str, response: dict, visual_context: str | None = None):
        cache_key = self._build_cache_key(user_text, visual_context)
        req_hash = self._build_request_hash(cache_key)

        self.semantic_cache.set(cache_key, response)
        self.deduplicator.record(req_hash, response)
        self.stats["api_calls"] += 1

        logger.debug(f"APIOptimizer: Response cached (key: {req_hash[:8]})")

    def get_optimization_stats(self) -> dict:
        rate_usage = self.rate_limiter.get_usage()
        cache_stats = self.semantic_cache.get_stats()
        dedup_stats = self.deduplicator.get_stats()

        total = self.stats["total_requests"]
        saved = self.stats["quota_saved"]
        api_calls = self.stats["api_calls"]

        return {
            "total_requests": total,
            "api_calls": api_calls,
            "cache_hits": self.stats["cache_hits"],
            "dedup_hits": self.stats["dedup_hits"],
            "quota_saved": saved,
            "quota_reduction_pct": round((saved / total * 100), 1) if total > 0 else 0,
            "rate_usage": f"{rate_usage[0]}/{rate_usage[1]} RPM",
            "remaining_quota": self.rate_limiter.get_remaining_quota(),
            "cache_size": cache_stats["l1_size"],
            "cache_hit_rate": cache_stats["hit_rate_pct"],
            "dedup_cached": dedup_stats["cached_requests"],
        }

    def log_stats(self):
        stats = self.get_optimization_stats()
        logger.info("=" * 40)
        logger.info("API OPTIMIZER STATS")
        logger.info(f"  Total requests: {stats['total_requests']}")
        logger.info(f"  API calls: {stats['api_calls']}")
        logger.info(f"  Quota saved: {stats['quota_saved']} ({stats['quota_reduction_pct']}%)")
        logger.info(f"  Cache hits: {stats['cache_hits']}")
        logger.info(f"  Dedup hits: {stats['dedup_hits']}")
        logger.info(f"  Rate usage: {stats['rate_usage']}")
        logger.info("=" * 40)
