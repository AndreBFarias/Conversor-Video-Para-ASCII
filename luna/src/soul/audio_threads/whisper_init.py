from __future__ import annotations

import time

import numpy as np

import config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class WhisperModelManager:
    def __init__(self, whisper_config: dict):
        self.whisper_config = whisper_config
        self.model = None
        self.model_loaded = False
        self.load_error = None
        self._warmup_done = False

    def initialize(self) -> bool:
        import os
        import sys

        from faster_whisper import WhisperModel

        model_size = self.whisper_config["MODEL_SIZE"]
        compute_type = self.whisper_config["COMPUTE_TYPE"]
        use_gpu = self.whisper_config["USE_GPU"]
        device = "cuda" if use_gpu else "cpu"

        download_root = str(config.WHISPER_MODELS_DIR)

        def _try_load(dev: str, ctype: str) -> bool:
            logger.info("=" * 50)
            logger.info("[WHISPER] INICIANDO CARREGAMENTO DO MODELO")
            logger.info(f"[WHISPER]   Modelo: {model_size}")
            logger.info(f"[WHISPER]   Device: {dev.upper()}")
            logger.info(f"[WHISPER]   Compute Type: {ctype}")
            logger.info(f"[WHISPER]   Download root: {download_root}")
            logger.info("=" * 50)

            start_load = time.time()

            old_stderr = sys.stderr
            try:
                sys.stderr = open(os.devnull, "w")
                self.model = WhisperModel(model_size, device=dev, compute_type=ctype, download_root=download_root)
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr

            load_time = time.time() - start_load

            logger.info("=" * 50)
            logger.info("[WHISPER] MODELO CARREGADO COM SUCESSO")
            logger.info(f"[WHISPER]   Device: {dev.upper()}")
            logger.info(f"[WHISPER]   Tempo: {load_time:.1f}s")
            logger.info("=" * 50)
            return True

        try:
            _try_load(device, compute_type)
            self.model_loaded = True
            return True

        except RuntimeError as e:
            cuda_errors = ["CUDA", "cuda", "GPU", "no device", "out of memory"]
            is_cuda_error = any(err in str(e) for err in cuda_errors)

            if is_cuda_error and device == "cuda":
                logger.warning("=" * 50)
                logger.warning("[WHISPER] CUDA indisponivel, tentando CPU...")
                logger.warning(f"[WHISPER]   Erro original: {e}")
                logger.warning("=" * 50)

                try:
                    cpu_compute = "int8" if compute_type == "float16" else compute_type
                    _try_load("cpu", cpu_compute)
                    self.model_loaded = True
                    logger.info("[WHISPER] Fallback para CPU bem-sucedido")
                    return True
                except Exception as cpu_e:
                    self.load_error = f"CUDA: {e} | CPU: {cpu_e}"
                    logger.error(f"[WHISPER] Fallback CPU tambem falhou: {cpu_e}")
                    return False
            else:
                self.load_error = str(e)
                logger.error(f"[WHISPER] Erro nao relacionado a CUDA: {e}", exc_info=True)
                return False

        except Exception as e:
            self.load_error = str(e)
            logger.error("=" * 50)
            logger.error("[WHISPER] ERRO AO CARREGAR MODELO")
            logger.error(f"[WHISPER]   Modelo: {model_size}")
            logger.error(f"[WHISPER]   Erro: {e}")
            logger.error("[WHISPER] Verifique:")
            logger.error("[WHISPER]   1. Se o modelo existe (large-v3-turbo, medium, small, etc)")
            logger.error("[WHISPER]   2. Se ha espaco em disco suficiente")
            logger.error("[WHISPER]   3. Se a conexao com internet esta ativa")
            logger.error("=" * 50, exc_info=True)
            return False

    def warmup(self):
        if not self.model or self._warmup_done:
            return

        logger.info("[WHISPER] Executando warmup do modelo...")
        try:
            start = time.time()
            dummy_audio = np.zeros(16000, dtype=np.float32)
            segments, _ = self.model.transcribe(dummy_audio, language="pt", beam_size=1, best_of=1)
            list(segments)
            logger.info(f"[WHISPER] Warmup concluido em {time.time() - start:.2f}s")
            self._warmup_done = True
        except Exception as e:
            logger.warning(f"[WHISPER] Warmup falhou (nao critico): {e}")

    def health_check(self) -> bool:
        if not self.model_loaded or not self.model:
            logger.error("[WHISPER] Health check falhou: modelo nao carregado")
            return False

        try:
            dummy_audio = np.zeros(1600, dtype=np.float32)
            segments, _ = self.model.transcribe(dummy_audio, language="pt", beam_size=1)
            list(segments)
            logger.info("[WHISPER] Health check OK")
            return True
        except Exception as e:
            logger.error(f"[WHISPER] Health check falhou: {e}")
            return False

    def transcribe(self, audio_float32: np.ndarray, whisper_params: dict) -> str:
        base_prompt = whisper_params.get("INITIAL_PROMPT", "Conversa em portugues brasileiro com Luna.")
        keywords = whisper_params.get("KEYWORDS", "")
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
            if keyword_list:
                base_prompt = f"{base_prompt} Palavras comuns: {', '.join(keyword_list)}."

        segments, _ = self.model.transcribe(
            audio_float32,
            language="pt",
            beam_size=whisper_params.get("BEAM_SIZE", 10),
            best_of=whisper_params.get("BEST_OF", 5),
            initial_prompt=base_prompt,
            condition_on_previous_text=whisper_params.get("CONDITION_ON_PREVIOUS", False),
            no_speech_threshold=whisper_params.get("NO_SPEECH_THRESHOLD", 0.6),
            log_prob_threshold=whisper_params.get("LOG_PROB_THRESHOLD", -0.8),
            compression_ratio_threshold=whisper_params.get("COMPRESSION_RATIO_THRESHOLD", 2.4),
            vad_filter=whisper_params.get("VAD_FILTER", True),
            vad_parameters=dict(min_silence_duration_ms=whisper_params.get("VAD_MIN_SILENCE_MS", 500)),
        )

        return " ".join([seg.text for seg in segments]).strip()
