from dataclasses import dataclass


@dataclass
class VoiceProfile:
    name: str
    audio_path: str
    exaggeration: float
    cfg_weight: float
    temperature: float
    description: str


@dataclass
class LunaResponse:
    text: str
    audio_path: str | None
    emotion: str
    voice_profile: str
    generation_time: float
    engine: str
