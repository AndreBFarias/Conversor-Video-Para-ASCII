from __future__ import annotations

import queue
import time

import numpy as np

import config
from src.core.logging_config import get_logger
from src.soul.threading_manager import AudioChunk

logger = get_logger(__name__)


class AudioCaptureThread:
    def __init__(self, threading_manager, audio_config, device_index: int, app=None):
        self.manager = threading_manager
        self.audio_config = audio_config
        self.device_index = device_index
        self.app = app

        self.target_sample_rate = 16000
        self.native_sample_rate = None
        self.chunk_size = audio_config.get("CHUNK_SIZE", 1024)
        self.channels = audio_config.get("CHANNELS", 1)
        self._resample_ratio = None

        self.p = None
        self.stream = None
        self._last_log_time = 0
        self._last_viz_time = 0
        self._viz_interval = config.UI_CONFIG.get("VIZ_INTERVAL", 0.1)
        self._chunks_captured = 0
        self._chunks_sent = 0
        self._drops = 0

        logger.info(
            f"[AUDIO_CAPTURE] Configurado: Target SR={self.target_sample_rate}Hz, Chunk={self.chunk_size}, Device={device_index}"
        )

    def initialize_audio(self):
        import pyaudio

        try:
            self.p = pyaudio.PyAudio()

            effective_device = None if self.device_index == 0 else self.device_index

            if effective_device is None:
                default_info = self.p.get_default_input_device_info()
                self.native_sample_rate = int(default_info["defaultSampleRate"])
                logger.info(f"Usando microfone padrao: {default_info['name']} | Rate: {self.native_sample_rate}Hz")
            else:
                try:
                    dev_info = self.p.get_device_info_by_index(self.device_index)
                    self.native_sample_rate = int(dev_info["defaultSampleRate"])
                    logger.info(
                        f"Device Info: {dev_info['name']} | Channels: {dev_info['maxInputChannels']} | Rate: {self.native_sample_rate}Hz"
                    )
                except Exception as dev_err:
                    logger.warning(f"Nao foi possivel obter info do device: {dev_err}")
                    self.native_sample_rate = 48000

            if self.native_sample_rate != self.target_sample_rate:
                self._resample_ratio = self.native_sample_rate / self.target_sample_rate
                logger.info(
                    f"[AUDIO_CAPTURE] Resample ativado: {self.native_sample_rate}Hz -> {self.target_sample_rate}Hz (ratio={self._resample_ratio:.2f})"
                )

            native_chunk = (
                int(self.chunk_size * (self.native_sample_rate / self.target_sample_rate))
                if self._resample_ratio
                else self.chunk_size
            )

            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.native_sample_rate,
                input=True,
                input_device_index=effective_device,
                frames_per_buffer=native_chunk,
                stream_callback=None,
            )

            self._native_chunk_size = native_chunk
            logger.info(f"Stream aberto: {self.native_sample_rate}Hz, chunk={native_chunk}")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar audio: {e}", exc_info=True)
            return False

    def _resample_audio(self, audio_np: np.ndarray) -> np.ndarray:
        if self._resample_ratio is None or self._resample_ratio == 1.0:
            return audio_np
        import scipy.signal

        up = self.target_sample_rate
        down = self.native_sample_rate
        gcd = np.gcd(up, down)
        resampled = scipy.signal.resample_poly(audio_np, up // gcd, down // gcd)
        return np.clip(resampled, -32768, 32767).astype(np.int16)

    def run(self):
        logger.info("[AUDIO_CAPTURE] Aguardando Whisper carregar antes de iniciar captura...")

        start_wait = time.time()
        whisper_ready = self.manager.whisper_ready_event.wait(timeout=120)
        wait_time = time.time() - start_wait

        if not whisper_ready:
            logger.error("[AUDIO_CAPTURE] Timeout aguardando Whisper (120s). Iniciando mesmo assim.")
        else:
            logger.info(f"[AUDIO_CAPTURE] Whisper pronto apos {wait_time:.1f}s. Iniciando captura...")

        if not self.initialize_audio():
            logger.error("[AUDIO_CAPTURE] Falha ao inicializar audio. Thread nao pode continuar.")
            return

        self.manager.audio_ready_event.set()
        logger.info("[AUDIO_CAPTURE] Thread rodando, aguardando listening_event...")

        consecutive_errors = 0
        max_errors = 10
        last_stats_time = time.time()
        warmup_frames = 10
        warmup_done = False

        while not self.manager.shutdown_event.is_set():
            try:
                chunk_to_read = getattr(self, "_native_chunk_size", self.chunk_size)
                raw_data = self.stream.read(chunk_to_read, exception_on_overflow=False)
                self._chunks_captured += 1

                if not warmup_done:
                    if self._chunks_captured >= warmup_frames:
                        warmup_done = True
                        logger.info(f"[AUDIO_CAPTURE] Warmup concluido ({warmup_frames} frames descartados)")
                    continue

                audio_np = np.frombuffer(raw_data, dtype=np.int16).copy()

                if self._resample_ratio and self._resample_ratio != 1.0:
                    audio_np = self._resample_audio(audio_np)

                data = audio_np.tobytes()

                chunk = AudioChunk(data=data, sample_rate=self.target_sample_rate, timestamp=time.time())

                if hasattr(self.manager, "wake_word_queue"):
                    try:
                        self.manager.wake_word_queue.put_nowait(chunk)
                        self._wake_word_sends = getattr(self, "_wake_word_sends", 0) + 1
                    except Exception as e:
                        logger.debug(f"[AUDIO_CAPTURE] Erro ao enviar para wake_word_queue: {e}")

                if time.time() - last_stats_time > 10.0:
                    wake_sends = getattr(self, "_wake_word_sends", 0)
                    wake_queue = (
                        self.manager.wake_word_queue.qsize() if hasattr(self.manager, "wake_word_queue") else -1
                    )
                    listening = self.manager.listening_event.is_set()
                    logger.info(
                        f"[AUDIO_CAPTURE] Stats: captured={self._chunks_captured}, wake_sends={wake_sends}, wake_queue={wake_queue}, listening={listening}"
                    )
                    last_stats_time = time.time()

                try:
                    self.manager.audio_input_queue.put_nowait(chunk)
                    self._chunks_sent += 1
                    consecutive_errors = 0
                except queue.Full:
                    if self._chunks_captured % 100 == 0:
                        logger.warning(f"[AUDIO_CAPTURE] Queue cheia! chunks_captured={self._chunks_captured}")

                if not self.manager.listening_event.is_set():
                    time.sleep(0.01)
                    continue

                current_time = time.time()
                if self.app and (current_time - self._last_viz_time) >= self._viz_interval:
                    self._last_viz_time = current_time
                    try:
                        viz = self.app.query_one("#audio-visualizer")
                        if viz and not viz.has_class("hidden"):
                            audio_copy = audio_np.copy()
                            self.app.call_from_thread(viz.update_audio, audio_copy, self.target_sample_rate)
                    except Exception as e:
                        logger.debug(f"Erro ao atualizar visualizador: {e}")

            except Exception as e:
                consecutive_errors += 1
                logger.warning(f"[AUDIO_CAPTURE] Erro: {e} (consecutivos: {consecutive_errors})")

                if consecutive_errors >= max_errors:
                    logger.error(f"[AUDIO_CAPTURE] Muitos erros ({consecutive_errors}), parando thread")
                    break

                time.sleep(0.1)

        self.cleanup()
        logger.info(f"[AUDIO_CAPTURE] Finalizado. Total: captured={self._chunks_captured}, sent={self._chunks_sent}")

    def cleanup(self):
        logger.info("Limpando recursos de audio...")

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                logger.info("Stream de audio fechado")
            except Exception as e:
                logger.error(f"Erro ao fechar stream: {e}")

        if self.p:
            try:
                self.p.terminate()
                logger.info("PyAudio terminado")
            except Exception as e:
                logger.error(f"Erro ao terminar PyAudio: {e}")
