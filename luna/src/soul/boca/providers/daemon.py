from __future__ import annotations

import json
import os
import socket
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.soul.boca.providers.base import TTSParams, TTSProvider

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)

TTS_SOCKET_PATH = "/tmp/luna_tts_daemon.sock"


class DaemonProvider(TTSProvider):
    name = "daemon"
    priority = 100

    def __init__(self, boca: Boca) -> None:
        super().__init__(boca)
        self._socket_path = TTS_SOCKET_PATH

    def check_availability(self) -> bool:
        if not os.path.exists(self._socket_path):
            self._available = False
            return False

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(self._socket_path)

            request = {"text": "test", "speed": 1.0, "exaggeration": 0.5, "health_check": True}
            sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    break

            sock.close()

            if response_data:
                response = json.loads(response_data.decode("utf-8").strip())
                if response.get("status") in ("success", "ok", "healthy"):
                    self._available = True
                    logger.info("[Daemon] TTS Daemon disponivel")
                    return True

            self._available = False
            return False

        except Exception as e:
            logger.debug(f"[Daemon] Nao disponivel: {e}")
            self._available = False
            return False

    @perf_monitor("tts.provider.daemon.generate")
    def generate(self, text: str, params: TTSParams) -> str | None:
        if not self._available:
            return None

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(30.0)
            sock.connect(self._socket_path)

            request = {
                "text": text,
                "speed": params.speed,
                "exaggeration": params.style,
            }

            sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    break

            sock.close()

            if not response_data:
                logger.error("[Daemon] Retornou resposta vazia")
                return None

            response = json.loads(response_data.decode("utf-8").strip())

            if response.get("status") == "success":
                path = response.get("path")
                duration = response.get("duration", 0)
                logger.info(f"[Daemon] Audio gerado em {duration:.2f}s: {path}")
                return path
            else:
                logger.error(f"[Daemon] Erro: {response.get('message')}")
                return None

        except TimeoutError:
            logger.error("[Daemon] Timeout")
            self._available = False
            return None
        except Exception as e:
            logger.error(f"[Daemon] Erro: {e}")
            self._available = False
            return None

    def speak(self, text: str, params: TTSParams) -> bool:
        if not self._available:
            return False

        try:
            audio_path = self.generate(text, params)

            if not audio_path:
                return False

            from src.soul.boca.playback import play_audio_file

            if play_audio_file(self._boca, audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
                logger.info("[Daemon] TTS executado com sucesso")
                return True

            return False

        except Exception as e:
            logger.error(f"[Daemon] Erro no speak: {e}")
            return False
