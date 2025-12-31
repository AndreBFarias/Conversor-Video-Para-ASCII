from __future__ import annotations

import logging
import time
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class APIRequestTracker:
    def __init__(self):
        self.lock = Lock()
        self.requests = []
        self.request_counter = 0
        self.consecutive_429_errors = 0
        self.circuit_open = False
        self.circuit_open_until = 0
        self.max_requests_per_minute = 5
        self.debug_logger = None

        logger.info("APIRequestTracker inicializado")

    def _lazy_init_logger(self):
        if self.debug_logger is None:
            from src.core.metricas.singletons import get_api_debug_logger

            self.debug_logger = get_api_debug_logger()

    def _generate_request_id(self) -> str:
        self.request_counter += 1
        return f"REQ-{datetime.now().strftime('%H%M%S')}-{self.request_counter:04d}"

    def can_make_request(self) -> tuple[bool, str]:
        with self.lock:
            now = time.time()

            if self.circuit_open:
                if now < self.circuit_open_until:
                    remaining = int(self.circuit_open_until - now)
                    return False, f"Circuit breaker aberto. Aguarde {remaining}s"
                else:
                    self.circuit_open = False
                    self.consecutive_429_errors = 0
                    logger.info("Circuit breaker fechado. Retomando requests.")

            one_minute_ago = now - 60
            recent_requests = [r for r in self.requests if r["start_time"] > one_minute_ago]
            self.requests = recent_requests

            if len(recent_requests) >= self.max_requests_per_minute:
                return False, f"Limite de {self.max_requests_per_minute} requests/min atingido"

            return True, ""

    def start_request(self, module: str, prompt_preview: str = "") -> dict:
        request_id = self._generate_request_id()
        request_info = {
            "id": request_id,
            "module": module,
            "prompt_preview": prompt_preview[:100] if prompt_preview else "",
            "prompt_len": len(prompt_preview) if prompt_preview else 0,
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": "pending",
            "error": None,
        }

        with self.lock:
            self.requests.append(request_info)
            pending_count = sum(1 for r in self.requests if r["status"] == "pending")
            recent_count = len([r for r in self.requests if r["start_time"] > time.time() - 60])

        logger.info(
            f"[{request_id}] API REQUEST | module={module} | prompt_chars={request_info['prompt_len']} | pending={pending_count} | last_60s={recent_count}"
        )
        return request_info

    def end_request(self, request_info: dict, success: bool, error: str = None):
        self._lazy_init_logger()

        request_info["end_time"] = time.time()
        request_info["duration"] = request_info["end_time"] - request_info["start_time"]
        request_info["status"] = "success" if success else "failed"
        request_info["error"] = error

        is_429 = error and "429" in str(error)

        with self.lock:
            if is_429:
                self.consecutive_429_errors += 1
                recent_requests = [r for r in self.requests if r["start_time"] > time.time() - 60]
                modules_last_60s = [r["module"] for r in recent_requests]
                module_counts = {}
                for m in modules_last_60s:
                    module_counts[m] = module_counts.get(m, 0) + 1

                logger.error(
                    f"[{request_info['id']}] QUOTA 429 ERROR #{self.consecutive_429_errors} | module={request_info['module']} | duration={request_info['duration']:.2f}s"
                )
                logger.error(
                    f"[{request_info['id']}] QUOTA DEBUG | requests_last_60s={len(recent_requests)} | breakdown={module_counts}"
                )

                if self.consecutive_429_errors >= 2:
                    self.circuit_open = True
                    self.circuit_open_until = time.time() + 60
                    logger.error("CIRCUIT BREAKER ATIVADO! Pausando requests por 60s")
            elif not success:
                self.consecutive_429_errors = 0
                logger.warning(
                    f"[{request_info['id']}] REQUEST FAILED | module={request_info['module']} | error={error[:80] if error else 'unknown'}"
                )
            else:
                self.consecutive_429_errors = 0

        status_symbol = "OK" if success else "FAIL"
        logger.info(
            f"[{request_info['id']}] API RESPONSE {status_symbol} | module={request_info['module']} | duration={request_info['duration']:.2f}s"
        )

        if self.debug_logger:
            self.debug_logger.log_result(
                request_id=request_info["id"],
                module=request_info["module"],
                duration=request_info["duration"],
                prompt_len=request_info.get("prompt_len", 0),
                success=success,
                error=error,
                retries=0,
            )

    def get_stats(self) -> dict:
        with self.lock:
            total = len(self.requests)
            successful = sum(1 for r in self.requests if r["status"] == "success")
            failed = sum(1 for r in self.requests if r["status"] == "failed")
            avg_duration = sum(r["duration"] or 0 for r in self.requests) / max(total, 1)

            now = time.time()
            recent = [r for r in self.requests if r["start_time"] > now - 60]
            modules = {}
            for r in recent:
                modules[r["module"]] = modules.get(r["module"], 0) + 1

            return {
                "total_requests": total,
                "successful": successful,
                "failed": failed,
                "avg_duration": round(avg_duration, 3),
                "circuit_open": self.circuit_open,
                "consecutive_429_errors": self.consecutive_429_errors,
                "requests_last_60s": len(recent),
                "modules_last_60s": modules,
            }

    def log_quota_status(self):
        stats = self.get_stats()
        logger.info("=" * 50)
        logger.info("API QUOTA STATUS")
        logger.info(f"  Total requests: {stats['total_requests']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Requests (last 60s): {stats['requests_last_60s']}")
        logger.info(f"  By module: {stats['modules_last_60s']}")
        logger.info(f"  Circuit breaker: {'OPEN' if stats['circuit_open'] else 'closed'}")
        logger.info(f"  Consecutive 429s: {stats['consecutive_429_errors']}")
        logger.info("=" * 50)
