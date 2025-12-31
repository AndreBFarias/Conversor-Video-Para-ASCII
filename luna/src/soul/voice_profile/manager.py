import json
import logging
from datetime import datetime

import numpy as np

import config

logger = logging.getLogger(__name__)


class VoiceProfileManager:
    def __init__(self):
        self.user_dir = config.USER_DATA_DIR
        self.user_dir.mkdir(parents=True, exist_ok=True)

        self.encoder = None
        self.user_embedding: np.ndarray | None = None
        self._loaded = False
        self._similarity_threshold = config.VOICE_SIMILARITY_THRESHOLD

    def _load_encoder(self) -> bool:
        if self.encoder is not None:
            return True

        try:
            from resemblyzer import VoiceEncoder

            logger.info("Carregando VoiceEncoder (resemblyzer)...")
            self.encoder = VoiceEncoder()
            logger.info("VoiceEncoder carregado")
            return True
        except ImportError:
            logger.warning("resemblyzer nao instalado. Voice profile desativado.")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar VoiceEncoder: {e}")
            return False

    def _load_user_embedding(self):
        embedding_path = self.user_dir / "voice_embedding.npy"
        if embedding_path.exists():
            try:
                self.user_embedding = np.load(embedding_path)
                self._loaded = True
                logger.info("Voice embedding do usuario carregado")
            except Exception as e:
                logger.error(f"Erro ao carregar voice embedding: {e}")

    def extract_embedding(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray | None:
        if not self._load_encoder():
            return None

        try:
            from resemblyzer import preprocess_wav

            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                else:
                    audio_data = audio_data.astype(np.float32)

            wav = preprocess_wav(audio_data, source_sr=sample_rate)
            embedding = self.encoder.embed_utterance(wav)
            return embedding
        except Exception as e:
            logger.error(f"Erro ao extrair embedding de voz: {e}")
            return None

    def save_user_voice(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bool:
        embedding = self.extract_embedding(audio_data, sample_rate)
        if embedding is None:
            return False

        try:
            np.save(self.user_dir / "voice_embedding.npy", embedding)
            self.user_embedding = embedding
            self._loaded = True

            samples_dir = self.user_dir / "voice_samples"
            samples_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sample_path = samples_dir / f"sample_{timestamp}.wav"

            try:
                import soundfile as sf

                sf.write(sample_path, audio_data, sample_rate)
                logger.info(f"Amostra de voz salva: {sample_path.name}")
            except ImportError:
                logger.warning("soundfile nao instalado, amostra nao salva")

            self._update_profile(
                {
                    "voice_saved": True,
                    "last_voice_update": timestamp,
                    "voice_sample_count": len(list(samples_dir.glob("*.wav"))),
                }
            )

            logger.info("Voice embedding do usuario salvo com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar voz do usuario: {e}")
            return False

    def identify_speaker(self, audio_data: np.ndarray, sample_rate: int = 16000) -> tuple[bool, float]:
        if self.user_embedding is None:
            self._load_user_embedding()
            if self.user_embedding is None:
                return False, 0.0

        embedding = self.extract_embedding(audio_data, sample_rate)
        if embedding is None:
            return False, 0.0

        try:
            similarity = float(np.dot(self.user_embedding, embedding))
            is_user = similarity > self._similarity_threshold

            logger.debug(f"Speaker similarity: {similarity:.3f} (user: {is_user})")
            return is_user, similarity
        except Exception as e:
            logger.error(f"Erro ao identificar speaker: {e}")
            return False, 0.0

    def _update_profile(self, data: dict):
        profile_path = self.user_dir / "profile.json"

        try:
            if profile_path.exists():
                with open(profile_path, encoding="utf-8") as f:
                    profile = json.load(f)
            else:
                profile = {}

            profile.update(data)
            profile["updated_at"] = datetime.now().isoformat()

            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao atualizar profile: {e}")

    def get_profile(self) -> dict:
        profile_path = self.user_dir / "profile.json"
        if profile_path.exists():
            try:
                with open(profile_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Erro ao ler voice profile: {e}")
        return {}

    @property
    def has_voice_profile(self) -> bool:
        return (self.user_dir / "voice_embedding.npy").exists()
