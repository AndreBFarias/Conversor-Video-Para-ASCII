"""
LunaLiveSession - Integracao Gemini 2.5 Flash Native Audio

Este modulo implementa streaming bidirecional de audio usando a
Multimodal Live API do Gemini 2.5 Flash.

#1 - Streaming de audio do microfone para o Gemini
#2 - Native Audio: TTS gerado pelo proprio modelo
#3 - Barge-in: interrupcao quando usuario comeca a falar
#4 - Integracao com audio_threads.py (AudioCaptureThread)

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/live_session/
"""

from src.soul.live_session import (
    LiveAudioBridge,
    LiveAudioChunk,
    LiveResponse,
    LunaLiveSession,
    NativeAudioPlayer,
    create_live_session,
    get_live_session,
)

__all__ = [
    "LiveAudioChunk",
    "LiveResponse",
    "NativeAudioPlayer",
    "LunaLiveSession",
    "LiveAudioBridge",
    "get_live_session",
    "create_live_session",
]


if __name__ == "__main__":
    import logging
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(level=logging.INFO)

    import config

    if not config.GOOGLE_API_KEY:
        print("GOOGLE_API_KEY nao configurada")
        exit(1)

    def on_text(text: str):
        print(f"[LUNA] {text}")

    def on_audio(audio: bytes):
        print(f"[AUDIO] Recebido {len(audio)} bytes")

    def on_interrupt():
        print("[INTERRUPT] Usuario interrompeu")

    session = create_live_session(
        api_key=config.GOOGLE_API_KEY, on_text_response=on_text, on_audio_response=on_audio, on_interrupt=on_interrupt
    )

    if session.start():
        print("Sessao Live iniciada. Digite mensagens ou Ctrl+C para sair.")

        try:
            while True:
                text = input("> ")
                if text.strip():
                    session.send_text(text)
        except KeyboardInterrupt:
            pass
        finally:
            session.stop()
    else:
        print("Falha ao iniciar sessao Live")
