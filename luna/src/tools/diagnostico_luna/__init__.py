from .models import TestResult
from .runner import LunaDiagnostico
from .tests import (
    test_animation_frames,
    test_audio_devices,
    test_config,
    test_consciencia,
    test_emotion_mapping,
    test_gemini_connection,
    test_ollama_connection,
    test_profiler,
    test_react_pattern,
    test_threading_manager,
    test_tts_engine,
    test_tts_full,
    test_vad_config,
    test_whisper_load,
)

__all__ = [
    "TestResult",
    "LunaDiagnostico",
    "test_config",
    "test_threading_manager",
    "test_profiler",
    "test_whisper_load",
    "test_audio_devices",
    "test_tts_engine",
    "test_gemini_connection",
    "test_ollama_connection",
    "test_animation_frames",
    "test_react_pattern",
    "test_emotion_mapping",
    "test_consciencia",
    "test_tts_full",
    "test_vad_config",
]


def main():
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    diag = LunaDiagnostico()
    diag.run_all()
