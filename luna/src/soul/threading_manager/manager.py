from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable

import config

from .models import ThreadState
from .queues import BackpressureQueue, RingBuffer

logger = logging.getLogger(__name__)


class LunaThreadingManager:
    def __init__(self, app=None):
        self.app = app

        queue_cfg = config.QUEUE_CONFIG
        self.audio_input_queue = RingBuffer(maxsize=queue_cfg.get("AUDIO_INPUT", 100), name="audio_input")
        self.transcription_queue = BackpressureQueue(
            maxsize=queue_cfg.get("TRANSCRIPTION", 50), name="transcription", drop_oldest=True
        )
        self.processing_queue = BackpressureQueue(
            maxsize=queue_cfg.get("PROCESSING", 20), name="processing", drop_oldest=True
        )
        self.response_queue = BackpressureQueue(
            maxsize=queue_cfg.get("RESPONSE", 10), name="response", drop_oldest=False
        )
        self.tts_queue = BackpressureQueue(maxsize=queue_cfg.get("TTS", 30), name="tts", drop_oldest=True)
        self.tts_playback_queue = BackpressureQueue(
            maxsize=queue_cfg.get("TTS", 30), name="tts_playback", drop_oldest=True
        )
        self.animation_queue = BackpressureQueue(
            maxsize=queue_cfg.get("ANIMATION", 20), name="animation", drop_oldest=True
        )
        self.vision_queue = BackpressureQueue(maxsize=queue_cfg.get("VISION", 5), name="vision", drop_oldest=True)
        self.wake_word_queue = RingBuffer(maxsize=queue_cfg.get("WAKE_WORD", 50), name="wake_word")

        self.interrupt_event = threading.Event()
        self.shutdown_event = threading.Event()
        self.user_speaking_event = threading.Event()
        self.luna_speaking_event = threading.Event()
        self.listening_event = threading.Event()

        self.whisper_ready_event = threading.Event()
        self.whisper_failed_event = threading.Event()
        self.tts_ready_event = threading.Event()
        self.audio_ready_event = threading.Event()

        self.threads = {}
        self.thread_states = {}
        self.thread_errors = {}
        self._init_times = {}

        self._lock = threading.Lock()

        logger.info("ThreadingManager inicializado (com RingBuffer e eventos de sincronizacao)")

    def register_thread(self, name: str, target: Callable, daemon: bool = True) -> threading.Thread:
        thread = threading.Thread(target=self._thread_wrapper, args=(name, target), daemon=daemon, name=name)
        self.threads[name] = thread
        self.thread_states[name] = ThreadState.STOPPED
        logger.info(f"Thread '{name}' registrada")
        return thread

    def _thread_wrapper(self, name: str, target: Callable):
        try:
            with self._lock:
                self.thread_states[name] = ThreadState.STARTING

            logger.info(f"Thread '{name}' iniciando...")

            with self._lock:
                self.thread_states[name] = ThreadState.RUNNING

            target.run()

            with self._lock:
                self.thread_states[name] = ThreadState.STOPPED

            logger.info(f"Thread '{name}' finalizada normalmente")

        except Exception as e:
            logger.error(f"Thread '{name}' falhou: {e}", exc_info=True)
            with self._lock:
                self.thread_states[name] = ThreadState.ERROR
                self.thread_errors[name] = str(e)

    def start_thread(self, name: str):
        if name not in self.threads:
            logger.error(f"Thread '{name}' nao registrada")
            return False

        thread = self.threads[name]

        if thread.is_alive():
            logger.warning(f"Thread '{name}' ja esta rodando")
            return False

        try:
            thread.start()
            logger.info(f"Thread '{name}' iniciada")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar thread '{name}': {e}")
            return False

    def start_all_threads(self):
        logger.info("Iniciando todas as threads...")
        started = 0

        for name in self.threads:
            if self.start_thread(name):
                started += 1

        logger.info(f"{started}/{len(self.threads)} threads iniciadas")
        return started == len(self.threads)

    def stop_all_threads(self, timeout: float = 5.0, force: bool = False):
        logger.info(f"Parando todas as threads (force={force})...")

        self.shutdown_event.set()

        self._inject_sentinels()

        self._clear_all_queues()

        alive_threads = []
        for name, thread in self.threads.items():
            if thread.is_alive():
                alive_threads.append((name, thread))

        effective_timeout = 1.0 if force else timeout

        for name, thread in alive_threads:
            logger.info(f"Aguardando thread '{name}'...")

            is_daemon = thread.daemon
            wait_time = 0.5 if (force or is_daemon) else effective_timeout

            thread.join(timeout=wait_time)

            if thread.is_alive():
                if force:
                    logger.warning(f"Thread '{name}' ignorada (force shutdown)")
                else:
                    logger.warning(f"Thread '{name}' nao finalizou no timeout de {wait_time}s")
            else:
                logger.info(f"Thread '{name}' finalizada")

        still_alive = sum(1 for _, t in alive_threads if t.is_alive())

        if still_alive > 0 and not force:
            logger.warning(f"{still_alive} threads pendentes. Tentando force shutdown...")
            return self.stop_all_threads(timeout=1.0, force=True)

        logger.info(f"Shutdown {'forcado ' if force else ''}completo. {still_alive} threads serao encerradas pelo OS.")

        return still_alive == 0

    def _inject_sentinels(self):
        sentinel_queues = [
            self.transcription_queue,
            self.processing_queue,
            self.response_queue,
            self.tts_queue,
            self.tts_playback_queue,
            self.animation_queue,
        ]

        for q in sentinel_queues:
            try:
                q.put(None, block=False)
            except Exception as e:
                logger.debug(f"Erro ao injetar sentinel: {e}")

        logger.debug("Sentinelas injetados nas filas")

    def _clear_all_queues(self):
        if hasattr(self.audio_input_queue, "clear"):
            cleared = self.audio_input_queue.clear()
            if cleared > 0:
                logger.debug(f"Limpou {cleared} itens da fila 'audio_input' (RingBuffer)")

        queues = [
            ("transcription", self.transcription_queue),
            ("processing", self.processing_queue),
            ("response", self.response_queue),
            ("tts", self.tts_queue),
            ("tts_playback", self.tts_playback_queue),
            ("animation", self.animation_queue),
            ("vision", self.vision_queue),
        ]

        for name, q in queues:
            if hasattr(q, "clear"):
                cleared = q.clear()
                if cleared > 0:
                    logger.debug(f"Limpou {cleared} itens da fila '{name}' (BackpressureQueue)")
            else:
                cleared = 0
                while True:
                    try:
                        q.get_nowait()
                        cleared += 1
                    except queue.Empty:
                        break
                if cleared > 0:
                    logger.debug(f"Limpou {cleared} itens da fila '{name}'")

    def trigger_interrupt(self):
        logger.warning("INTERRUPCAO ATIVADA")

        self.interrupt_event.set()

        self._clear_all_queues()

        self.luna_speaking_event.clear()

        logger.info("Filas limpas, Luna parada")

    def clear_interrupt(self):
        self.interrupt_event.clear()
        logger.info("Interrupção limpa")

    def get_thread_status(self) -> dict:
        with self._lock:
            status = {}
            for name, thread in self.threads.items():
                status[name] = {
                    "state": self.thread_states.get(name, ThreadState.STOPPED).value,
                    "alive": thread.is_alive(),
                    "error": self.thread_errors.get(name),
                }
            return status

    def get_queue_sizes(self) -> dict:
        return {
            "audio_input": self.audio_input_queue.qsize(),
            "transcription": self.transcription_queue.qsize(),
            "processing": self.processing_queue.qsize(),
            "response": self.response_queue.qsize(),
            "tts": self.tts_queue.qsize(),
            "tts_playback": self.tts_playback_queue.qsize(),
            "animation": self.animation_queue.qsize(),
            "vision": self.vision_queue.qsize(),
        }

    def get_ring_buffer_stats(self) -> dict:
        if hasattr(self.audio_input_queue, "get_stats"):
            return self.audio_input_queue.get_stats()
        return {}

    def record_init_time(self, component: str, duration: float):
        self._init_times[component] = {"duration": duration, "timestamp": time.time()}
        logger.info(f"[INIT] {component} inicializado em {duration:.2f}s")

    def get_init_times(self) -> dict:
        return dict(self._init_times)

    def health_check(self) -> dict:
        status = self.get_thread_status()
        queues = self.get_queue_sizes()

        healthy_threads = sum(1 for s in status.values() if s["state"] == ThreadState.RUNNING.value and s["alive"])
        total_threads = len(status)

        overflowing_queues = [
            name for name, size in queues.items() if size > 0.8 * getattr(self, f"{name}_queue").maxsize
        ]

        health = {
            "healthy": healthy_threads == total_threads and len(overflowing_queues) == 0,
            "threads": status,
            "queues": queues,
            "warnings": overflowing_queues,
            "uptime": time.time(),
        }

        return health
