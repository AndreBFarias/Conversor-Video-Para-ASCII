import logging
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLED = "installed"
    ERROR = "error"


@dataclass
class ModelInfo:
    name: str
    size: str
    description: str
    category: str  # chat, vision, code, embedding
    status: ModelStatus = ModelStatus.NOT_INSTALLED


AVAILABLE_MODELS = {
    "chat": [
        ModelInfo("dolphin-mistral", "4.1GB", "Chat principal, sem censura, bom em JSON", "chat"),
        ModelInfo("llama3.2:3b", "2.0GB", "Fallback rapido, leve", "chat"),
        ModelInfo("llama3.2:1b", "1.3GB", "Ultra leve, basico", "chat"),
        ModelInfo("qwen2.5:3b", "1.9GB", "Alibaba Qwen 2.5", "chat"),
        ModelInfo("gemma2:2b", "1.6GB", "Google Gemma 2B", "chat"),
        ModelInfo("phi3:mini", "2.3GB", "Microsoft Phi-3, compacto", "chat"),
        ModelInfo("tinyllama", "637MB", "Minimo, para testes", "chat"),
    ],
    "vision": [
        ModelInfo("moondream", "1.7GB", "Visao compacta, recomendado", "vision"),
        ModelInfo("llava-phi3", "2.9GB", "Visao media, boa qualidade", "vision"),
        ModelInfo("llava:7b", "4.7GB", "Visao completa (pode exceder VRAM)", "vision"),
    ],
}


class ModelManager:
    def __init__(self):
        self._installed_models: list[str] = []
        self._downloading: dict[str, threading.Thread] = {}
        self._download_progress: dict[str, str] = {}
        self._callbacks: dict[str, Callable] = {}
        self._lock = threading.Lock()
        self.refresh_installed()

    def refresh_installed(self) -> list[str]:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]
                self._installed_models = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_name = parts[0].split(":")[0]
                            self._installed_models.append(model_name)
                            full_name = parts[0]
                            if full_name not in self._installed_models:
                                self._installed_models.append(full_name)

                logger.info(f"Modelos instalados: {self._installed_models}")
            else:
                logger.warning(f"Erro ao listar modelos: {result.stderr}")
                self._installed_models = []

        except FileNotFoundError:
            logger.error("Ollama nao encontrado no sistema")
            self._installed_models = []
        except subprocess.TimeoutExpired:
            logger.error("Timeout ao listar modelos")
            self._installed_models = []
        except Exception as e:
            logger.error(f"Erro ao verificar modelos: {e}")
            self._installed_models = []

        return self._installed_models

    def is_installed(self, model_name: str) -> bool:
        base_name = model_name.split(":")[0]
        return (
            model_name in self._installed_models
            or base_name in self._installed_models
            or any(m.split(":")[0] == base_name for m in self._installed_models)
        )

    def is_downloading(self, model_name: str) -> bool:
        return model_name in self._downloading

    def get_download_progress(self, model_name: str) -> str | None:
        return self._download_progress.get(model_name)

    def get_model_status(self, model_name: str) -> ModelStatus:
        if self.is_downloading(model_name):
            return ModelStatus.DOWNLOADING
        if self.is_installed(model_name):
            return ModelStatus.INSTALLED
        return ModelStatus.NOT_INSTALLED

    def download_model(
        self,
        model_name: str,
        on_progress: Callable[[str, str], None] | None = None,
        on_complete: Callable[[str, bool, str], None] | None = None,
    ) -> bool:
        if self.is_installed(model_name):
            logger.info(f"Modelo {model_name} ja esta instalado")
            if on_complete:
                on_complete(model_name, True, "Ja instalado")
            return True

        if self.is_downloading(model_name):
            logger.warning(f"Modelo {model_name} ja esta sendo baixado")
            return False

        def _download_thread():
            try:
                logger.info(f"Iniciando download do modelo: {model_name}")
                self._download_progress[model_name] = "Iniciando..."

                if on_progress:
                    on_progress(model_name, "Iniciando download...")

                process = subprocess.Popen(
                    ["ollama", "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                for line in iter(process.stdout.readline, ""):
                    line = line.strip()
                    if line:
                        self._download_progress[model_name] = line
                        if on_progress:
                            on_progress(model_name, line)
                        logger.debug(f"[{model_name}] {line}")

                process.wait()

                with self._lock:
                    if model_name in self._downloading:
                        del self._downloading[model_name]
                    if model_name in self._download_progress:
                        del self._download_progress[model_name]

                if process.returncode == 0:
                    self.refresh_installed()
                    logger.info(f"Download concluido: {model_name}")
                    if on_complete:
                        on_complete(model_name, True, "Download concluido")
                else:
                    logger.error(f"Falha no download: {model_name}")
                    if on_complete:
                        on_complete(model_name, False, "Falha no download")

            except Exception as e:
                logger.error(f"Erro no download de {model_name}: {e}")
                with self._lock:
                    if model_name in self._downloading:
                        del self._downloading[model_name]
                if on_complete:
                    on_complete(model_name, False, str(e))

        thread = threading.Thread(target=_download_thread, daemon=True)
        self._downloading[model_name] = thread
        thread.start()

        return True

    def delete_model(self, model_name: str) -> bool:
        try:
            result = subprocess.run(["ollama", "rm", model_name], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self.refresh_installed()
                logger.info(f"Modelo removido: {model_name}")
                return True
            else:
                logger.error(f"Falha ao remover modelo: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Erro ao remover modelo: {e}")
            return False

    def get_available_models(self, category: str = None) -> list[ModelInfo]:
        if category:
            models = AVAILABLE_MODELS.get(category, [])
        else:
            models = []
            for cat_models in AVAILABLE_MODELS.values():
                models.extend(cat_models)

        for model in models:
            model.status = self.get_model_status(model.name)

        return models

    def get_installed_models(self) -> list[str]:
        return list(self._installed_models)

    def ensure_model_available(
        self,
        model_name: str,
        on_progress: Callable[[str, str], None] | None = None,
        on_complete: Callable[[str, bool, str], None] | None = None,
    ) -> bool:
        if self.is_installed(model_name):
            return True

        logger.info(f"Modelo {model_name} nao instalado, iniciando download...")
        return self.download_model(model_name, on_progress, on_complete)

    def check_ollama_running(self) -> bool:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Ollama nao esta rodando: {e}")
            return False

    def start_ollama(self) -> bool:
        try:
            subprocess.Popen(
                ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
            import time

            time.sleep(2)
            return self.check_ollama_running()
        except Exception as e:
            logger.error(f"Erro ao iniciar Ollama: {e}")
            return False


_manager_instance = None


def get_model_manager() -> ModelManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModelManager()
    return _manager_instance
