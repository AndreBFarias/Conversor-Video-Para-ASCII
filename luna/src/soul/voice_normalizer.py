from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import config
from src.core.file_lock import read_json_safe
from src.core.logging_config import get_logger

logger = get_logger(__name__)

EngineType = Literal["coqui", "chatterbox", "elevenlabs"]


@dataclass
class NormalizedVoiceParams:
    stability: float = 0.5
    style: float = 0.5
    speed: float = 1.0
    similarity: float = 0.75

    def to_coqui(self) -> dict:
        return {
            "speed": self.speed,
            "temperature": 1.0 - self.stability,
        }

    def to_chatterbox(self) -> dict:
        return {
            "exaggeration": self.style,
            "cfg_weight": self.stability,
            "temperature": 0.5 + (0.5 * self.style),
        }

    def to_elevenlabs(self) -> dict:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity,
            "style": self.style,
            "use_speaker_boost": self.similarity > 0.7,
        }


class VoiceNormalizer:
    _emotion_map: dict[str, NormalizedVoiceParams] = {
        "neutral": NormalizedVoiceParams(0.5, 0.3, 1.0, 0.75),
        "observando": NormalizedVoiceParams(0.5, 0.3, 1.0, 0.75),
        "happy": NormalizedVoiceParams(0.4, 0.7, 1.1, 0.75),
        "feliz": NormalizedVoiceParams(0.4, 0.7, 1.1, 0.75),
        "sad": NormalizedVoiceParams(0.7, 0.2, 0.9, 0.75),
        "triste": NormalizedVoiceParams(0.7, 0.2, 0.9, 0.75),
        "angry": NormalizedVoiceParams(0.3, 0.8, 1.2, 0.75),
        "irritada": NormalizedVoiceParams(0.3, 0.8, 1.2, 0.75),
        "seductive": NormalizedVoiceParams(0.6, 0.6, 0.95, 0.8),
        "flertando": NormalizedVoiceParams(0.6, 0.6, 0.95, 0.8),
        "apaixonada": NormalizedVoiceParams(0.55, 0.65, 0.95, 0.8),
        "curious": NormalizedVoiceParams(0.5, 0.5, 1.05, 0.75),
        "curiosa": NormalizedVoiceParams(0.5, 0.5, 1.05, 0.75),
        "sarcastic": NormalizedVoiceParams(0.4, 0.6, 1.0, 0.75),
        "sarcastica": NormalizedVoiceParams(0.4, 0.6, 1.0, 0.75),
        "travessa": NormalizedVoiceParams(0.45, 0.65, 1.05, 0.75),
    }

    def __init__(self, entity_id: str | None = None):
        self.entity_id = entity_id or config.get_current_entity_id()
        self.voice_config: dict = {}
        self._load_entity_config()

    def _load_entity_config(self) -> None:
        config_path = config.ENTITIES_DIR / self.entity_id / "config.json"
        if config_path.exists():
            try:
                data = read_json_safe(config_path)
                self.voice_config = data.get("voice", {})
            except Exception as e:
                logger.error(f"Erro ao carregar voice config: {e}")
                self.voice_config = {}
        else:
            self.voice_config = {}

    def get_params_for_engine(
        self,
        engine: EngineType,
        emotion: str = "neutral",
    ) -> dict:
        base_params = self._get_emotion_params(emotion)
        engine_overrides = self.voice_config.get(engine, {})

        for key in ["stability", "style", "speed", "similarity"]:
            if key in engine_overrides:
                setattr(base_params, key, engine_overrides[key])

        if engine == "coqui":
            return base_params.to_coqui()
        elif engine == "chatterbox":
            return base_params.to_chatterbox()
        elif engine == "elevenlabs":
            return base_params.to_elevenlabs()
        else:
            logger.warning(f"Engine desconhecida: {engine}, usando coqui")
            return base_params.to_coqui()

    def _get_emotion_params(self, emotion: str) -> NormalizedVoiceParams:
        emotion_lower = emotion.lower().strip()
        if emotion_lower in self._emotion_map:
            params = self._emotion_map[emotion_lower]
            return NormalizedVoiceParams(
                stability=params.stability,
                style=params.style,
                speed=params.speed,
                similarity=params.similarity,
            )
        return NormalizedVoiceParams()

    def get_reference_audio(self, engine: EngineType) -> str | None:
        if engine == "coqui":
            return config.get_coqui_reference_audio(self.entity_id)
        elif engine == "chatterbox":
            return config.get_chatterbox_reference_audio(self.entity_id)
        elif engine == "elevenlabs":
            return self.voice_config.get("elevenlabs", {}).get("voice_id")
        return None

    def get_speaker_embedding(self, engine: EngineType) -> str | None:
        if engine == "coqui":
            return config.get_coqui_speaker_embedding(self.entity_id)
        return None

    def reload_for_entity(self, entity_id: str) -> None:
        self.entity_id = entity_id
        self._load_entity_config()
        logger.info(f"VoiceNormalizer recarregado para: {entity_id}")


_normalizer_instance: VoiceNormalizer | None = None


def get_voice_normalizer(entity_id: str | None = None) -> VoiceNormalizer:
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = VoiceNormalizer(entity_id)
    elif entity_id and entity_id != _normalizer_instance.entity_id:
        _normalizer_instance.reload_for_entity(entity_id)
    return _normalizer_instance


def reset_voice_normalizer() -> None:
    global _normalizer_instance
    _normalizer_instance = None
