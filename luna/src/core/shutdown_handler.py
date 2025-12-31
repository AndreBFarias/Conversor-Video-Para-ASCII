import atexit
import signal
import sys
import threading
from collections.abc import Callable

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ShutdownHandler:
    def __init__(self):
        self.callbacks: list[Callable] = []
        self.shutting_down = False
        self._lock = threading.Lock()
        self._original_sigint = None
        self._original_sigterm = None

    def setup_signals(self):
        self._original_sigint = signal.signal(signal.SIGINT, self._handle_signal)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._handle_signal)
        atexit.register(self._atexit_handler)
        logger.debug("Shutdown handler signals configured")

    def register(self, callback: Callable, name: str = None):
        with self._lock:
            self.callbacks.append((callback, name or callback.__name__))
            logger.debug(f"Shutdown callback registered: {name or callback.__name__}")

    def unregister(self, callback: Callable):
        with self._lock:
            self.callbacks = [(cb, name) for cb, name in self.callbacks if cb != callback]

    def _handle_signal(self, signum, frame):
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"Received {signal_name}")

        if self.shutting_down:
            logger.warning("Force exit requested (second signal)")
            sys.exit(1)

        self.shutdown()

    def _atexit_handler(self):
        if not self.shutting_down:
            self.shutdown()

    def shutdown(self):
        with self._lock:
            if self.shutting_down:
                return
            self.shutting_down = True

        logger.info("Graceful shutdown initiated...")

        for callback, name in reversed(self.callbacks):
            try:
                logger.debug(f"Running shutdown callback: {name}")
                callback()
            except Exception as e:
                logger.error(f"Shutdown callback error ({name}): {e}")

        logger.info("Shutdown complete")

    def is_shutting_down(self) -> bool:
        return self.shutting_down

    def restore_signals(self):
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm:
            signal.signal(signal.SIGTERM, self._original_sigterm)


_shutdown_handler: ShutdownHandler | None = None


def get_shutdown_handler() -> ShutdownHandler:
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = ShutdownHandler()
    return _shutdown_handler


def setup_graceful_shutdown():
    handler = get_shutdown_handler()
    handler.setup_signals()
    return handler


def register_shutdown_callback(callback: Callable, name: str = None):
    handler = get_shutdown_handler()
    handler.register(callback, name)


def is_shutting_down() -> bool:
    if _shutdown_handler:
        return _shutdown_handler.is_shutting_down()
    return False


def reset_shutdown_handler():
    global _shutdown_handler
    if _shutdown_handler:
        _shutdown_handler.restore_signals()
    _shutdown_handler = None
