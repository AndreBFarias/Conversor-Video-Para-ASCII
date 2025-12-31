import threading
import time
from collections.abc import Callable
from datetime import datetime

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class HealthCheck:
    def __init__(self):
        self.checks: dict[str, Callable] = {}
        self.results: dict[str, dict] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def register(self, name: str, check_func: Callable[[], bool]):
        self.checks[name] = check_func
        logger.debug(f"Health check registered: {name}")

    def unregister(self, name: str):
        if name in self.checks:
            del self.checks[name]
            logger.debug(f"Health check unregistered: {name}")

    def run_check(self, name: str) -> dict:
        if name not in self.checks:
            return {"status": "unknown", "error": "Check not registered"}

        start = time.time()
        try:
            result = self.checks[name]()
            elapsed = time.time() - start

            return {
                "status": "healthy" if result else "unhealthy",
                "latency_ms": int(elapsed * 1000),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    def run_all(self) -> dict:
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)

        self.results = results

        healthy_count = sum(1 for r in results.values() if r["status"] == "healthy")

        return {
            "overall": "healthy" if healthy_count == len(results) else "degraded",
            "healthy": healthy_count,
            "total": len(results),
            "checks": results,
        }

    def start_background_checks(self, interval: int = 60):
        if self._running:
            return

        self._running = True

        def _run():
            while self._running:
                try:
                    self.run_all()
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info(f"Background health checks started (interval: {interval}s)")

    def stop(self):
        self._running = False
        logger.info("Background health checks stopped")

    def get_last_results(self) -> dict:
        return self.results.copy()

    def is_healthy(self) -> bool:
        if not self.results:
            self.run_all()
        return all(r["status"] == "healthy" for r in self.results.values())


_health_instance: HealthCheck | None = None


def get_health_check() -> HealthCheck:
    global _health_instance
    if _health_instance is None:
        _health_instance = HealthCheck()
        _register_default_checks(_health_instance)
    return _health_instance


def _register_default_checks(health: HealthCheck):
    health.register("memory_system", _check_memory)
    health.register("entity_loader", _check_entity)
    health.register("file_system", _check_filesystem)


def _check_memory() -> bool:
    try:
        from src.data_memory.smart_memory import get_entity_smart_memory

        mem = get_entity_smart_memory("luna")
        return mem is not None
    except Exception:
        return False


def _check_entity() -> bool:
    try:
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")
        return loader.get_soul_prompt() is not None and len(loader.get_soul_prompt()) > 0
    except Exception:
        return False


def _check_filesystem() -> bool:
    import config

    paths = [
        config.APP_DIR / "src" / "data_memory" / "user" / "profile.json",
        config.APP_DIR / "src" / "assets" / "panteao" / "registry.json",
    ]

    for p in paths:
        if not p.exists():
            return False
    return True


def reset_health_check():
    global _health_instance
    if _health_instance:
        _health_instance.stop()
    _health_instance = None
