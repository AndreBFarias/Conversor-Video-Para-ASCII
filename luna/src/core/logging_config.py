import logging
import sys
from logging.handlers import RotatingFileHandler

import config

LOG_DIR = config.APP_DIR / "src" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
LOG_FORMAT_DETAILED = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)s:%(lineno)d | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    detailed: bool = False,
) -> None:
    global _initialized

    if _initialized:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    root_logger.handlers.clear()

    fmt = LOG_FORMAT_DETAILED if detailed else LOG_FORMAT
    formatter = logging.Formatter(fmt, LOG_DATE_FORMAT)

    if log_to_console:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        console.setLevel(logging.INFO)
        root_logger.addHandler(console)

    if log_to_file:
        file_handler = RotatingFileHandler(
            LOG_DIR / "luna.log",
            maxBytes=10_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

        error_handler = RotatingFileHandler(
            LOG_DIR / "luna_errors.log",
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT_DETAILED, LOG_DATE_FORMAT))
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

    _silence_noisy_loggers()

    _initialized = True
    logging.info("Logging inicializado")


def _silence_noisy_loggers() -> None:
    noisy = [
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "PIL",
        "matplotlib",
        "numba",
        "torch",
        "faster_whisper",
        "TTS",
        "pydub",
        "transformers",
        "ctranslate2",
    ]
    for name in noisy:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
