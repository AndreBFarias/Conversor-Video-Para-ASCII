from __future__ import annotations

import queue
import time
from concurrent.futures import Future, ThreadPoolExecutor

import numpy as np

import config
from src.core.event_logger import get_event_logger
from src.core.logging_config import get_logger
from src.core.metricas import perf_monitor
from src.core.profiler import get_pipeline_logger, get_profiler
from src.soul.audio_threads.adaptive_vad import AdaptiveVAD
from src.soul.audio_threads.hallucination_filter import is_hallucination
from src.soul.audio_threads.whisper_init import WhisperModelManager

logger = get_logger(__name__)
profiler = get_profiler()
plog = get_pipeline_logger()


class TranscriptionThread:
    def __init__(self, threading_manager, whisper_config, vad_config: dict = None):
        self.manager = threading_manager
        self.whisper_config = whisper_config
        self.vad_config = vad_config or {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="whisper")
        self._pending_transcription: Future | None = None
        self._chunks_processed = 0
        self._speech_detections = 0
        self._transcriptions_sent = 0

        self.whisper_manager = WhisperModelManager(whisper_config)
        self.adaptive_vad = AdaptiveVAD(self.vad_config)

        logger.info(
            f"[TRANSCRIPTION] Configurado: whisper={whisper_config.get('MODEL_SIZE')}, auto_adjust={self.adaptive_vad.enabled}"
        )

    @property
    def model(self):
        return self.whisper_manager.model

    @property
    def model_loaded(self):
        return self.whisper_manager.model_loaded

    @property
    def load_error(self):
        return self.whisper_manager.load_error

    def initialize_whisper(self):
        return self.whisper_manager.initialize()

    def warmup_model(self):
        self.whisper_manager.warmup()

    def health_check(self) -> bool:
        return self.whisper_manager.health_check()

    def _resample_for_vad(self, audio_np: np.ndarray, source_rate: int, target_rate: int = 16000) -> bytes:
        import scipy.signal

        if source_rate == target_rate:
            return audio_np.tobytes()

        gcd = np.gcd(source_rate, target_rate)
        up = target_rate // gcd
        down = source_rate // gcd

        resampled = scipy.signal.resample_poly(audio_np.astype(np.float64), up, down)
        resampled = np.clip(resampled, -32768, 32767).astype(np.int16)

        frame_samples = int(target_rate * 0.02)
        if len(resampled) >= frame_samples:
            resampled = resampled[:frame_samples]
        else:
            resampled = np.pad(resampled, (0, frame_samples - len(resampled)))

        return resampled.tobytes()

    def run(self):
        init_start = time.time()
        if not self.initialize_whisper():
            logger.error("[TRANSCRIPTION] Falha ao inicializar Whisper.")
            if hasattr(self.manager, "whisper_failed_event"):
                self.manager.whisper_failed_event.set()
            return

        self.warmup_model()

        if not self.health_check():
            logger.error("[TRANSCRIPTION] Health check falhou.")
            if hasattr(self.manager, "whisper_failed_event"):
                self.manager.whisper_failed_event.set()
            return

        init_time = time.time() - init_start
        self.manager.record_init_time("whisper", init_time)
        self.manager.whisper_ready_event.set()
        logger.info("[TRANSCRIPTION] Whisper pronto!")

        self._run_vad_loop()

    def _run_vad_loop(self):
        import webrtcvad

        audio_buffer = []
        vad_buffer = []
        speech_started = False
        silence_frames = 0
        silence_frame_limit = self.vad_config.get(
            "SILENCE_FRAME_LIMIT", config.VAD_CONFIG.get("SILENCE_FRAME_LIMIT", 12)
        )

        vad_mode = self.vad_config.get("MODE", config.VAD_CONFIG.get("MODE", 2))
        vad = webrtcvad.Vad(vad_mode)

        vad_target_rate = self.vad_config.get("TARGET_RATE", config.VAD_CONFIG.get("TARGET_RATE", 16000))
        min_speech_chunks = self.vad_config.get("MIN_SPEECH_CHUNKS", config.VAD_CONFIG.get("MIN_SPEECH_CHUNKS", 3))
        vad_buffer_size = self.vad_config.get("FRAME_BUFFER_SIZE", config.VAD_CONFIG.get("FRAME_BUFFER_SIZE", 6))

        self._calibrate_vad()

        last_stats_time = time.time()
        luna_was_speaking = False
        post_speech_cooldown = 0
        cooldown_frames = self.vad_config.get("POST_SPEECH_COOLDOWN_FRAMES", 15)

        while not self.manager.shutdown_event.is_set():
            self._process_pending_transcription()

            try:
                chunk = self.manager.audio_input_queue.get(timeout=0.05)
                self._chunks_processed += 1

                luna_speaking_now = self.manager.luna_speaking_event.is_set()

                if luna_speaking_now:
                    audio_buffer, vad_buffer = [], []
                    speech_started, silence_frames = False, 0
                    luna_was_speaking, post_speech_cooldown = True, 0
                    continue

                if luna_was_speaking and not luna_speaking_now:
                    luna_was_speaking = False
                    post_speech_cooldown = cooldown_frames
                    audio_buffer, vad_buffer = [], []
                    speech_started, silence_frames = False, 0

                if post_speech_cooldown > 0:
                    post_speech_cooldown -= 1
                    continue

                audio_np = np.frombuffer(chunk.data, dtype=np.int16).copy()
                rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))

                current_threshold = self.adaptive_vad.process_chunk(rms)

                if not self.manager.listening_event.is_set():
                    continue

                is_speech = self._detect_speech(chunk, audio_np, rms, current_threshold, vad, vad_target_rate)

                vad_buffer.append(is_speech)
                if len(vad_buffer) > vad_buffer_size:
                    vad_buffer.pop(0)

                smoothed_speech = sum(vad_buffer) > len(vad_buffer) * 0.5

                if time.time() - last_stats_time > 5.0:
                    logger.info(
                        f"[VAD] Stats: processed={self._chunks_processed}, detections={self._speech_detections}, transcribed={self._transcriptions_sent}"
                    )
                    last_stats_time = time.time()

                speech_started, silence_frames, audio_buffer, vad_buffer = self._handle_speech_detection(
                    smoothed_speech,
                    speech_started,
                    silence_frames,
                    audio_buffer,
                    vad_buffer,
                    audio_np,
                    chunk,
                    rms,
                    min_speech_chunks,
                    silence_frame_limit,
                )

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[TRANSCRIPTION] Erro no loop: {e}", exc_info=True)

        self._executor.shutdown(wait=False)
        logger.info("Transcription thread finalizado")

    def _calibrate_vad(self):
        if not self.adaptive_vad.enabled:
            return

        logger.info(f"[ADAPTIVE_VAD] Calibrando {self.adaptive_vad.calibration_seconds}s...")
        calibration_start = time.time()
        calibration_samples = 0

        while not self.manager.shutdown_event.is_set():
            elapsed = time.time() - calibration_start
            if elapsed >= self.adaptive_vad.calibration_seconds:
                break

            try:
                chunk = self.manager.audio_input_queue.get(timeout=0.1)
                audio_np = np.frombuffer(chunk.data, dtype=np.int16).copy()
                rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
                self.adaptive_vad._rms_samples.append(rms)
                calibration_samples += 1
            except Exception:
                continue

        self.adaptive_vad._calibration_start = calibration_start
        self.adaptive_vad._calibrate()
        logger.info(
            f"[ADAPTIVE_VAD] Calibrado: {calibration_samples} amostras, threshold={self.adaptive_vad.current_threshold}"
        )

    def _detect_speech(self, chunk, audio_np, rms, current_threshold, vad, vad_target_rate) -> bool:
        energy_speech = rms > current_threshold
        webrtc_speech = False

        if chunk.sample_rate in [8000, 16000, 32000, 48000]:
            try:
                webrtc_speech = vad.is_speech(chunk.data, chunk.sample_rate)
            except Exception:
                pass
        else:
            try:
                resampled_data = self._resample_for_vad(audio_np, chunk.sample_rate, vad_target_rate)
                frame_duration_ms = int(len(resampled_data) / 2 * 1000 / vad_target_rate)
                if frame_duration_ms in [10, 20, 30]:
                    webrtc_speech = vad.is_speech(resampled_data, vad_target_rate)
            except Exception:
                pass

        return energy_speech or webrtc_speech

    def _handle_speech_detection(
        self,
        smoothed_speech,
        speech_started,
        silence_frames,
        audio_buffer,
        vad_buffer,
        audio_np,
        chunk,
        rms,
        min_speech_chunks,
        silence_frame_limit,
    ):
        if smoothed_speech:
            audio_buffer.append(audio_np)
            silence_frames = 0

            if not speech_started and len(audio_buffer) >= min_speech_chunks:
                self._speech_detections += 1
                profiler.mark("vad", "SPEECH_START", {"rms": rms, "chunks": len(audio_buffer)})
                logger.info(f"[VAD] FALA DETECTADA #{self._speech_detections}")
                speech_started = True
                self.manager.user_speaking_event.set()

                if self.manager.luna_speaking_event.is_set():
                    logger.info("[VAD] Usuario interrompeu Luna")
                    self.manager.trigger_interrupt()
        else:
            if speech_started:
                silence_frames += 1
                audio_buffer.append(audio_np)

                if silence_frames > silence_frame_limit:
                    self._process_speech_end(audio_buffer, chunk, min_speech_chunks)
                    audio_buffer, vad_buffer = [], []
                    speech_started, silence_frames = False, 0
                    self.manager.user_speaking_event.clear()
            else:
                if len(audio_buffer) > 50:
                    audio_buffer = audio_buffer[-50:]

        return speech_started, silence_frames, audio_buffer, vad_buffer

    def _process_speech_end(self, audio_buffer, chunk, min_speech_chunks):
        if len(audio_buffer) < min_speech_chunks * 2:
            return

        full_audio = np.concatenate(audio_buffer)
        full_rms = np.sqrt(np.mean(full_audio.astype(np.float32) ** 2))
        duration_sec = len(full_audio) / chunk.sample_rate

        min_rms = self.adaptive_vad.current_threshold * 0.3

        if full_rms < min_rms:
            profiler.mark("vad", "DISCARDED_NOISE", {"rms": full_rms})
            logger.info(f"[VAD] Audio descartado: RMS={full_rms:.0f} < {min_rms:.0f}")
        elif self._pending_transcription is None or self._pending_transcription.done():
            profiler.mark("vad", "SPEECH_END", {"chunks": len(audio_buffer), "duration": duration_sec})
            logger.info(f"[VAD] FIM DE FALA ({len(audio_buffer)} chunks, ~{duration_sec:.1f}s)")
            self._pending_transcription = self._executor.submit(self._transcribe, full_audio, chunk.sample_rate)
        else:
            profiler.mark("vad", "DISCARDED_BUSY")
            logger.warning("[WHISPER] Transcricao anterior em andamento")

    def _process_pending_transcription(self):
        if not self._pending_transcription or not self._pending_transcription.done():
            return

        try:
            text = self._pending_transcription.result()
            if text:
                from src.soul.threading_manager import TranscriptionResult

                result = TranscriptionResult(text=text, confidence=0.9, timestamp=time.time())
                try:
                    self.manager.transcription_queue.put_nowait(result)
                    self._transcriptions_sent += 1
                    evt_logger = get_event_logger()
                    evt_logger.transcription(text, success=True, details={"count": self._transcriptions_sent})
                    logger.info(f"[TRANSCRIPTION] #{self._transcriptions_sent}: '{text[:60]}...'")
                except queue.Full:
                    evt_logger = get_event_logger()
                    evt_logger.transcription(text, success=False, details={"error": "queue_full"})
        except Exception as e:
            logger.error(f"[TRANSCRIPTION] Erro: {e}")
        finally:
            self._pending_transcription = None

    @perf_monitor("whisper.transcribe")
    def _transcribe(self, audio_int16: np.ndarray, sample_rate: int) -> str | None:
        try:
            with profiler.span("stt.whisper"):
                start_time = time.time()
                audio_duration = len(audio_int16) / sample_rate

                with profiler.span("stt.preprocess"):
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0
                    if sample_rate != 16000:
                        import scipy.signal

                        number_of_samples = round(len(audio_float32) * float(16000) / sample_rate)
                        audio_float32 = scipy.signal.resample(audio_float32, number_of_samples)

                with profiler.span("stt.inference"):
                    texto = self.whisper_manager.transcribe(audio_float32, config.WHISPER_TRANSCRIPTION)

                elapsed = time.time() - start_time
                rtf = elapsed / audio_duration if audio_duration > 0 else 0
                plog.log_stage("stt", f"'{texto[:40]}...'", duration_ms=elapsed * 1000, rtf=f"{rtf:.2f}x")

                if len(texto) < 2:
                    return None

                is_hal, reason = is_hallucination(texto)
                if is_hal:
                    plog.log_stage("stt", f"HALLUCINATION ({reason})")
                    return None

                return texto

        except Exception as e:
            logger.error(f"Erro na transcricao: {e}")
            return None
