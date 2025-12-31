import json
import logging
from pathlib import Path

from .models import VoiceProfile

logger = logging.getLogger(__name__)


class VoiceManager:
    def __init__(self, voices_dir: Path):
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.voices_dir / "voice_profiles.json"
        self.profiles: dict[str, VoiceProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        self.profiles[name] = VoiceProfile(
                            name=name,
                            audio_path=config_data.get("audio_path", ""),
                            exaggeration=config_data.get("exaggeration", 0.5),
                            cfg_weight=config_data.get("cfg_weight", 0.5),
                            temperature=config_data.get("temperature", 0.8),
                            description=config_data.get("description", ""),
                        )
                logger.info(f"Carregados {len(self.profiles)} perfis de voz")
            except Exception as e:
                logger.error(f"Erro ao carregar perfis de voz: {e}")

    def get_profile(self, name: str) -> VoiceProfile | None:
        return self.profiles.get(name)

    def add_profile(
        self,
        name: str,
        audio_path: str,
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
        description: str = "",
    ) -> None:
        profile = VoiceProfile(name, audio_path, exaggeration, cfg_weight, temperature, description)
        self.profiles[name] = profile
