from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path


@runtime_checkable
class IConfigProvider(Protocol):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any: ...

    @abstractmethod
    def get_nested(self, *keys: str, default: Any = None) -> Any: ...

    @abstractmethod
    def get_api_key(self, provider: str) -> str | None: ...


@runtime_checkable
class IMemoryStore(Protocol):
    @abstractmethod
    def add(self, content: str, source: str = "unknown") -> str | None: ...

    @abstractmethod
    def retrieve(self, query: str, max_chars: int = 600) -> str: ...

    @abstractmethod
    def recall_emotional(self, emotion: str) -> list[dict]: ...

    @abstractmethod
    def get_stats(self) -> dict[str, Any]: ...


@runtime_checkable
class ILLMClient(Protocol):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str: ...

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str: ...

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> Any: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...


@runtime_checkable
class ITTSEngine(Protocol):
    @abstractmethod
    def synthesize(self, text: str) -> bytes | None: ...

    @abstractmethod
    def synthesize_to_file(self, text: str, output_path: Path) -> bool: ...

    @property
    @abstractmethod
    def engine_name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...


@runtime_checkable
class IVisionProvider(Protocol):
    @abstractmethod
    def analyze_image(self, image_path: Path, prompt: str) -> str: ...

    @abstractmethod
    def analyze_base64(self, image_b64: str, prompt: str) -> str: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...


@runtime_checkable
class IContextBuilder(Protocol):
    @abstractmethod
    def build(
        self,
        user_input: str,
        conversation_history: list[dict],
        memory_context: str = "",
    ) -> str: ...

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    @abstractmethod
    def estimate_tokens(self, text: str) -> int: ...


@runtime_checkable
class ISemanticCache(Protocol):
    @abstractmethod
    def get(self, query: str) -> str | None: ...

    @abstractmethod
    def set(self, query: str, response: str) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def get_stats(self) -> dict[str, Any]: ...


@runtime_checkable
class IRateLimiter(Protocol):
    @abstractmethod
    def acquire(self) -> bool: ...

    @abstractmethod
    def wait(self) -> None: ...

    @property
    @abstractmethod
    def requests_remaining(self) -> int: ...


@runtime_checkable
class IEntityLoader(Protocol):
    @abstractmethod
    def get_soul(self) -> str: ...

    @abstractmethod
    def get_config(self) -> dict[str, Any]: ...

    @abstractmethod
    def get_animation_path(self, animation_name: str) -> Path | None: ...

    @property
    @abstractmethod
    def entity_id(self) -> str: ...

    @property
    @abstractmethod
    def entity_name(self) -> str: ...


@runtime_checkable
class IAnimationController(Protocol):
    @abstractmethod
    def play(self, animation_name: str) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def set_default(self, animation_name: str) -> None: ...

    @property
    @abstractmethod
    def current_animation(self) -> str: ...


@runtime_checkable
class IAudioPlayer(Protocol):
    @abstractmethod
    def play(self, audio_data: bytes) -> None: ...

    @abstractmethod
    def play_file(self, file_path: Path) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @property
    @abstractmethod
    def is_playing(self) -> bool: ...


@runtime_checkable
class ILogger(Protocol):
    @abstractmethod
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
