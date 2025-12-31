"""Testes para MemoryCron."""

import pytest


class TestMemoryCron:
    def test_import(self):
        from src.data_memory.memory_cron import MemoryCron

        assert MemoryCron is not None

    def test_create_cron(self):
        from src.data_memory.memory_cron import MemoryCron

        cron = MemoryCron(interval_minutes=30)
        assert cron is not None
        assert cron.interval == 30 * 60

    def test_initial_state(self):
        from src.data_memory.memory_cron import MemoryCron

        cron = MemoryCron()
        assert cron.running is False
        assert cron.run_count == 0
