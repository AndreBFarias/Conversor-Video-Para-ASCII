# -*- coding: utf-8 -*-
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, Callable
from threading import Thread, Event
import time

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import cupy as cp
    GPU_FFT_AVAILABLE = True
except ImportError:
    GPU_FFT_AVAILABLE = False


@dataclass
class AudioConfig:
    enabled: bool = False
    sample_rate: int = 44100
    chunk_size: int = 2048
    smoothing: float = 0.3
    bass_sensitivity: float = 1.0
    mids_sensitivity: float = 1.0
    treble_sensitivity: float = 1.0
    device_index: Optional[int] = None


@dataclass
class AudioBands:
    bass: float = 0.0
    mids: float = 0.0
    treble: float = 0.0
    raw_spectrum: np.ndarray = field(default_factory=lambda: np.zeros(64))


BAND_RANGES = {
    'bass': (20, 250),
    'mids': (250, 4000),
    'treble': (4000, 16000)
}


class AudioAnalyzer:

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.pa = None
        self.stream = None
        self._running = Event()
        self._thread = None
        self._current_bands = AudioBands()
        self._smoothed_bass = 0.0
        self._smoothed_mids = 0.0
        self._smoothed_treble = 0.0
        self._use_gpu = GPU_FFT_AVAILABLE
        self._callbacks = []

    def start(self) -> bool:
        if not PYAUDIO_AVAILABLE:
            print("[AudioAnalyzer] PyAudio nao disponivel")
            return False

        if self._running.is_set():
            return True

        try:
            self.pa = pyaudio.PyAudio()

            device_index = self.config.device_index
            if device_index is None:
                device_index = self._find_loopback_device()

            if device_index is not None:
                device_name = self.pa.get_device_info_by_index(device_index).get('name', 'Unknown')
                print(f"[AudioAnalyzer] Usando dispositivo: [{device_index}] {device_name}")

            self.stream = self.pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback
            )

            self._running.set()
            self.stream.start_stream()
            return True

        except Exception as e:
            print(f"[AudioAnalyzer] Erro ao iniciar: {e}")
            self._cleanup()
            return False

    def stop(self):
        self._running.clear()
        self._cleanup()

    def _cleanup(self):
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass
            self.pa = None

    def _find_loopback_device(self) -> Optional[int]:
        if not self.pa:
            return None

        loopback_keywords = ['loopback', 'monitor', 'stereo mix', 'what u hear']
        fallback_keywords = ['pulse', 'pipewire', 'default']
        fallback_device = None

        for i in range(self.pa.get_device_count()):
            try:
                info = self.pa.get_device_info_by_index(i)
                name = info.get('name', '').lower()
                if info.get('maxInputChannels', 0) > 0:
                    for kw in loopback_keywords:
                        if kw in name:
                            return i
                    for kw in fallback_keywords:
                        if kw in name and fallback_device is None:
                            fallback_device = i
            except Exception:
                continue

        if fallback_device is not None:
            return fallback_device

        try:
            return self.pa.get_default_input_device_info().get('index')
        except Exception:
            return None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        if not self._running.is_set():
            return (None, pyaudio.paComplete)

        try:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            self._process_audio(audio_data)
        except Exception as e:
            print(f"[AudioAnalyzer] Erro no callback: {e}")

        return (None, pyaudio.paContinue)

    def _process_audio(self, audio_data: np.ndarray):
        if self._use_gpu:
            try:
                audio_gpu = cp.asarray(audio_data)
                fft_result = cp.abs(cp.fft.rfft(audio_gpu))
                spectrum = cp.asnumpy(fft_result)
            except Exception:
                self._use_gpu = False
                spectrum = np.abs(np.fft.rfft(audio_data))
        else:
            spectrum = np.abs(np.fft.rfft(audio_data))

        freqs = np.fft.rfftfreq(len(audio_data), 1.0 / self.config.sample_rate)

        bass_mask = (freqs >= BAND_RANGES['bass'][0]) & (freqs < BAND_RANGES['bass'][1])
        mids_mask = (freqs >= BAND_RANGES['mids'][0]) & (freqs < BAND_RANGES['mids'][1])
        treble_mask = (freqs >= BAND_RANGES['treble'][0]) & (freqs < BAND_RANGES['treble'][1])

        bass_energy = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0.0
        mids_energy = np.mean(spectrum[mids_mask]) if np.any(mids_mask) else 0.0
        treble_energy = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0.0

        bass_norm = np.clip(bass_energy * self.config.bass_sensitivity * 0.1, 0, 1)
        mids_norm = np.clip(mids_energy * self.config.mids_sensitivity * 0.15, 0, 1)
        treble_norm = np.clip(treble_energy * self.config.treble_sensitivity * 0.2, 0, 1)

        alpha = self.config.smoothing
        self._smoothed_bass = alpha * self._smoothed_bass + (1 - alpha) * bass_norm
        self._smoothed_mids = alpha * self._smoothed_mids + (1 - alpha) * mids_norm
        self._smoothed_treble = alpha * self._smoothed_treble + (1 - alpha) * treble_norm

        num_bars = 64
        bar_indices = np.linspace(0, len(spectrum) // 4, num_bars + 1, dtype=int)
        raw_spectrum = np.zeros(num_bars)
        for i in range(num_bars):
            start, end = bar_indices[i], bar_indices[i + 1]
            if end > start:
                raw_spectrum[i] = np.mean(spectrum[start:end])

        max_val = np.max(raw_spectrum)
        if max_val > 0:
            raw_spectrum = raw_spectrum / max_val

        self._current_bands = AudioBands(
            bass=self._smoothed_bass,
            mids=self._smoothed_mids,
            treble=self._smoothed_treble,
            raw_spectrum=raw_spectrum
        )

        for callback in self._callbacks:
            try:
                callback(self._current_bands)
            except Exception:
                pass

    def get_bands(self) -> AudioBands:
        return self._current_bands

    def add_callback(self, callback: Callable[[AudioBands], None]):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[AudioBands], None]):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_available_devices(self) -> list:
        devices = []
        if not PYAUDIO_AVAILABLE:
            return devices

        try:
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                try:
                    info = pa.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        devices.append({
                            'index': i,
                            'name': info.get('name', f'Device {i}'),
                            'sample_rate': int(info.get('defaultSampleRate', 44100))
                        })
                except Exception:
                    continue
            pa.terminate()
        except Exception:
            pass

        return devices

    def is_running(self) -> bool:
        return self._running.is_set()


