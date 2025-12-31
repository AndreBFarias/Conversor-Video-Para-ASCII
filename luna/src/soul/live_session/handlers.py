from __future__ import annotations

import asyncio
import base64
import logging
import queue
from typing import TYPE_CHECKING

from src.soul.live_session.models import LiveAudioChunk, LiveResponse

if TYPE_CHECKING:
    from src.soul.live_session.client import LunaLiveSession

logger = logging.getLogger(__name__)


def send_audio(session: "LunaLiveSession", audio_data: bytes, sample_rate: int = 16000):
    if not session._running or not session._connected:
        return

    chunk = LiveAudioChunk(data=audio_data, sample_rate=sample_rate)
    session._send_queue.put(chunk)

    if session._loop and session._connected:
        asyncio.run_coroutine_threadsafe(_send_audio_chunk(session, chunk), session._loop)


async def _send_audio_chunk(session: "LunaLiveSession", chunk: LiveAudioChunk):
    if not session._session or not session._connected:
        return

    try:
        from google.genai import types

        audio_b64 = base64.b64encode(chunk.data).decode("utf-8")

        async with session._session as s:
            await s.send(
                input=types.LiveClientRealtimeInput(media_chunks=[types.Blob(mime_type="audio/pcm", data=audio_b64)]),
                end_of_turn=chunk.is_final,
            )

    except Exception as e:
        logger.error(f"Erro ao enviar audio: {e}")


def send_text(session: "LunaLiveSession", text: str):
    if not session._running or not session._connected:
        return

    if session._loop:
        asyncio.run_coroutine_threadsafe(_send_text(session, text), session._loop)


async def _send_text(session: "LunaLiveSession", text: str):
    if not session._session:
        return

    try:
        async with session._session as s:
            await s.send(input=text, end_of_turn=True)
    except Exception as e:
        logger.error(f"Erro ao enviar texto: {e}")


def interrupt(session: "LunaLiveSession"):
    if not session._is_speaking:
        return

    session._interrupted = True
    session._is_speaking = False

    if session._native_player:
        session._native_player.stop()

    if session.on_interrupt:
        session.on_interrupt()

    logger.info("Barge-in: Resposta interrompida")


async def receive_loop(session: "LunaLiveSession"):
    if not session._session:
        return

    try:
        async with session._session as s:
            while session._running:
                try:
                    async for response in s.receive():
                        if not session._running:
                            break

                        if session._interrupted:
                            session._interrupted = False
                            continue

                        await _process_response(session, response)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if session._running:
                        logger.error(f"Erro no receive loop: {e}")
                    await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Erro fatal no receive loop: {e}")


async def _process_response(session: "LunaLiveSession", response):
    try:
        if hasattr(response, "server_content"):
            content = response.server_content

            if hasattr(content, "model_turn") and content.model_turn:
                for part in content.model_turn.parts:
                    if hasattr(part, "text") and part.text:
                        session._is_speaking = True
                        if session.on_text_response:
                            session.on_text_response(part.text)

                    if hasattr(part, "inline_data") and part.inline_data:
                        if "audio" in part.inline_data.mime_type:
                            session._is_speaking = True
                            audio_bytes = base64.b64decode(part.inline_data.data)

                            if session._native_player:
                                session._native_player.play(audio_bytes)

                            if session.on_audio_response:
                                session.on_audio_response(audio_bytes)

            if hasattr(content, "turn_complete") and content.turn_complete:
                session._is_speaking = False
                logger.debug("Turn completo")

    except Exception as e:
        logger.error(f"Erro ao processar resposta: {e}")


def get_response(session: "LunaLiveSession", timeout: float = 0.1) -> LiveResponse | None:
    try:
        return session._response_queue.get(timeout=timeout)
    except queue.Empty:
        return None
