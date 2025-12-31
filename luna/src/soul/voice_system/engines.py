import hashlib
import logging
import subprocess
from pathlib import Path

import torch
import torchaudio as ta

import config

try:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    CHATTERBOX_AVAILABLE = True
except ImportError:
    CHATTERBOX_AVAILABLE = False

logger = logging.getLogger(__name__)


class CoquiTTSEngine:
    def __init__(self):
        self.project_root = config.APP_DIR
        self.venv_tts_python = self.project_root / "venv_tts" / "bin" / "python"
        self.tts_wrapper = self.project_root / "src" / "tools" / "tts_wrapper.py"
        self.output_dir = config.APP_DIR / "src" / "temp" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.venv_tts_python.exists():
            logger.warning(f"venv_tts Python not found at {self.venv_tts_python}")
        if not self.tts_wrapper.exists():
            logger.warning(f"TTS wrapper not found at {self.tts_wrapper}")

    def is_available(self) -> bool:
        return self.venv_tts_python.exists() and self.tts_wrapper.exists()

    def generate(self, text: str, reference_audio: str | None = None, speed: float = 1.0) -> str | None:
        if not self.is_available():
            logger.error("Coqui TTS environment not available")
            return None

        if not reference_audio or not Path(reference_audio).exists():
            default_ref = config.APP_DIR / "src" / "models" / "echoes" / "coqui" / "luna" / "reference.wav"
            if default_ref.exists():
                reference_audio = str(default_ref)
            else:
                logger.error(f"Reference audio not found: {reference_audio}")
                return None

        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_file = self.output_dir / f"luna_tts_{text_hash}.wav"

        try:
            cmd = [
                str(self.venv_tts_python),
                str(self.tts_wrapper),
                text,
                str(output_file),
                str(reference_audio),
                str(speed),
            ]

            logger.info(f"Calling TTS wrapper: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and "SUCCESS:" in result.stdout:
                logger.info(f"TTS generation successful: {output_file}")
                return str(output_file)
            else:
                logger.error(f"TTS generation failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("TTS generation timed out")
            return None
        except Exception as e:
            logger.error(f"TTS subprocess error: {e}")
            return None


class ChatterboxEngine:
    def __init__(self, device: str = "cuda"):
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.model = None
        self.sr = None
        if CHATTERBOX_AVAILABLE:
            self._initialize_model()
        else:
            logger.warning("Biblioteca Chatterbox nao disponivel.")

    def _initialize_model(self) -> None:
        try:
            logger.info(f"Carregando Chatterbox no device: {self.device}")
            self.model = ChatterboxMultilingualTTS.from_pretrained(device=self.device)
            self.sr = self.model.sr
            logger.info(f"Modelo Chatterbox carregado. Sample rate: {self.sr}")
        except Exception as e:
            logger.error(f"Erro ao inicializar Chatterbox: {e}")
            self.model = None

    def generate(
        self,
        text: str,
        voice_sample: str | None = None,
        language: str = "pt",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
    ) -> torch.Tensor | None:
        if not self.model:
            return None

        try:
            if voice_sample and Path(voice_sample).exists():
                wav = self.model.generate(
                    text,
                    audio_prompt_path=voice_sample,
                    language_id=language,
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    temperature=temperature,
                )
            else:
                wav = self.model.generate(
                    text,
                    language_id=language,
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    temperature=temperature,
                )
            return wav
        except Exception as e:
            logger.error(f"Erro na geracao Chatterbox: {e}")
            return None

    def save_audio(self, wav: torch.Tensor, output_path: str) -> None:
        if self.sr:
            ta.save(output_path, wav, self.sr)

    def cleanup(self) -> None:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
