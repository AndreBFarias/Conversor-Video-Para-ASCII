from __future__ import annotations

import asyncio
import base64
import logging
import queue
import threading
from collections.abc import Callable

from src.soul.live_session.audio_player import NativeAudioPlayer
from src.soul.live_session.models import LiveAudioChunk, LiveResponse

logger = logging.getLogger(__name__)


class LunaLiveSession:
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
        self.api_key = api_key
        self.model = model
        self.system_instruction = system_instruction or self._default_system_instruction()

        self.on_audio_response = on_audio_response
        self.on_text_response = on_text_response
        self.on_interrupt = on_interrupt

        self._session = None
        self._running = False
        self._is_speaking = False
        self._interrupted = False

        self._send_queue: queue.Queue = queue.Queue()
        self._response_queue: queue.Queue = queue.Queue()

        self._send_thread: threading.Thread | None = None
        self._receive_thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        self._client = None
        self._connected = False

        self._native_player: NativeAudioPlayer | None = None
        if enable_native_playback:
            self._native_player = NativeAudioPlayer(sample_rate=native_audio_sample_rate)
            logger.info("Playback nativo habilitado")

        logger.info(f"LunaLiveSession inicializada (model: {model})")

    def _default_system_instruction(self) -> str:
        return """Voce e Luna, uma assistente gotica e sarcastica.

Regras do modo Live:
- Respostas CURTAS e diretas (maximo 2-3 frases)
- Tom sarcastico e sedutor
- Fale em portugues brasileiro
- Sem emojis, sem girias excessivas
- Mantenha a personalidade mesmo em conversas rapidas"""

    async def _init_client(self):
        try:
            from google import genai
            from google.genai import types

            self._client = genai.Client(api_key=self.api_key)

            config = types.LiveConnectConfig(
                response_modalities=["AUDIO", "TEXT"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede"))
                ),
                system_instruction=types.Content(parts=[types.Part(text=self.system_instruction)]),
            )

            logger.info("Conectando ao Gemini Live API...")
            self._session = self._client.aio.live.connect(model=self.model, config=config)

            self._connected = True
            logger.info("Conectado ao Gemini Live API com sucesso")
            return True

        except ImportError as e:
            logger.error(f"google-genai nao instalado ou versao incompativel: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar ao Gemini Live: {e}")
            return False

    def start(self) -> bool:
        if self._running:
            logger.warning("Sessao ja esta rodando")
            return True

        try:
            self._loop = asyncio.new_event_loop()

            def run_loop():
                asyncio.set_event_loop(self._loop)
                self._loop.run_forever()

            self._send_thread = threading.Thread(target=run_loop, daemon=True)
            self._send_thread.start()

            future = asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)

            if not future.result(timeout=30):
                logger.error("Falha ao inicializar cliente Gemini Live")
                self.stop()
                return False

            asyncio.run_coroutine_threadsafe(self._receive_loop(), self._loop)

            self._running = True
            logger.info("LunaLiveSession iniciada")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar sessao: {e}")
            self.stop()
            return False

    def stop(self):
        self._running = False

        if self._native_player:
            self._native_player.cleanup()
            self._native_player = None

        if self._session:
            try:
                if self._loop and self._loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self._close_session(), self._loop)
                    future.result(timeout=5)
            except Exception as e:
                logger.error(f"Erro ao fechar sessao: {e}")

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        self._connected = False
        self._session = None
        logger.info("LunaLiveSession parada")

    async def _close_session(self):
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Erro ao fechar sessao: {e}")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking
