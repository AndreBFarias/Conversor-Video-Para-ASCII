from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.soul.live_session.session import LunaLiveSession

_live_session: "LunaLiveSession | None" = None


def get_live_session() -> "LunaLiveSession | None":
    return _live_session


def create_live_session(
    api_key: str,
    system_instruction: str = None,
    enable_native_playback: bool = True,
    native_audio_sample_rate: int = 24000,
    **kwargs,
) -> "LunaLiveSession":
    global _live_session

    from src.soul.live_session.session import LunaLiveSession

    if _live_session and _live_session.is_running:
        _live_session.stop()

    _live_session = LunaLiveSession(
        api_key=api_key,
        system_instruction=system_instruction,
        enable_native_playback=enable_native_playback,
        native_audio_sample_rate=native_audio_sample_rate,
        **kwargs,
    )

    return _live_session
