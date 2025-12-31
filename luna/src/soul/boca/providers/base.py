from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.soul.boca.core import Boca


@dataclass
class TTSParams:
    speed: float = 1.0
    stability: float = 0.5
    style: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_metatags(cls, metatags: dict | None) -> TTSParams:
        if not metatags:
            return cls()
        return cls(
            speed=metatags.get("speed", 1.0),
            stability=metatags.get("stability", 0.5),
            style=metatags.get("style", 0.0),
            extra=metatags.get("extra", {}),
        )


class TTSProvider(ABC):
    name: str = "base"
    priority: int = 0

    def __init__(self, boca: Boca) -> None:
        self._boca = boca
        self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    @abstractmethod
    def check_availability(self) -> bool:
        pass

    @abstractmethod
    def generate(self, text: str, params: TTSParams) -> str | None:
        pass

    @abstractmethod
    def speak(self, text: str, params: TTSParams) -> bool:
        pass

    def get_reference_audio(self) -> str | None:
        return None

    def __repr__(self) -> str:
        status = "OK" if self._available else "N/A"
        return f"<{self.__class__.__name__} [{status}]>"
