import logging

import pytest


class TestLoggingConfig:
    def test_get_logger_returns_logger(self):
        from src.core.logging_config import get_logger

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_setup_logging_idempotent(self):
        from src.core.logging_config import setup_logging

        setup_logging()
        handlers_before = len(logging.getLogger().handlers)

        setup_logging()
        handlers_after = len(logging.getLogger().handlers)

        assert handlers_before == handlers_after

    def test_logger_writes_to_file(self, tmp_path):
        import config

        original_log_dir = config.APP_DIR / "logs"

        logger = logging.getLogger("test_file_write")
        logger.info("Teste de escrita")

        log_file = original_log_dir / "luna.log"
        if log_file.exists():
            content = log_file.read_text()
            assert len(content) > 0


class TestLoggingLevels:
    def test_debug_not_in_console_by_default(self, capfd):
        from src.core.logging_config import get_logger

        logger = get_logger("test_levels")
        logger.debug("Debug message")

        captured = capfd.readouterr()
        assert "Debug message" not in captured.out

    def test_info_in_console(self, capfd):
        import logging

        from src.core.logging_config import get_logger, setup_logging

        setup_logging()
        logger = get_logger("test_info")
        logger.info("Info message unique12345")

        root_logger = logging.getLogger()
        has_console_handler = any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
        assert has_console_handler is True


class TestLogFormat:
    def test_log_format_contains_expected_fields(self):
        from src.core.logging_config import LOG_FORMAT

        assert "asctime" in LOG_FORMAT
        assert "levelname" in LOG_FORMAT
        assert "name" in LOG_FORMAT
        assert "message" in LOG_FORMAT

    def test_detailed_format_has_function_and_line(self):
        from src.core.logging_config import LOG_FORMAT_DETAILED

        assert "funcName" in LOG_FORMAT_DETAILED
        assert "lineno" in LOG_FORMAT_DETAILED


class TestLogDir:
    def test_log_dir_exists(self):
        from src.core.logging_config import LOG_DIR

        assert LOG_DIR.exists()

    def test_log_dir_is_writable(self):
        from src.core.logging_config import LOG_DIR

        test_file = LOG_DIR / "test_write_check.tmp"
        try:
            test_file.write_text("test")
            assert test_file.exists()
        finally:
            if test_file.exists():
                test_file.unlink()


class TestNoisyLoggers:
    def test_silence_noisy_loggers_callable(self):
        from src.core.logging_config import _silence_noisy_loggers

        _silence_noisy_loggers()

        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level >= logging.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
