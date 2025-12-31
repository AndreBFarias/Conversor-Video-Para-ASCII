from __future__ import annotations

import asyncio
from collections.abc import Callable

from src.soul.live_session.client import LunaLiveSession as _LunaLiveSessionBase
from src.soul.live_session.handlers import (
    get_response,
    interrupt,
    receive_loop,
    send_audio,
    send_text,
)
from src.soul.live_session.models import LiveResponse


class LunaLiveSession(_LunaLiveSessionBase):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        system_instruction: str = None,
        on_audio_response: Callable[[bytes], None] = None,
        on_text_response: Callable[[str], None] = None,
        on_interrupt: Callable[[], None] = None,
        enable_native_playback: bool = True,
        native_audio_sample_rate: int = 24000,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            system_instruction=system_instruction,
            on_audio_response=on_audio_response,
            on_text_response=on_text_response,
            on_interrupt=on_interrupt,
            enable_native_playback=enable_native_playback,
            native_audio_sample_rate=native_audio_sample_rate,
        )

    def start(self) -> bool:
        result = super().start()
        if result and self._loop:
            asyncio.run_coroutine_threadsafe(self._receive_loop(), self._loop)
        return result

    async def _receive_loop(self):
        await receive_loop(self)

    def send_audio(self, audio_data: bytes, sample_rate: int = 16000):
        send_audio(self, audio_data, sample_rate)

    def send_text(self, text: str):
        send_text(self, text)

    def interrupt(self):
        interrupt(self)

    def get_response(self, timeout: float = 0.1) -> LiveResponse | None:
        return get_response(self, timeout)
