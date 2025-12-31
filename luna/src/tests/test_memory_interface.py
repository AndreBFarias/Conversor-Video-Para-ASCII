import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.data_memory.memory_adapter import SmartMemoryAdapter, get_memory_adapter
from src.data_memory.memory_interface import (
    MemoryCategory,
    MemoryContext,
    MemoryEntry,
    MemoryHorizon,
    MemoryInterface,
)
from src.data_memory.smart_memory import SmartMemory


class TestMemoryEntry:
    def test_to_compact_normal(self):
        entry = MemoryEntry(
            id="test1",
            content="Usuario gosta de cafe",
            category=MemoryCategory.PREFERENCE,
            horizon=MemoryHorizon.LONG,
            importance=0.5,
            timestamp=datetime.now(),
        )

        compact = entry.to_compact()
        assert "cafe" in compact
        assert "[PREFERENCE]" not in compact

    def test_to_compact_important(self):
        entry = MemoryEntry(
            id="test2",
            content="Usuario e programador Python",
            category=MemoryCategory.USER_INFO,
            horizon=MemoryHorizon.LONG,
            importance=0.9,
            timestamp=datetime.now(),
        )

        compact = entry.to_compact()
        assert "[USER_INFO]" in compact

    def test_to_dict(self):
        entry = MemoryEntry(
            id="test3",
            content="Teste",
            category=MemoryCategory.FACT,
            horizon=MemoryHorizon.SHORT,
            importance=0.3,
            timestamp=datetime.now(),
        )

        d = entry.to_dict()
        assert d["id"] == "test3"
        assert d["category"] == "fact"
        assert d["horizon"] == "short"


class TestMemoryContext:
    def test_add_within_budget(self):
        ctx = MemoryContext(max_tokens=100)
        entry = MemoryEntry(
            id="1",
            content="Curto",
            category=MemoryCategory.CONTEXT,
            horizon=MemoryHorizon.SHORT,
            importance=0.5,
            timestamp=datetime.now(),
        )

        assert ctx.add(entry) is True
        assert len(ctx) == 1

    def test_add_exceeds_budget(self):
        ctx = MemoryContext(max_tokens=10)
        entry = MemoryEntry(
            id="1",
            content="Texto muito longo que excede o budget de tokens",
            category=MemoryCategory.CONTEXT,
            horizon=MemoryHorizon.SHORT,
            importance=0.5,
            timestamp=datetime.now(),
        )

        assert ctx.add(entry) is False
        assert len(ctx) == 0

    def test_render_empty(self):
        ctx = MemoryContext()
        assert ctx.render() == ""

    def test_render_with_entries(self):
        ctx = MemoryContext()
        ctx.entries = [
            MemoryEntry(
                id="1",
                content="Mem 1",
                category=MemoryCategory.FACT,
                horizon=MemoryHorizon.LONG,
                importance=0.8,
                timestamp=datetime.now(),
            ),
            MemoryEntry(
                id="2",
                content="Mem 2",
                category=MemoryCategory.CONTEXT,
                horizon=MemoryHorizon.SHORT,
                importance=0.3,
                timestamp=datetime.now(),
            ),
        ]

        rendered = ctx.render()
        assert "[MEMORIA]" in rendered
        assert "Mem 1" in rendered
        assert "Mem 2" in rendered


class TestSmartMemoryAdapter:
    def test_implements_interface(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            assert isinstance(adapter, MemoryInterface)

    def test_remember_and_recall(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            mem_id = adapter.remember("Usuario mora em cidade grande e trabalha com dados", importance=0.8)

            assert mem_id is not None

            ctx = adapter.recall("onde o usuario mora?")
            assert isinstance(ctx, MemoryContext)

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            stats = adapter.get_stats()
            assert "total_memories" in stats

    def test_forget_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            result = adapter.forget("nonexistent_id")
            assert result is False

    def test_flush_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            result = adapter.flush()
            assert result is None

    def test_consolidate_returns_int(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SmartMemory(storage_path=str(Path(tmpdir) / "mem.json"), lazy_load=False)
            adapter = SmartMemoryAdapter(sm)

            result = adapter.consolidate()
            assert isinstance(result, int)


class TestGetMemoryAdapter:
    def test_returns_interface(self):
        adapter = get_memory_adapter("luna")
        assert isinstance(adapter, MemoryInterface)

    def test_different_entities(self):
        luna_adapter = get_memory_adapter("luna")
        eris_adapter = get_memory_adapter("eris")

        assert luna_adapter is not eris_adapter


class TestMemoryHorizon:
    def test_horizon_values(self):
        assert MemoryHorizon.SHORT.value == "short"
        assert MemoryHorizon.MEDIUM.value == "medium"
        assert MemoryHorizon.LONG.value == "long"


class TestMemoryCategory:
    def test_category_values(self):
        assert MemoryCategory.FACT.value == "fact"
        assert MemoryCategory.PREFERENCE.value == "preference"
        assert MemoryCategory.EMOTION.value == "emotion"
        assert MemoryCategory.EVENT.value == "event"
        assert MemoryCategory.USER_INFO.value == "user_info"
        assert MemoryCategory.CONTEXT.value == "context"
        assert MemoryCategory.TASK.value == "task"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
