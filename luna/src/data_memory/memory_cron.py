import threading
import time
from datetime import datetime

from src.core.logging_config import get_logger
from src.data_memory.memory_consolidator import consolidate_all_entities

logger = get_logger(__name__)


class MemoryCron:
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes * 60
        self.running = False
        self.thread: threading.Thread | None = None
        self.last_run: datetime | None = None
        self.run_count = 0
        self.last_results: dict | None = None

    def _run_cycle(self):
        while self.running:
            try:
                logger.info("Memory cron: starting consolidation cycle")
                results = consolidate_all_entities()

                total_consolidated = sum(r.get("consolidated", 0) for r in results.values() if isinstance(r, dict))

                self.last_results = results
                self.last_run = datetime.now()
                self.run_count += 1

                logger.info(f"Memory cron: consolidated {total_consolidated} memories across all entities")

            except Exception as e:
                logger.error(f"Memory cron error: {e}")

            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        if self.running:
            logger.warning("Memory cron already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_cycle, daemon=True, name="MemoryCron")
        self.thread.start()
        logger.info(f"Memory cron started (interval: {self.interval // 60} min)")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("Memory cron stopped")

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "interval_minutes": self.interval // 60,
            "run_count": self.run_count,
            "last_results": self.last_results,
        }

    def force_run(self) -> dict:
        logger.info("Memory cron: forced consolidation")
        try:
            results = consolidate_all_entities()
            self.last_results = results
            self.last_run = datetime.now()
            self.run_count += 1
            return results
        except Exception as e:
            logger.error(f"Forced consolidation failed: {e}")
            return {"status": "error", "error": str(e)}


_cron_instance: MemoryCron | None = None


def get_memory_cron() -> MemoryCron:
    global _cron_instance
    if _cron_instance is None:
        _cron_instance = MemoryCron()
    return _cron_instance


def start_memory_cron(interval_minutes: int = 30) -> MemoryCron:
    global _cron_instance
    if _cron_instance is None:
        _cron_instance = MemoryCron(interval_minutes=interval_minutes)
    _cron_instance.start()
    return _cron_instance


def stop_memory_cron():
    global _cron_instance
    if _cron_instance:
        _cron_instance.stop()
