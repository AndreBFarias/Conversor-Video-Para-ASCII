import logging
import time

from .models import TestResult
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
    test_vad_config,
)

logger = logging.getLogger(__name__)


class LunaDiagnostico:
    def __init__(self):
        self.results: list[TestResult] = []
        self.start_time = time.time()

    def run_test(self, name: str, test_func) -> TestResult:
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTANDO: {name}")
        logger.info(f"{'='*60}")

        start = time.time()
        try:
            details = test_func()
            duration = time.time() - start
            result = TestResult(module=name, status="OK", duration=duration, details=details or "Sucesso")
            logger.info(f"[OK] {name} ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start
            result = TestResult(module=name, status="FALHA", duration=duration, error=str(e))
            logger.error(f"[FALHA] {name}: {e}")

        self.results.append(result)
        return result

    def run_all(self):
        logger.info("\n" + "=" * 70)
        logger.info("DIAGNOSTICO COMPLETO LUNA")
        logger.info("=" * 70)

        self.run_test("Config", test_config)
        self.run_test("ThreadingManager", test_threading_manager)
        self.run_test("Profiler", test_profiler)
        self.run_test("ReactPattern", test_react_pattern)
        self.run_test("EmotionMapping", test_emotion_mapping)
        self.run_test("AudioDevices", test_audio_devices)
        self.run_test("VADConfig", test_vad_config)
        self.run_test("AnimationFrames", test_animation_frames)
        self.run_test("TTSEngine", test_tts_engine)
        self.run_test("OllamaConnection", test_ollama_connection)
        self.run_test("GeminiConnection", test_gemini_connection)
        self.run_test("Consciencia", test_consciencia)

        self.print_summary()

    def print_summary(self):
        total_time = time.time() - self.start_time

        logger.info("\n" + "=" * 70)
        logger.info("RESUMO DO DIAGNOSTICO")
        logger.info("=" * 70)

        ok_count = sum(1 for r in self.results if r.status == "OK")
        fail_count = sum(1 for r in self.results if r.status == "FALHA")

        for r in self.results:
            icon = "OK" if r.status == "OK" else "!!"
            logger.info(f"  [{icon}] {r.module:25} | {r.duration:5.2f}s | {r.details or r.error}")

        logger.info("-" * 70)
        logger.info(f"TOTAL: {ok_count} OK | {fail_count} FALHAS | {total_time:.2f}s")

        if fail_count > 0:
            logger.info("\nFALHAS DETECTADAS:")
            for r in self.results:
                if r.status == "FALHA":
                    logger.info(f"  - {r.module}: {r.error}")

        logger.info("=" * 70)
