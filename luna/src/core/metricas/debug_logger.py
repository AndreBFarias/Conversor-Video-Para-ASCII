from __future__ import annotations

import json
import logging
import os
from datetime import datetime


class APIDebugLogger:
    def __init__(self, log_path="src/logs/api_debug.log"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.logger = logging.getLogger("api_debug")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(fh)
            self.logger.propagate = False

    def log_request(self, module, prompt_len, start_time, request_id):
        pass

    def log_result(self, request_id, module, duration, prompt_len, success, error=None, retries=0):
        msg = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "module": module,
            "duration_sec": round(duration, 3),
            "prompt_chars": prompt_len,
            "success": success,
            "error_msg": str(error) if error else None,
            "retries": retries,
            "is_429": "429" in str(error) if error else False,
        }

        log_line = json.dumps(msg)
        if success:
            self.logger.info(log_line)
        else:
            if msg["is_429"]:
                self.logger.warning(log_line)
            else:
                self.logger.error(log_line)
