from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LiveAudioChunk:
    """Chunk de audio para streaming"""

    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    is_final: bool = False


@dataclass
class LiveResponse:
    """Resposta do Gemini Live"""

    text: str | None = None
    audio_data: bytes | None = None
    is_final: bool = False
    interrupted: bool = False
