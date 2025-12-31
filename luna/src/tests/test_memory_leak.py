import gc
import tracemalloc
from pathlib import Path

import pytest


class TestMemoryLeak:
    def test_no_leak_on_entity_switch(self):
        from src.core.entity_loader import EntityLoader

        gc.collect()
        tracemalloc.start()

        for _ in range(100):
            loader = EntityLoader("luna")
            _ = loader.get_soul_prompt()
            del loader

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert current < 50_000_000, f"Memory usage: {current / 1_000_000:.1f}MB (expected < 50MB)"

    def test_no_leak_on_file_operations(self):
        from src.core.file_lock import read_json_safe, write_json_safe

        test_path = Path("/tmp/test_memory_leak.json")

        gc.collect()
        tracemalloc.start()

        for i in range(100):
            write_json_safe(test_path, {"iteration": i, "data": "x" * 1000})
            _ = read_json_safe(test_path)

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        test_path.unlink(missing_ok=True)
        assert current < 10_000_000, f"Memory usage: {current / 1_000_000:.1f}MB (expected < 10MB)"

    def test_no_leak_on_logging(self):
        from src.core.logging_config import get_logger

        logger = get_logger("test_memory_leak")

        gc.collect()
        tracemalloc.start()

        for i in range(1000):
            logger.info(f"Test message {i} with some data: {'x' * 100}")

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert current < 20_000_000, f"Memory usage: {current / 1_000_000:.1f}MB (expected < 20MB)"

    def test_no_leak_on_response_parsing(self):
        from src.soul.response_parser import get_parser

        parser = get_parser()
        test_json = '{"fala_tts": "Teste longo com muito texto" , "log_terminal": "Teste", "animacao": "Luna_observando", "comando_visao": false}'

        gc.collect()
        tracemalloc.start()

        for _ in range(500):
            _ = parser.parse(test_json)

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert current < 30_000_000, f"Memory usage: {current / 1_000_000:.1f}MB (expected < 30MB)"

    def test_no_leak_on_smart_memory_operations(self):
        from src.data_memory.smart_memory import get_entity_smart_memory

        memory = get_entity_smart_memory("luna")

        gc.collect()
        tracemalloc.start()

        for i in range(50):
            memory.add(f"Test memory entry {i}", source="test")
            _ = memory.retrieve("test query", max_chars=100)

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert current < 50_000_000, f"Memory usage: {current / 1_000_000:.1f}MB (expected < 50MB)"

    def test_peak_memory_reasonable(self):
        from src.core.entity_loader import EntityLoader
        from src.soul.response_parser import get_parser

        gc.collect()
        tracemalloc.start()

        for entity in ["luna", "eris", "juno"]:
            loader = EntityLoader(entity)
            _ = loader.get_soul_prompt()
            _ = loader.get_config()

        parser = get_parser()
        for _ in range(100):
            _ = parser.parse(
                '{"fala_tts": "Test", "log_terminal": "Test", "animacao": "Luna_observando", "comando_visao": false}'
            )

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert peak < 100_000_000, f"Peak memory: {peak / 1_000_000:.1f}MB (expected < 100MB)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
