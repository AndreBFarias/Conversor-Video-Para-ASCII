from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path


@runtime_checkable
class IConsciencia(Protocol):
    @abstractmethod
    def processar(
        self,
        user_input: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
        force_animation: str | None = None,
    ) -> Any: ...

    @abstractmethod
    def stream_processar(
        self,
        user_input: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
    ) -> Any: ...

    @property
    @abstractmethod
    def conversation_history(self) -> list[dict]: ...


@runtime_checkable
class IBoca(Protocol):
    @abstractmethod
    def falar(self, texto: str) -> None: ...

    @abstractmethod
    def parar(self) -> None: ...

    @property
    @abstractmethod
    def is_speaking(self) -> bool: ...


@runtime_checkable
class IVisao(Protocol):
    @abstractmethod
    def olhar(self) -> str: ...

    @abstractmethod
    def analisar_imagem(self, image_path: Path) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...


@runtime_checkable
class IOuvido(Protocol):
    @abstractmethod
    def ouvir(self) -> str | None: ...

    @abstractmethod
    def iniciar(self) -> None: ...

    @abstractmethod
    def parar(self) -> None: ...

    @property
    @abstractmethod
    def is_listening(self) -> bool: ...


@runtime_checkable
class ISessionManager(Protocol):
    @abstractmethod
    def new_session(self) -> str: ...

    @abstractmethod
    def load_session(self, session_id: str) -> bool: ...

    @abstractmethod
    def save_session(self) -> None: ...

    @property
    @abstractmethod
    def current_session_id(self) -> str | None: ...

    @property
    @abstractmethod
    def conversation_history(self) -> list[dict]: ...
