import json
import logging
import os
import socket
import threading
import time
import uuid
from pathlib import Path

from .constants import PID_FILE, SOCKET_PATH


RAM_DISK_PATH = Path("/dev/shm")
FALLBACK_PATH = Path("/tmp")
AUDIO_PREFIX = "luna_daemon_"


def get_temp_audio_path(suffix: str = ".wav") -> str:
    if RAM_DISK_PATH.exists() and os.access(RAM_DISK_PATH, os.W_OK):
        base_dir = RAM_DISK_PATH
    else:
        base_dir = FALLBACK_PATH

    filename = f"{AUDIO_PREFIX}{uuid.uuid4()}{suffix}"
    return str(base_dir / filename)


logger = logging.getLogger("tts_daemon")


class TTSDaemon:
    def __init__(self, engine: str = "coqui", reference_audio: str = None):
        self.engine = engine.lower()
        self.reference_audio = reference_audio
        self.model = None
        self.device = None
        self.running = False
        self.server_socket = None
        self._lock = threading.Lock()

    def load_model(self) -> bool:
        try:
            import torch

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Device: {self.device}")

            if self.engine == "coqui":
                return self._load_coqui()
            elif self.engine == "chatterbox":
                return self._load_chatterbox()
            else:
                logger.error(f"Engine desconhecido: {self.engine}")
                return False

        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False

    def _load_coqui(self) -> bool:
        try:
            import torch

            original_load = torch.load

            def patched_load(*args, **kwargs):
                if "weights_only" not in kwargs:
                    kwargs["weights_only"] = False
                return original_load(*args, **kwargs)

            torch.load = patched_load

            from TTS.api import TTS

            logger.info("Carregando modelo Coqui XTTS v2...")
            start = time.time()

            self.model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
            self.model.to(self.device)

            logger.info(f"Coqui carregado em {time.time() - start:.1f}s")
            return True

        except ImportError:
            logger.error("TTS (Coqui) nao instalado")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar Coqui: {e}")
            return False

    def _load_chatterbox(self) -> bool:
        try:
            from chatterbox.tts import ChatterboxTTS

            logger.info("Carregando modelo Chatterbox...")
            start = time.time()

            self.model = ChatterboxTTS.from_pretrained(device=self.device)

            logger.info(f"Chatterbox carregado em {time.time() - start:.1f}s")
            return True

        except ImportError:
            logger.error("Chatterbox nao instalado")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar Chatterbox: {e}")
            return False

    def generate(self, text: str, reference_audio: str = None, speed: float = 1.0, exaggeration: float = 0.5) -> str:
        with self._lock:
            try:
                output_path = get_temp_audio_path(".wav")
                ref_audio = reference_audio or self.reference_audio

                if not ref_audio or not os.path.exists(ref_audio):
                    logger.error(f"Reference audio invalido: {ref_audio}")
                    return None

                if self.engine == "coqui":
                    self.model.tts_to_file(
                        text=text, file_path=output_path, speaker_wav=ref_audio, language="pt", speed=speed
                    )
                elif self.engine == "chatterbox":
                    import torchaudio

                    wav = self.model.generate(text=text, audio_prompt_path=ref_audio, exaggeration=exaggeration)
                    torchaudio.save(output_path, wav, self.model.sr)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path

                return None

            except Exception as e:
                logger.error(f"Erro na geracao: {e}")
                return None

    def warmup(self):
        if not self.reference_audio:
            logger.warning("Sem reference audio para warmup")
            return

        logger.info("Executando warmup...")
        start = time.time()

        result = self.generate("Teste.", self.reference_audio)
        if result:
            os.remove(result)
            logger.info(f"Warmup concluido em {time.time() - start:.1f}s")
        else:
            logger.warning("Warmup falhou")

    def handle_client(self, client_socket):
        try:
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break

            if not data:
                return

            request = json.loads(data.decode("utf-8").strip())

            text = request.get("text", "")
            ref_audio = request.get("reference_audio", self.reference_audio)
            speed = request.get("speed", 1.0)
            exaggeration = request.get("exaggeration", 0.5)

            if not text.strip():
                response = {"status": "error", "message": "Texto vazio"}
            else:
                logger.info(f"Gerando: '{text[:40]}...'")
                start = time.time()

                output_path = self.generate(text, ref_audio, speed, exaggeration)

                if output_path:
                    duration = time.time() - start
                    logger.info(f"Gerado em {duration:.2f}s: {output_path}")
                    response = {"status": "success", "path": output_path, "duration": duration}
                else:
                    response = {"status": "error", "message": "Falha na geracao"}

            client_socket.sendall((json.dumps(response) + "\n").encode("utf-8"))

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalido: {e}")
            response = {"status": "error", "message": "JSON invalido"}
            client_socket.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except Exception as e:
            logger.error(f"Erro ao processar cliente: {e}")
        finally:
            client_socket.close()

    def start(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(SOCKET_PATH)
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        os.chmod(SOCKET_PATH, 0o666)

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        self.running = True
        logger.info(f"Daemon iniciado em {SOCKET_PATH}")

        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.daemon = True
                thread.start()
            except TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Erro no servidor: {e}")

        self.cleanup()

    def cleanup(self):
        logger.info("Encerrando daemon...")

        if self.server_socket:
            self.server_socket.close()

        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

        logger.info("Daemon encerrado")

    def stop(self):
        self.running = False
