from __future__ import annotations

import io
import logging
import queue
import threading
import time
import wave

import numpy as np

logger = logging.getLogger(__name__)


class NativeAudioPlayer:
    def __init__(self, sample_rate: int = 24000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._audio_queue: queue.Queue = queue.Queue()
        self._playing = False
        self._stop_event = threading.Event()
        self._player_thread: threading.Thread | None = None
        self._pygame_initialized = False
        self._sounddevice_available = False

        self._init_audio_backend()
        logger.info(f"NativeAudioPlayer inicializado (SR={sample_rate}Hz)")

    def _init_audio_backend(self):
        try:
            import pygame

            pygame.mixer.pre_init(frequency=self.sample_rate, size=-16, channels=self.channels, buffer=1024)
            pygame.mixer.init()
            self._pygame_initialized = True
            logger.info("NativeAudioPlayer usando pygame.mixer")
            return
        except Exception as e:
            logger.debug(f"pygame nao disponivel: {e}")

        try:
            self._sounddevice_available = True
            logger.info("NativeAudioPlayer usando sounddevice")
            return
        except Exception as e:
            logger.debug(f"sounddevice nao disponivel: {e}")

        logger.warning("Nenhum backend de audio disponivel (pygame ou sounddevice)")

    def play(self, audio_data: bytes):
        if not self._pygame_initialized and not self._sounddevice_available:
            logger.warning("Sem backend de audio para reproduzir")
            return

        self._audio_queue.put(audio_data)

        if not self._playing:
            self._start_playback()

    def _start_playback(self):
        if self._player_thread and self._player_thread.is_alive():
            return

        self._playing = True
        self._stop_event.clear()
        self._player_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._player_thread.start()

    def _playback_loop(self):
        while not self._stop_event.is_set():
            try:
                audio_data = self._audio_queue.get(timeout=0.5)

                if self._stop_event.is_set():
                    break

                self._play_chunk(audio_data)

            except queue.Empty:
                if self._audio_queue.empty():
                    break
            except Exception as e:
                logger.error(f"Erro no playback: {e}")

        self._playing = False

    def _play_chunk(self, audio_data: bytes):
        try:
            if self._pygame_initialized:
                self._play_pygame(audio_data)
            elif self._sounddevice_available:
                self._play_sounddevice(audio_data)
        except Exception as e:
            logger.error(f"Erro ao reproduzir chunk: {e}")

    def _play_pygame(self, audio_data: bytes):
        import pygame

        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav:
                wav.setnchannels(self.channels)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                wav.writeframes(audio_data)

            wav_buffer.seek(0)
            sound = pygame.mixer.Sound(wav_buffer)
            channel = sound.play()

            while channel.get_busy() and not self._stop_event.is_set():
                time.sleep(0.01)

        except Exception as e:
            logger.error(f"Erro pygame: {e}")

    def _play_sounddevice(self, audio_data: bytes):
        import sounddevice as sd

        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_np.astype(np.float32) / 32768.0

            sd.play(audio_float, self.sample_rate, blocking=False)

            duration = len(audio_float) / self.sample_rate
            start = time.time()
            while time.time() - start < duration and not self._stop_event.is_set():
                time.sleep(0.01)

        except Exception as e:
            logger.error(f"Erro sounddevice: {e}")

    def stop(self):
        self._stop_event.set()

        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        if self._pygame_initialized:
            try:
                import pygame

                pygame.mixer.stop()
            except Exception as e:
                logger.debug(f"Erro ao parar pygame mixer: {e}")

        if self._sounddevice_available:
            try:
                import sounddevice as sd

                sd.stop()
            except Exception as e:
                logger.debug(f"Erro ao parar sounddevice: {e}")

        logger.debug("Playback interrompido")

    def cleanup(self):
        self.stop()
        if self._pygame_initialized:
            try:
                import pygame

                pygame.mixer.quit()
            except Exception as e:
                logger.debug(f"Erro ao finalizar pygame mixer: {e}")
