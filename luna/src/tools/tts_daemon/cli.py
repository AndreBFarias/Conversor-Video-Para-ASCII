import logging
import os
import signal
import sys
import time

from .constants import DEFAULT_CHATTERBOX_REFERENCE, DEFAULT_COQUI_REFERENCE, PID_FILE
from .daemon import TTSDaemon

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("tts_daemon")

daemon: TTSDaemon | None = None


def signal_handler(signum, frame):
    logger.info(f"Sinal {signum} recebido")
    if daemon is not None:
        daemon.stop()
    sys.exit(0)


def is_daemon_running() -> bool:
    if not os.path.exists(PID_FILE):
        return False

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())

        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return False


def stop_daemon() -> bool:
    if not os.path.exists(PID_FILE):
        print("Daemon nao esta rodando")
        return False

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)

        for _ in range(10):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except OSError:
                print("Daemon parado")
                return True

        os.kill(pid, signal.SIGKILL)
        print("Daemon forcado a parar")
        return True

    except Exception as e:
        print(f"Erro ao parar daemon: {e}")
        return False


def main():
    import argparse

    global daemon

    parser = argparse.ArgumentParser(description="TTS Daemon para Luna")
    parser.add_argument("action", choices=["start", "stop", "status", "restart"], help="Acao a executar")
    parser.add_argument("--engine", choices=["coqui", "chatterbox"], default="coqui", help="Engine TTS a usar")
    parser.add_argument("--reference", type=str, default=None, help="Caminho do audio de referencia")
    parser.add_argument("--no-warmup", action="store_true", help="Nao executar warmup apos carregar modelo")

    args = parser.parse_args()

    if args.action == "status":
        if is_daemon_running():
            print("Daemon esta rodando")
            sys.exit(0)
        else:
            print("Daemon nao esta rodando")
            sys.exit(1)

    elif args.action == "stop":
        if stop_daemon():
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "restart":
        stop_daemon()
        time.sleep(1)

    if args.action in ["start", "restart"]:
        if is_daemon_running():
            print("Daemon ja esta rodando")
            sys.exit(1)

        if not args.reference:
            if args.engine == "coqui" and DEFAULT_COQUI_REFERENCE.exists():
                args.reference = str(DEFAULT_COQUI_REFERENCE)
            elif args.engine == "chatterbox" and DEFAULT_CHATTERBOX_REFERENCE.exists():
                args.reference = str(DEFAULT_CHATTERBOX_REFERENCE)
            else:
                print("ERRO: Reference audio nao especificado e default nao encontrado")
                sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        daemon = TTSDaemon(engine=args.engine, reference_audio=args.reference)

        print(f"Carregando modelo {args.engine}...")
        if not daemon.load_model():
            print("ERRO: Falha ao carregar modelo")
            sys.exit(1)

        if not args.no_warmup:
            daemon.warmup()

        print(f"Iniciando daemon TTS ({args.engine})...")
        daemon.start()
