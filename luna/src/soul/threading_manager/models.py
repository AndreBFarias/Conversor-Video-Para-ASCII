from dataclasses import dataclass
from enum import Enum


class ThreadState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class AudioChunk:
    data: bytes
    sample_rate: int
    timestamp: float


@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    timestamp: float
    metadata: dict | None = None


@dataclass
class ProcessingRequest:
    user_text: str
    visual_context: str | None = None
    attached_content: str | None = None
    forced_animation: str | None = None
    timestamp: float = 0.0


@dataclass
class LunaResponse:
    fala_tts: str
    log_terminal: str
    animacao: str
    tts_config: dict
    metadata: dict


@dataclass
class TTSChunk:
    audio_data: bytes
    chunk_index: int
    total_chunks: int
    format: str = "wav"