class AudioReactiveModulator:

    def __init__(self, analyzer: AudioAnalyzer):
        self.analyzer = analyzer
        self.bloom_base = 0.3
        self.brightness_base = 1.0

    def get_bloom_intensity(self) -> float:
        bands = self.analyzer.get_bands()
        return np.clip(self.bloom_base + bands.bass * 0.7, 0, 1)

    def get_brightness_multiplier(self) -> float:
        bands = self.analyzer.get_bands()
        return np.clip(self.brightness_base + bands.mids * 0.3, 0.5, 1.5)

    def get_glitch_probability(self) -> float:
        bands = self.analyzer.get_bands()
        return np.clip(bands.treble * 0.5, 0, 0.3)

    def get_color_shift(self) -> Tuple[float, float, float]:
        bands = self.analyzer.get_bands()
        r_shift = bands.bass * 0.2
        g_shift = bands.mids * 0.15
        b_shift = bands.treble * 0.25
        return (r_shift, g_shift, b_shift)

    def get_chromatic_intensity(self) -> float:
        bands = self.analyzer.get_bands()
        return np.clip(1 + bands.bass * 3, 1, 5)


def create_analyzer_from_config(config_parser) -> AudioAnalyzer:
    try:
        audio_config = AudioConfig(
            enabled=config_parser.getboolean('Audio', 'enabled', fallback=False),
            sample_rate=config_parser.getint('Audio', 'sample_rate', fallback=44100),
            chunk_size=config_parser.getint('Audio', 'chunk_size', fallback=2048),
            smoothing=config_parser.getfloat('Audio', 'smoothing', fallback=0.3),
            bass_sensitivity=config_parser.getfloat('Audio', 'bass_sensitivity', fallback=1.0),
            mids_sensitivity=config_parser.getfloat('Audio', 'mids_sensitivity', fallback=1.0),
            treble_sensitivity=config_parser.getfloat('Audio', 'treble_sensitivity', fallback=1.0),
        )
        return AudioAnalyzer(audio_config)
    except Exception:
        return AudioAnalyzer()


# "A musica expressa aquilo que nao pode ser dito e sobre o qual e impossivel ficar em silencio." - Victor Hugo
