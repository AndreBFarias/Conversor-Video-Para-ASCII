from __future__ import annotations

import queue
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.core.profiler import get_pipeline_logger, get_profiler

logger = get_logger(__name__)
profiler = get_profiler()
plog = get_pipeline_logger()


@dataclass
class TTSAudioChunk:
    audio_path: str
    text: str
    duration: float
    metatags: dict | None = None


class TTSThread:
    def __init__(self, threading_manager, boca):
        self.manager = threading_manager
        self.boca = boca
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tts_gen")
        self._pending_generation: Future | None = None

        logger.info("TTSThread configurado (geracao nao-bloqueante)")

    def run(self):
        logger.info("TTS Generator thread rodando...")
        self.manager.tts_ready_event.set()

        while not self.manager.shutdown_event.is_set():
            if self._pending_generation and self._pending_generation.done():
                try:
                    result = self._pending_generation.result()
                    if result:
                        try:
                            self.manager.tts_playback_queue.put_nowait(result)
                            logger.debug(f"[TTS] Audio enfileirado para playback: {result.text[:30]}...")
                        except queue.Full:
                            logger.warning("[TTS] Playback queue cheia!")
                except Exception as e:
                    logger.error(f"[TTS] Erro ao processar resultado: {e}")
                finally:
                    self._pending_generation = None

            try:
                chunk = self.manager.tts_queue.get(timeout=0.1)

                if chunk is None:
                    logger.debug("Sentinel recebido, finalizando TTSThread")
                    break

                if self.manager.interrupt_event.is_set():
                    logger.debug("TTS descartado (interrupcao)")
                    continue

                if self._pending_generation is None or self._pending_generation.done():
                    logger.info(f"[TTS] Gerando audio para: '{chunk.text[:40]}...'")
                    metatags = getattr(chunk, "metatags", None)
                    self._pending_generation = self._executor.submit(self._generate_audio, chunk.text, metatags)
                else:
                    logger.warning("[TTS] Geracao anterior em andamento, enfileirando...")
                    self.manager.tts_queue.put(chunk)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[TTS] Erro no loop: {e}", exc_info=True)

        self._executor.shutdown(wait=False)
        logger.info("TTS Generator thread finalizado")

    @perf_monitor("tts.generate")
    def _generate_audio(self, text: str, metatags: dict = None) -> TTSAudioChunk | None:
        try:
            with profiler.span("tts.generate", {"text_len": len(text)}):
                start_time = time.time()

                audio_path = self.boca.gerar_audio(text, metatags)
                if not audio_path:
                    return None

                duration = time.time() - start_time
                chars_per_sec = len(text) / duration if duration > 0 else 0
                plog.log_stage("tts", "generated", duration_ms=duration * 1000, chars_per_sec=f"{chars_per_sec:.0f}")

                return TTSAudioChunk(audio_path=audio_path, text=text, duration=duration, metatags=metatags)
        except Exception as e:
            logger.error(f"[TTS] Erro na geracao: {e}")
            return None


class TTSPlaybackThread:
    def __init__(self, threading_manager, boca):
        self.manager = threading_manager
        self.boca = boca

        logger.info("TTSPlaybackThread configurado")

    def run(self):
        logger.info("TTS Playback thread rodando...")

        while not self.manager.shutdown_event.is_set():
            try:
                chunk = self.manager.tts_playback_queue.get(timeout=0.2)

                if chunk is None:
                    logger.debug("Sentinel recebido, finalizando TTSPlaybackThread")
                    break

                if self.manager.interrupt_event.is_set():
                    logger.debug("[PLAYBACK] Audio descartado (interrupcao)")
                    self._cleanup_audio(chunk.audio_path)
                    continue

                logger.info(f"[PLAYBACK] Tocando: '{chunk.text[:40]}...'")
                self.manager.luna_speaking_event.set()

                try:
                    start_play = time.time()
                    success = self.boca._play_audio_file(chunk.audio_path)
                    play_time = time.time() - start_play

                    if success:
                        logger.info(f"[PLAYBACK] Concluido em {play_time:.2f}s")
                    else:
                        logger.warning("[PLAYBACK] Falha ao tocar audio")

                except Exception as e:
                    logger.error(f"[PLAYBACK] Erro: {e}")
                finally:
                    self.manager.luna_speaking_event.clear()
                    self._cleanup_audio(chunk.audio_path)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[PLAYBACK] Erro no loop: {e}", exc_info=True)

        logger.info("TTS Playback thread finalizado")

    def _cleanup_audio(self, audio_path: str):
        import os

        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            logger.debug(f"Erro ao limpar audio {audio_path}: {e}")
