from src.tools.tts_daemon import (
    DEFAULT_CHATTERBOX_REFERENCE,
    DEFAULT_COQUI_REFERENCE,
    PID_FILE,
    SOCKET_PATH,
    TTS_CACHE_DIR,
    TTSDaemon,
    is_daemon_running,
    main,
    stop_daemon,
)

__all__ = [
    "TTSDaemon",
    "is_daemon_running",
    "stop_daemon",
    "main",
    "SOCKET_PATH",
    "PID_FILE",
    "TTS_CACHE_DIR",
    "DEFAULT_COQUI_REFERENCE",
    "DEFAULT_CHATTERBOX_REFERENCE",
]

if __name__ == "__main__":
    main()
