import os
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

SCRIPT_DIR = Path(__file__).parent.parent.parent.parent
TTS_CACHE_DIR = SCRIPT_DIR / "src" / "models" / "tts"

os.environ["TTS_HOME"] = str(TTS_CACHE_DIR)
os.environ["HF_HOME"] = str(TTS_CACHE_DIR)
os.environ["TORCH_HOME"] = str(TTS_CACHE_DIR)

SOCKET_PATH = "/tmp/luna_tts_daemon.sock"
PID_FILE = "/tmp/luna_tts_daemon.pid"

DEFAULT_COQUI_REFERENCE = SCRIPT_DIR / "src" / "models" / "echoes" / "coqui" / "luna" / "reference.wav"
DEFAULT_CHATTERBOX_REFERENCE = SCRIPT_DIR / "src" / "models" / "echoes" / "chatterbox" / "luna" / "reference.wav"
