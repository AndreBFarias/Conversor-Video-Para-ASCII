import pytest
import os
import tempfile
import logging
from src.utils.logger import setup_logger


class TestSetupLogger:

    def test_returns_logger_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("test_logger", log_file)
            assert isinstance(logger, logging.Logger)

    def test_logger_has_correct_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("custom_name", log_file)
            assert logger.name == "custom_name"

    def test_logger_level_is_debug(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("debug_test", log_file)
            assert logger.level == logging.DEBUG

    def test_creates_log_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "subdir", "logs")
            log_file = os.path.join(log_dir, "test.log")
            setup_logger("dir_test", log_file)
            assert os.path.exists(log_dir)

    def test_writes_to_log_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("write_test", log_file)
            logger.info("Test message")
            for handler in logger.handlers:
                handler.flush()
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content

    def test_avoids_duplicate_handlers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger1 = setup_logger("dup_test", log_file)
            handler_count_1 = len(logger1.handlers)
            logger2 = setup_logger("dup_test", log_file)
            handler_count_2 = len(logger2.handlers)
            assert handler_count_1 == handler_count_2

    def test_different_log_levels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("level_test", log_file)
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            for handler in logger.handlers:
                handler.flush()
            with open(log_file, 'r') as f:
                content = f.read()
                assert "DEBUG" in content
                assert "INFO" in content
                assert "WARNING" in content
                assert "ERROR" in content
