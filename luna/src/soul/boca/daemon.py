from __future__ import annotations

import json
import socket
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.soul.boca.core import Boca

logger = get_logger(__name__)

TTS_SOCKET_PATH = "/tmp/luna_tts_daemon.sock"


def gerar_via_daemon(boca: Boca, texto: str, speed: float = 1.0, exaggeration: float = 0.5) -> str | None:
    if not boca.daemon_disponivel:
        return None

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(30.0)
        sock.connect(TTS_SOCKET_PATH)

        request = {"text": texto, "speed": speed, "exaggeration": exaggeration}

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
            logger.error("Daemon retornou resposta vazia")
            return None

        response = json.loads(response_data.decode("utf-8").strip())

        if response.get("status") == "success":
            path = response.get("path")
            duration = response.get("duration", 0)
            logger.info(f"[DAEMON] Audio gerado em {duration:.2f}s: {path}")
            return path
        else:
            logger.error(f"[DAEMON] Erro: {response.get('message')}")
            return None

    except TimeoutError:
        logger.error("Timeout ao comunicar com daemon TTS")
        boca.daemon_disponivel = False
        return None
    except Exception as e:
        logger.error(f"Erro ao comunicar com daemon TTS: {e}")
        boca.daemon_disponivel = False
        return None
