import logging
import os
import sys
import time

import numpy as np
import pyaudio
import webrtcvad

import config

os.environ["CT2_VERBOSE"] = "0"

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = config.AUDIO_CONFIG.get("SAMPLE_RATE", 16000)
FRAME_DURATION_MS = 30
VAD_MODE = config.VAD_CONFIG.get("MODE", 2)
VOICE_AVAILABLE = True
VAD_FRAME_BUFFER_SIZE = config.VAD_CONFIG.get("FRAME_BUFFER_SIZE", 6)


class OuvidoSussurrante:
    def __init__(self):
        logger.info("--- INICIANDO SISTEMA DE AUDICAO (PyAudio) ---")

        self.p = pyaudio.PyAudio()
        self.device_index = None
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.model = None

        target_device_id = config.AUDIO_CONFIG.get("DEVICE_ID", None)

        if target_device_id is not None:
            try:
                info = self.p.get_device_info_by_index(target_device_id)
                if info["maxInputChannels"] > 0:
                    self.device_index = target_device_id
                    self.sample_rate = int(info["defaultSampleRate"])
                    logger.info(
                        f"Dispositivo Configurado Selecionado: [{self.device_index}] {info['name']} (SR: {self.sample_rate}Hz)"
                    )
                else:
                    logger.warning(f"Dispositivo {target_device_id} nao e de entrada. Buscando automatico...")
                    self.device_index = None
            except Exception as e:
                logger.warning(f"Falha ao carregar dispositivo {target_device_id}: {e}. Buscando automatico...")
                self.device_index = None

        if self.device_index is None:
            logger.info("Procurando melhor dispositivo disponivel...")
            best_device = self._find_best_device()
            if best_device:
                self.device_index = best_device["index"]
                self.sample_rate = int(best_device["defaultSampleRate"])
                logger.info(
                    f"Melhor dispositivo encontrado: [{self.device_index}] {best_device['name']} (SR: {self.sample_rate}Hz)"
                )
            else:
                try:
                    default_info = self.p.get_default_input_device_info()
                    self.device_index = default_info["index"]
                    self.sample_rate = int(default_info["defaultSampleRate"])
                    logger.info(
                        f"Usando Dispositivo Padrao do Sistema: [{self.device_index}] {default_info['name']} (SR: {self.sample_rate}Hz)"
                    )
                except Exception as e:
                    logger.critical(f"Nenhum dispositivo de audio encontrado! Erro: {e}")
                    self.device_index = None

        self.vad = webrtcvad.Vad(VAD_MODE)
        self.vad_frame_buffer = []

        logger.info("Sistema de audicao configurado (Whisper sera carregado na TranscriptionThread).")

    def _find_best_device(self):
        best_dev = None
        driver_priority = ["pulse", "pipewire", "default"]

        for i in range(self.p.get_device_count()):
            try:
                info = self.p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    name = info["name"].lower()
                    if "monitor" in name or "hdmi" in name:
                        continue

                    for priority in driver_priority:
                        if priority in name:
                            return info

                    if best_dev is None:
                        best_dev = info
            except Exception:
                continue

        return best_dev

    def _init_whisper(self):
        if self.model is not None:
            return True

        model_size = config.WHISPER_CONFIG["MODEL_SIZE"]
        compute_type = config.WHISPER_CONFIG["COMPUTE_TYPE"]
        use_gpu = config.WHISPER_CONFIG["USE_GPU"]
        device = "cuda" if use_gpu else "cpu"

        download_root = str(config.WHISPER_MODELS_DIR)
        logger.info(f"Carregando Faster-Whisper '{model_size}' em {device.upper()} ({compute_type})...")
        logger.info(f"Download root: {download_root}")
        try:
            from faster_whisper import WhisperModel

            with open(os.devnull, "w") as devnull:
                old_stderr = sys.stderr
                sys.stderr = devnull
                try:
                    self.model = WhisperModel(
                        model_size, device=device, compute_type=compute_type, download_root=download_root
                    )
                finally:
                    sys.stderr = old_stderr
            logger.info("Faster-Whisper Carregado.")
            return True
        except Exception as e:
            logger.critical(f"Erro ao carregar Whisper: {e}")
            return False

    def ouvir_e_transcrever(
        self, should_stop=None, status_callback=None, visualization_callback=None, interruption_callback=None
    ) -> str | None:
        if not self._init_whisper():
            logger.error("Whisper nao disponivel para transcricao.")
            return None

        if self.device_index is None:
            logger.error("Nenhum dispositivo de audio configurado.")
            return None

        supported_rates = [8000, 16000, 32000, 48000]
        capture_rate = self.sample_rate
        vad_rate = capture_rate
        vad_target_rate = config.VAD_CONFIG.get("TARGET_RATE", 16000)

        if capture_rate not in supported_rates:
            vad_rate = vad_target_rate
            logger.info(
                f"Device: {capture_rate}Hz nao suportado pelo VAD. VAD vai usar fallback para {vad_target_rate}Hz."
            )

        chunk_size = int(capture_rate * FRAME_DURATION_MS / 1000)
        logger.info(
            f"Ouvindo... (Device: {self.device_index}, Capture: {capture_rate}Hz, VAD: {vad_rate}Hz, Chunk: {chunk_size})"
        )

        try:
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=capture_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=chunk_size,
            )
        except Exception as e:
            logger.error(f"Erro ao abrir stream PyAudio: {e}")
            return None

        audio_buffer = []
        speech_started = False
        silence_frames = 0

        max_silence_sec = config.VAD_CONFIG["SILENCE_DURATION"]
        silence_frame_limit = int(max_silence_sec * 1000 / FRAME_DURATION_MS)
        max_initial_silence_sec = config.VAD_CONFIG.get("MAX_INITIAL_SILENCE", 4.0)
        start_time = time.time()

        THRESHOLD_RMS = config.VAD_CONFIG["ENERGY_THRESHOLD"]

        try:
            while True:
                if should_stop and should_stop():
                    logger.info("Parada solicitada.")
                    break

                if time.time() - start_time > 30:
                    logger.info("Timeout absoluto (30s).")
                    break

                try:
                    data = stream.read(chunk_size, exception_on_overflow=False)
                except Exception as e:
                    logger.warning(f"Erro leitura stream: {e}")
                    break

                audio_chunk = np.frombuffer(data, dtype=np.int16).copy()

                if visualization_callback:
                    visualization_callback(audio_chunk.copy(), capture_rate)

                rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))

                is_speech = False
                if vad_rate == capture_rate:
                    try:
                        is_speech = self.vad.is_speech(data, capture_rate)
                    except Exception:
                        is_speech = rms > THRESHOLD_RMS
                else:
                    is_speech = rms > THRESHOLD_RMS

                self.vad_frame_buffer.append(is_speech)
                if len(self.vad_frame_buffer) > VAD_FRAME_BUFFER_SIZE:
                    self.vad_frame_buffer.pop(0)

                smoothed_speech = sum(self.vad_frame_buffer) > (len(self.vad_frame_buffer) / 2)

                if smoothed_speech:
                    if not speech_started:
                        logger.debug("Fala detectada!")
                        speech_started = True
                        if interruption_callback:
                            interruption_callback()
                    silence_frames = 0
                    audio_buffer.append(audio_chunk)
                else:
                    if speech_started:
                        silence_frames += 1
                        audio_buffer.append(audio_chunk)
                        if silence_frames > silence_frame_limit:
                            logger.info("Fim de fala detectado (Silencio).")
                            break
                    else:
                        if time.time() - start_time > max_initial_silence_sec:
                            logger.info("Ninguem falou (Timeout Inicial).")
                            break

                        if len(audio_buffer) > (500 / FRAME_DURATION_MS):
                            audio_buffer.pop(0)
                        audio_buffer.append(audio_chunk)

        except Exception as e:
            logger.error(f"Erro no loop de gravacao: {e}", exc_info=True)
        finally:
            stream.stop_stream()
            stream.close()

        if not speech_started or len(audio_buffer) == 0:
            return None

        full_audio_int16 = np.concatenate(audio_buffer)

        final_rms = np.sqrt(np.mean(full_audio_int16.astype(np.float32) ** 2))
        logger.info(f"RMS Final Capturado: {final_rms:.2f}")

        if final_rms < THRESHOLD_RMS:
            msg = f"Audio muito baixo ({final_rms:.0f}). Fale mais alto."
            logger.warning(msg)
            if status_callback:
                status_callback(msg)
            return None

        audio_float32 = full_audio_int16.astype(np.float32) / 32768.0

        if capture_rate != 16000:
            logger.info(f"Resampling {capture_rate}Hz -> 16000Hz...")
            import scipy.signal

            number_of_samples = round(len(audio_float32) * float(16000) / capture_rate)
            audio_float32 = scipy.signal.resample(audio_float32, number_of_samples)

        logger.info("Transcrevendo...")
        try:
            segments, _ = self.model.transcribe(
                audio_float32,
                language="pt",
                beam_size=5,
                initial_prompt="Conversa em Portugues brasileiro. Nomes comuns: Andre, Pedro, Amanda, Luna, Maria, Joao.",
                condition_on_previous_text=False,
                no_speech_threshold=0.4,
                compression_ratio_threshold=2.4,
            )
            texto = " ".join([seg.text for seg in segments]).strip()

            logger.info(f"Transcricao: '{texto}'")

            if len(texto) < 2:
                logger.info("Texto muito curto ignora.")
                return None

            return texto

        except Exception as e:
            logger.error(f"Erro transcricao: {e}")
            return None

    def close(self):
        self.p.terminate()
