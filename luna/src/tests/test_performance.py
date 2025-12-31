import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestPerformance:
    def test_entity_load_under_100ms(self):
        from src.core.entity_loader import EntityLoader

        start = time.time()
        loader = EntityLoader("luna")
        _ = loader.get_soul_prompt()
        elapsed = time.time() - start

        assert elapsed < 0.1, f"Entity load took {elapsed:.3f}s (expected < 0.1s)"

    def test_entity_config_load_under_50ms(self):
        from src.core.entity_loader import EntityLoader

        start = time.time()
        loader = EntityLoader("luna")
        _ = loader.get_config()
        elapsed = time.time() - start

        assert elapsed < 0.05, f"Config load took {elapsed:.3f}s (expected < 0.05s)"

    def test_animation_path_resolution_under_10ms(self):
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader("luna")

        start = time.time()
        _ = loader.get_animation_path("observando")
        elapsed = time.time() - start

        assert elapsed < 0.01, f"Animation path resolution took {elapsed:.3f}s"

    def test_multiple_entity_switches_under_500ms(self):
        from src.core.entity_loader import get_active_entity, set_active_entity

        original = get_active_entity()
        entities = ["luna", "eris", "juno"]

        start = time.time()
        for _ in range(10):
            for entity in entities:
                set_active_entity(entity)
        set_active_entity(original)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"30 entity switches took {elapsed:.3f}s"

    def test_file_lock_read_under_20ms(self):
        from src.core.file_lock import read_json_safe

        test_path = Path("/tmp/test_perf_lock.json")
        test_path.write_text('{"test": true}')

        start = time.time()
        for _ in range(10):
            _ = read_json_safe(test_path)
        elapsed = time.time() - start

        test_path.unlink(missing_ok=True)
        assert elapsed < 0.02, f"10 file reads took {elapsed:.3f}s"

    def test_logging_overhead_under_5ms(self):
        from src.core.logging_config import get_logger

        logger = get_logger("test_performance")

        start = time.time()
        for _ in range(100):
            logger.info("Test log message")
        elapsed = time.time() - start

        assert elapsed < 0.005, f"100 log calls took {elapsed:.3f}s"

    def test_response_parser_under_50ms(self):
        from src.soul.response_parser import get_parser

        parser = get_parser()
        test_json = (
            '{"fala_tts": "Teste", "log_terminal": "Teste", "animacao": "Luna_observando", "comando_visao": false}'
        )

        start = time.time()
        for _ in range(10):
            _ = parser.parse(test_json)
        elapsed = time.time() - start

        assert elapsed < 0.05, f"10 parses took {elapsed:.3f}s"

    def test_smart_memory_retrieve_under_5s(self):
        from src.data_memory.smart_memory import get_entity_smart_memory

        memory = get_entity_smart_memory("luna")

        memory.retrieve("warmup query", max_chars=100)

        start = time.time()
        _ = memory.retrieve("test query", max_chars=200)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Memory retrieve took {elapsed:.3f}s (first call includes model loading)"


class TestAnimationPerformance:
    def test_animation_controller_init_under_200ms(self):
        from src.core.animation import AnimationController

        mock_app = MagicMock()
        mock_app.query_one = MagicMock(return_value=MagicMock())

        start = time.time()
        controller = AnimationController(mock_app)
        elapsed = time.time() - start

        assert elapsed < 0.2, f"AnimationController init took {elapsed:.3f}s"

    def test_animation_method_exists(self):
        from src.core.animation import AnimationController

        mock_app = MagicMock()
        mock_app.query_one = MagicMock(return_value=MagicMock())
        controller = AnimationController(mock_app)

        assert hasattr(controller, "run_animation") or hasattr(controller, "set_animation")
        assert hasattr(controller, "reload_for_entity")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
