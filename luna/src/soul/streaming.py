"""
Streaming - Componentes de streaming de audio e texto.

Modulo para processamento de streams LLM e TTS:
- SentenceStreamer: Quebra texto em sentencas para TTS
- TTSStreamProcessor: Processa TTS em paralelo
- StreamingLLMAdapter: Adapter para streaming de LLM
- AudioChunk: Dataclass para chunks de audio

Classes principais:
    SentenceStreamer: Divisor de sentencas
    TTSStreamProcessor: Processador paralelo de TTS
    StreamingLLMAdapter: Adapter de streaming LLM

Dependencias:
    - Nenhuma (modulo independente)
"""

import logging
import queue
import re
import threading
from collections.abc import Callable, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    sentence: str
    audio_data: bytes
    index: int
    is_last: bool


class SentenceStreamer:
    def __init__(self, min_sentence_length: int = 10):
        self.min_sentence_length = min_sentence_length
        self._sentence_pattern = re.compile(r"([^.!?]+[.!?]+)")

    def split_into_sentences(self, text: str) -> list[str]:
        if not text:
            return []

        text = text.strip()

        if len(text) < self.min_sentence_length:
            return [text] if text else []

        sentences = self._sentence_pattern.findall(text)

        if not sentences:
            return [text]

        remaining = text
        for s in sentences:
            remaining = remaining.replace(s, "", 1)
        remaining = remaining.strip()

        if remaining and len(remaining) > 3:
            sentences.append(remaining)

        merged = []
        current = ""

        for s in sentences:
            s = s.strip()
            if not s:
                continue

            if len(current) + len(s) < self.min_sentence_length:
                current += " " + s if current else s
            else:
                if current:
                    merged.append(current)
                current = s

        if current:
            merged.append(current)

        return merged


class TTSStreamProcessor:
    def __init__(
        self, tts_callback: Callable[[str], bytes], playback_callback: Callable[[bytes], None], max_parallel: int = 2
    ):
        self.tts_callback = tts_callback
        self.playback_callback = playback_callback
        self.max_parallel = max_parallel
        self.sentence_streamer = SentenceStreamer()

        self._audio_queue: queue.Queue[AudioChunk] = queue.Queue(maxsize=10)
        self._stop_event = threading.Event()
        self._playback_thread: threading.Thread | None = None
        self._tts_semaphore = threading.Semaphore(max_parallel)

    def process_text(self, text: str) -> None:
        sentences = self.sentence_streamer.split_into_sentences(text)

        if not sentences:
            logger.warning("Nenhuma sentenca para processar")
            return

        self._stop_event.clear()
        self._start_playback_thread()

        threads = []
        for i, sentence in enumerate(sentences):
            is_last = i == len(sentences) - 1
            t = threading.Thread(target=self._process_sentence, args=(sentence, i, is_last), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=30)

        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=10)

    def _process_sentence(self, sentence: str, index: int, is_last: bool) -> None:
        with self._tts_semaphore:
            try:
                audio_data = self.tts_callback(sentence)
                if audio_data:
                    chunk = AudioChunk(sentence=sentence, audio_data=audio_data, index=index, is_last=is_last)
                    self._audio_queue.put(chunk, timeout=30)
                    logger.debug(f"Chunk {index} processado: {sentence[:30]}...")
            except Exception as e:
                logger.error(f"Erro ao processar sentenca {index}: {e}")

    def _start_playback_thread(self) -> None:
        def playback_worker():
            pending = {}
            next_index = 0

            while not self._stop_event.is_set() or not self._audio_queue.empty():
                try:
                    chunk = self._audio_queue.get(timeout=0.5)
                    pending[chunk.index] = chunk

                    while next_index in pending:
                        c = pending.pop(next_index)
                        try:
                            self.playback_callback(c.audio_data)
                        except Exception as e:
                            logger.error(f"Erro no playback chunk {c.index}: {e}")
                        next_index += 1

                        if c.is_last:
                            return

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Erro no playback worker: {e}")
                    break

        self._playback_thread = threading.Thread(target=playback_worker, daemon=True)
        self._playback_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            while not self._audio_queue.empty():
                self._audio_queue.get_nowait()
        except queue.Empty:
            pass


class StreamingLLMAdapter:
    def __init__(self, ollama_client=None, gemini_client=None):
        self.ollama_client = ollama_client
        self.gemini_client = gemini_client

    def stream_ollama(self, prompt: str, model: str, system: str = None) -> Generator[str, None, None]:
        if not self.ollama_client:
            return

        try:
            for chunk in self.ollama_client.generate_stream(prompt=prompt, model=model, system=system):
                if chunk:
                    yield chunk
        except Exception as e:
            logger.error(f"Erro no streaming Ollama: {e}")

    def stream_gemini(self, prompt: str, model: str) -> Generator[str, None, None]:
        if not self.gemini_client:
            return

        try:
            response = self.gemini_client.models.generate_content_stream(model=model, contents=prompt)
            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Erro no streaming Gemini: {e}")
