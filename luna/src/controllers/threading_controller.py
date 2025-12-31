import logging
import threading
from queue import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import TemploDaAlma

logger = logging.getLogger(__name__)


class ThreadingController:
    def __init__(self, app: "TemploDaAlma"):
        self.app = app
        self.audio_input_queue: Queue = Queue(maxsize=100)
        self.transcription_queue: Queue = Queue()
        self.processing_queue: Queue = Queue()
        self.tts_queue: Queue = Queue()

        self._threads: dict = {}
        self._shutdown_event = threading.Event()

    def setup_threads(self):
        from src.luna.audio_threads import AudioCaptureThread, TranscriptionThread
        from src.luna.processing_threads import ProcessingThread, TTSThread

        self._threads["audio_capture"] = AudioCaptureThread(
            audio_queue=self.audio_input_queue, shutdown_event=self._shutdown_event
        )

        self._threads["transcription"] = TranscriptionThread(
            audio_queue=self.audio_input_queue,
            output_queue=self.transcription_queue,
            shutdown_event=self._shutdown_event,
        )

        self._threads["processing"] = ProcessingThread(
            input_queue=self.transcription_queue,
            output_queue=self.processing_queue,
            tts_queue=self.tts_queue,
            app=self.app,
            shutdown_event=self._shutdown_event,
        )

        self._threads["tts"] = TTSThread(tts_queue=self.tts_queue, shutdown_event=self._shutdown_event)

        logger.info("Threads configuradas")

    def start_all(self):
        for name, thread in self._threads.items():
            if not thread.is_alive():
                thread.start()
                logger.info(f"Thread {name} iniciada")

    def stop_all(self, timeout: float = 5.0):
        logger.info("Iniciando shutdown de threads...")
        self._shutdown_event.set()

        for name, thread in self._threads.items():
            if thread.is_alive():
                thread.join(timeout=timeout)
                if thread.is_alive():
                    logger.warning(f"Thread {name} nao finalizou no timeout")
                else:
                    logger.info(f"Thread {name} finalizada")

    def is_running(self, thread_name: str) -> bool:
        thread = self._threads.get(thread_name)
        return thread and thread.is_alive()

    def get_queue_sizes(self) -> dict:
        return {
            "audio_input": self.audio_input_queue.qsize(),
            "transcription": self.transcription_queue.qsize(),
            "processing": self.processing_queue.qsize(),
            "tts": self.tts_queue.qsize(),
        }

    def clear_queues(self):
        for q in [self.audio_input_queue, self.transcription_queue, self.processing_queue, self.tts_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                except Exception:
                    break
