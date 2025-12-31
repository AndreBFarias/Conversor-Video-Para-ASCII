import logging
import time

import numpy as np

import config
from src.core.entity_loader import get_active_entity

logger = logging.getLogger(__name__)


class WakeWordDetector:
    GREETING_RESPONSES = [
        "Me chamou?",
        "Diga.",
        "Estou aqui.",
        "O que foi?",
        "Sim?",
        "Pode falar.",
        "Te escuto.",
        "Fala, mortal.",
        "Presente.",
        "Em que posso ajudar?",
    ]

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._response_index = 0
        self._last_detection_time = 0
        self._cooldown = config.WAKE_WORD_COOLDOWN
        self._loaded = False
        self._whisper_model = None
        self._vad = None
        self._audio_buffer = []
        self._min_audio_length = int(sample_rate * 0.5)
        self._max_audio_length = int(sample_rate * 3.0)

        self._patterns = self._get_patterns()

    def _get_patterns(self) -> list:
        entity_id = get_active_entity()
        return getattr(config, "WAKE_WORD_PATTERNS", config.get_wake_word_patterns(entity_id))

    def reload_patterns(self, entity_id: str = None):
        if entity_id:
            self._patterns = config.get_wake_word_patterns(entity_id)
        else:
            self._patterns = self._get_patterns()
        logger.info(f"Wake word patterns recarregados: {self._patterns[:3]}...")

    def load_model(self, whisper_model=None) -> bool:
        try:
            import webrtcvad

            self._vad = webrtcvad.Vad(config.VAD_CONFIG.get("MODE", 2))
            logger.info("VAD carregado para wake word")
        except ImportError:
            logger.error("webrtcvad nao instalado")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar VAD: {e}")
            return False

        if whisper_model:
            self._whisper_model = whisper_model
            self._loaded = True
            logger.info("Wake word usando modelo Whisper compartilhado")
            return True

        try:
            from faster_whisper import WhisperModel

            model_size = config.WHISPER_CONFIG.get("MODEL_SIZE", "small")
            compute_type = config.WHISPER_CONFIG.get("COMPUTE_TYPE", "int8")
            use_gpu = config.WHISPER_CONFIG.get("USE_GPU", False)
            device = "cuda" if use_gpu else "cpu"

            self._whisper_model = WhisperModel(
                model_size, device=device, compute_type=compute_type, download_root=str(config.WHISPER_MODELS_DIR)
            )
            self._loaded = True
            logger.info(f"Whisper carregado para wake word: {model_size}")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar Whisper para wake word: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def detect(self, audio_chunk: bytes) -> tuple[bool, str | None]:
        if not self._loaded:
            return False, None

        now = time.time()
        if now - self._last_detection_time < self._cooldown:
            return False, None

        try:
            if isinstance(audio_chunk, np.ndarray):
                audio_data = (audio_chunk * 32767).astype(np.int16).tobytes()
            elif hasattr(audio_chunk, "tobytes"):
                audio_data = audio_chunk.tobytes()
            else:
                audio_data = audio_chunk

            frame_duration = 30
            frame_length = int(self.sample_rate * frame_duration / 1000) * 2

            if len(audio_data) < frame_length:
                return False, None

            frame = audio_data[:frame_length]
            is_speech = self._vad.is_speech(frame, self.sample_rate)

            if is_speech:
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                self._audio_buffer.extend(audio_np.tolist())

                if len(self._audio_buffer) > self._max_audio_length:
                    self._audio_buffer = self._audio_buffer[-self._max_audio_length :]

            else:
                if len(self._audio_buffer) >= self._min_audio_length:
                    audio_array = np.array(self._audio_buffer, dtype=np.float32)
                    transcript = self._transcribe(audio_array)

                    self._audio_buffer = []

                    if transcript and self._matches_pattern(transcript):
                        self._last_detection_time = now
                        logger.info(f"Wake word detectado: '{transcript}'")
                        return True, transcript

                self._audio_buffer = []

        except Exception as e:
            logger.debug(f"Erro na deteccao wake word: {e}")

        return False, None

    def _transcribe(self, audio_array: np.ndarray) -> str | None:
        if not self._whisper_model:
            return None

        try:
            segments, _ = self._whisper_model.transcribe(
                audio_array,
                language="pt",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=False,
                without_timestamps=True,
            )

            text = " ".join(seg.text for seg in segments).strip().lower()
            return text if text else None

        except Exception as e:
            logger.debug(f"Erro na transcricao wake word: {e}")
            return None

    def _matches_pattern(self, text: str) -> bool:
        text_normalized = self._normalize(text)
        for pattern in self._patterns:
            pattern_normalized = self._normalize(pattern)
            if pattern_normalized in text_normalized:
                return True
        return False

    def _normalize(self, text: str) -> str:
        replacements = {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
        }
        result = text.lower()
        for k, v in replacements.items():
            result = result.replace(k, v)
        return result

    def get_greeting(self) -> str:
        response = self.GREETING_RESPONSES[self._response_index]
        self._response_index = (self._response_index + 1) % len(self.GREETING_RESPONSES)
        return response

    def reset(self):
        self._audio_buffer = []
