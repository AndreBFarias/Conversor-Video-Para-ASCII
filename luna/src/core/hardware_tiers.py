import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class HardwareTier(Enum):
    PREMIUM = "premium"
    BALANCED = "balanced"
    LIGHT = "light"
    MINIMAL = "minimal"


@dataclass
class HardwareInfo:
    gpu_name: str | None = None
    gpu_vram_gb: float = 0.0
    ram_gb: float = 0.0
    cpu_cores: int = 1
    has_cuda: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": round(self.gpu_vram_gb, 1),
            "ram_gb": round(self.ram_gb, 1),
            "cpu_cores": self.cpu_cores,
            "has_cuda": self.has_cuda,
        }


@dataclass
class TierConfig:
    tier: HardwareTier
    llm_model: str
    llm_provider: str
    tts_engine: str
    stt_model: str
    use_gpu: bool
    max_context: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value,
            "llm": {"model": self.llm_model, "provider": self.llm_provider},
            "tts": {"engine": self.tts_engine},
            "stt": {"model": self.stt_model},
            "use_gpu": self.use_gpu,
            "max_context": self.max_context,
        }


TIER_CONFIGS = {
    HardwareTier.PREMIUM: TierConfig(
        tier=HardwareTier.PREMIUM,
        llm_model="dolphin-mistral",
        llm_provider="ollama",
        tts_engine="xtts",
        stt_model="medium",
        use_gpu=True,
        max_context=8192,
    ),
    HardwareTier.BALANCED: TierConfig(
        tier=HardwareTier.BALANCED,
        llm_model="dolphin-mistral",
        llm_provider="ollama",
        tts_engine="xtts",
        stt_model="small",
        use_gpu=True,
        max_context=4096,
    ),
    HardwareTier.LIGHT: TierConfig(
        tier=HardwareTier.LIGHT,
        llm_model="llama3.2:3b",
        llm_provider="ollama",
        tts_engine="piper",
        stt_model="small",
        use_gpu=True,
        max_context=2048,
    ),
    HardwareTier.MINIMAL: TierConfig(
        tier=HardwareTier.MINIMAL,
        llm_model="llama3.2:3b",
        llm_provider="ollama",
        tts_engine="piper",
        stt_model="tiny",
        use_gpu=False,
        max_context=1024,
    ),
}


class HardwareDetector:
    def __init__(self):
        self.info = self._detect()

    def _detect(self) -> HardwareInfo:
        info = HardwareInfo()

        info.ram_gb = self._detect_ram()
        info.cpu_cores = os.cpu_count() or 1

        gpu_info = self._detect_gpu()
        info.gpu_name = gpu_info.get("name")
        info.gpu_vram_gb = gpu_info.get("vram_gb", 0.0)
        info.has_cuda = gpu_info.get("has_cuda", False)

        logger.info(
            f"Hardware detectado: GPU={info.gpu_name}, "
            f"VRAM={info.gpu_vram_gb:.1f}GB, "
            f"RAM={info.ram_gb:.1f}GB, "
            f"Cores={info.cpu_cores}"
        )

        return info

    def _detect_ram(self) -> float:
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            return kb / (1024**2)
            except Exception as e:
                logger.debug(f"Erro ao ler /proc/meminfo: {e}")
        except Exception as e:
            logger.debug(f"Erro ao detectar RAM: {e}")

        return 8.0

    def _detect_gpu(self) -> dict:
        result = {"name": None, "vram_gb": 0.0, "has_cuda": False}

        try:
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if proc.returncode == 0:
                output = proc.stdout.strip()
                if output:
                    parts = output.split(", ")
                    if len(parts) >= 2:
                        result["name"] = parts[0].strip()
                        vram_mb = float(parts[1].strip())
                        result["vram_gb"] = vram_mb / 1024
                        result["has_cuda"] = True

        except FileNotFoundError:
            logger.debug("nvidia-smi nao encontrado - sem GPU NVIDIA")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi timeout")
        except Exception as e:
            logger.debug(f"Erro ao detectar GPU: {e}")

        return result

    def determine_tier(self) -> HardwareTier:
        if self.info.has_cuda:
            if self.info.gpu_vram_gb >= 6:
                return HardwareTier.PREMIUM
            elif self.info.gpu_vram_gb >= 4:
                return HardwareTier.BALANCED
            elif self.info.gpu_vram_gb >= 2:
                return HardwareTier.LIGHT

        if self.info.ram_gb >= 16:
            return HardwareTier.LIGHT
        elif self.info.ram_gb >= 8:
            return HardwareTier.MINIMAL

        return HardwareTier.MINIMAL

    def get_config(self) -> TierConfig:
        tier = self.determine_tier()
        return TIER_CONFIGS[tier]


_cached_detector: HardwareDetector | None = None


def get_hardware_detector() -> HardwareDetector:
    global _cached_detector
    if _cached_detector is None:
        _cached_detector = HardwareDetector()
    return _cached_detector


def get_hardware_config() -> TierConfig:
    detector = get_hardware_detector()
    config = detector.get_config()
    logger.info(f"Tier selecionado: {config.tier.value}")
    return config


def apply_hardware_config(config: TierConfig) -> None:
    try:
        import config as cfg

        if hasattr(cfg, "WHISPER_CONFIG"):
            cfg.WHISPER_CONFIG["MODEL_SIZE"] = config.stt_model
            cfg.WHISPER_CONFIG["USE_GPU"] = config.use_gpu

        if config.llm_provider == "ollama":
            if hasattr(cfg, "CHAT_PROVIDER"):
                cfg.CHAT_PROVIDER = "local"
            if hasattr(cfg, "CHAT_LOCAL"):
                cfg.CHAT_LOCAL["model"] = config.llm_model
                cfg.CHAT_LOCAL["context_length"] = config.max_context

        if hasattr(cfg, "TTS_ENGINE"):
            cfg.TTS_ENGINE = config.tts_engine

        logger.info(
            f"Config aplicada: LLM={config.llm_model}, "
            f"TTS={config.tts_engine}, "
            f"STT={config.stt_model}, "
            f"GPU={config.use_gpu}"
        )

    except Exception as e:
        logger.error(f"Erro ao aplicar config de hardware: {e}")


def get_tier_for_vram(vram_gb: float) -> HardwareTier:
    if vram_gb >= 6:
        return HardwareTier.PREMIUM
    elif vram_gb >= 4:
        return HardwareTier.BALANCED
    elif vram_gb >= 2:
        return HardwareTier.LIGHT
    return HardwareTier.MINIMAL


def get_tier_description(tier: HardwareTier) -> str:
    descriptions = {
        HardwareTier.PREMIUM: "RTX 3060+, 16GB RAM - Dolphin-Mistral, XTTS, contexto 8K",
        HardwareTier.BALANCED: "RTX 3050, 8GB RAM - Dolphin-Mistral, XTTS, contexto 4K",
        HardwareTier.LIGHT: "GPU integrada, 8GB RAM - Llama3.2:3b, Piper, contexto 2K",
        HardwareTier.MINIMAL: "CPU only, 4GB RAM - Llama3.2:3b, Piper, contexto 1K",
    }
    return descriptions.get(tier, "Tier desconhecido")
