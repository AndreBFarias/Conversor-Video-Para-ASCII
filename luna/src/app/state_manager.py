import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class AppMode(Enum):
    IDLE = auto()
    BUSY = auto()
    RECORDING = auto()
    PROCESSING = auto()


@dataclass
class AppState:
    mode: AppMode = AppMode.IDLE
    em_chamada: bool = False
    is_speaking: bool = False
    is_looping_olhar: bool = False


class StateManager:
    def __init__(self):
        self._state = AppState()
        self._observers: list[Callable[[AppState], Any]] = []

    @property
    def mode(self) -> AppMode:
        return self._state.mode

    @property
    def is_idle(self) -> bool:
        return self._state.mode == AppMode.IDLE

    @property
    def is_busy(self) -> bool:
        return self._state.mode == AppMode.BUSY

    @property
    def em_chamada(self) -> bool:
        return self._state.em_chamada

    @em_chamada.setter
    def em_chamada(self, value: bool) -> None:
        self._state.em_chamada = value
        self._notify_observers()

    @property
    def is_speaking(self) -> bool:
        return self._state.is_speaking

    @is_speaking.setter
    def is_speaking(self, value: bool) -> None:
        self._state.is_speaking = value
        self._notify_observers()

    @property
    def is_looping_olhar(self) -> bool:
        return self._state.is_looping_olhar

    @is_looping_olhar.setter
    def is_looping_olhar(self, value: bool) -> None:
        self._state.is_looping_olhar = value
        self._notify_observers()

    def transition_to(self, mode: AppMode) -> bool:
        valid_transitions = {
            AppMode.IDLE: [AppMode.BUSY, AppMode.RECORDING, AppMode.PROCESSING],
            AppMode.BUSY: [AppMode.IDLE, AppMode.PROCESSING],
            AppMode.RECORDING: [AppMode.IDLE, AppMode.PROCESSING],
            AppMode.PROCESSING: [AppMode.IDLE, AppMode.BUSY],
        }
        if mode in valid_transitions.get(self._state.mode, []) or mode == self._state.mode:
            self._state.mode = mode
            self._notify_observers()
            return True
        return False

    def force_idle(self) -> None:
        self._state.mode = AppMode.IDLE
        self._notify_observers()

    def subscribe(self, callback: Callable[[AppState], Any]) -> None:
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[AppState], Any]) -> None:
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        for cb in self._observers:
            try:
                cb(self._state)
            except Exception as e:
                logger.debug(f"Erro ao notificar observer: {e}")

    def get_state_snapshot(self) -> dict:
        return {
            "mode": self._state.mode.name,
            "em_chamada": self._state.em_chamada,
            "is_speaking": self._state.is_speaking,
            "is_looping_olhar": self._state.is_looping_olhar,
        }
