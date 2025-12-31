import tempfile
from pathlib import Path

import pytest

from src.data_memory.memory_adapter import SmartMemoryAdapter, get_memory_adapter
from src.data_memory.memory_interface import MemoryCategory, MemoryContext, MemoryInterface
from src.data_memory.smart_memory import SmartMemory


class TestSmartMemoryAdapterDetailed:
    def test_adapter_wraps_smart_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            assert adapter._sm is sm

    def test_remember_with_category(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            mem_id = adapter.remember(
                "Preferencia de usuario",
                importance=0.9,
                category=MemoryCategory.PREFERENCE,
            )

            assert mem_id is not None

    def test_remember_with_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            mem_id = adapter.remember(
                "Informacao com metadata",
                importance=0.5,
                metadata={"source": "test", "custom_field": "value"},
            )

            assert mem_id is not None

    def test_recall_returns_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            ctx = adapter.recall("query qualquer")
            assert isinstance(ctx, MemoryContext)

    def test_category_map_completeness(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            expected_categories = [
                "user_info",
                "preference",
                "fact",
                "event",
                "emotion",
                "context",
                "task",
            ]

            for cat in expected_categories:
                assert cat in adapter._category_map


class TestGetMemoryAdapterFactory:
    def test_factory_returns_adapter(self):
        adapter = get_memory_adapter("luna")
        assert isinstance(adapter, SmartMemoryAdapter)
        assert isinstance(adapter, MemoryInterface)

    def test_factory_creates_new_instances(self):
        adapter1 = get_memory_adapter("luna")
        adapter2 = get_memory_adapter("luna")

        assert adapter1 is not adapter2

    def test_factory_different_entities_return_different_adapters(self):
        luna = get_memory_adapter("luna")
        eris = get_memory_adapter("eris")

        assert luna is not eris
        assert isinstance(luna, MemoryInterface)
        assert isinstance(eris, MemoryInterface)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
