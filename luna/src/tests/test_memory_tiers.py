"""Testes para o sistema de memoria em tiers (curto/medio/longo prazo)."""

import time
from unittest.mock import MagicMock, patch

import pytest


class TestShortTermEntry:
    def test_entry_creation(self):
        from src.data_memory.short_term_memory import ShortTermEntry

        entry = ShortTermEntry(
            id="test123",
            content="Meu nome e test_user",
            timestamp=time.time(),
            importance=0.8,
            category="user_info",
        )

        assert entry.id == "test123"
        assert entry.content == "Meu nome e test_user"
        assert entry.importance == 0.8
        assert entry.category == "user_info"
        assert entry.access_count == 0

    def test_entry_not_expired(self):
        from src.data_memory.short_term_memory import ShortTermEntry

        entry = ShortTermEntry(
            id="test",
            content="test content",
            timestamp=time.time(),
        )

        assert entry.is_expired(ttl_seconds=300) is False

    def test_entry_expired(self):
        from src.data_memory.short_term_memory import ShortTermEntry

        old_timestamp = time.time() - 400
        entry = ShortTermEntry(
            id="test",
            content="test content",
            timestamp=old_timestamp,
        )

        assert entry.is_expired(ttl_seconds=300) is True

    def test_entry_to_dict(self):
        from src.data_memory.short_term_memory import ShortTermEntry

        entry = ShortTermEntry(
            id="abc123",
            content="test",
            timestamp=1234567890.0,
            importance=0.6,
            metadata={"key": "value"},
        )

        result = entry.to_dict()

        assert result["id"] == "abc123"
        assert result["content"] == "test"
        assert result["timestamp"] == 1234567890.0
        assert result["importance"] == 0.6
        assert result["metadata"] == {"key": "value"}


class TestShortTermMemory:
    def test_add_memory(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory(ttl_seconds=300, max_size=50)
        entry_id = stm.add("Meu nome e test_user e eu moro em SP", importance=0.7)

        assert entry_id != ""
        assert len(stm) == 1

    def test_add_rejects_short_text(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        entry_id = stm.add("oi", importance=0.5)

        assert entry_id == ""
        assert len(stm) == 0

    def test_get_recent(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        stm.add("Primeira memoria que adiciono aqui", importance=0.5)
        stm.add("Segunda memoria que adiciono aqui", importance=0.6)
        stm.add("Terceira memoria que adiciono aqui", importance=0.7)

        recent = stm.get_recent(limit=2)

        assert len(recent) == 2
        assert recent[0].content == "Terceira memoria que adiciono aqui"

    def test_get_by_query(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        stm.add("Meu nome e test_user e sou programador", importance=0.5)
        stm.add("Eu gosto de cafe e chocolate", importance=0.5)

        results = stm.get("nome", limit=5)

        assert len(results) == 1
        assert "test_user" in results[0].content

    def test_get_promotable_by_importance(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory(promotion_threshold=0.7)
        stm.add("Memoria pouco importante testando", importance=0.3)
        stm.add("Memoria muito importante testando", importance=0.8)

        promotable = stm.get_promotable()

        assert len(promotable) == 1
        assert promotable[0].importance == 0.8

    def test_get_promotable_by_access_count(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory(promotion_threshold=0.9)
        stm.add("Memoria acessada varias vezes", importance=0.4)

        stm.get("acessada", limit=1)
        stm.get("acessada", limit=1)

        promotable = stm.get_promotable()

        assert len(promotable) == 1
        assert promotable[0].access_count >= 2

    def test_mark_promoted(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        entry_id = stm.add("Memoria para promocao teste", importance=0.8)

        assert len(stm) == 1

        success = stm.mark_promoted(entry_id)

        assert success is True
        assert len(stm) == 0

    def test_clear(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        stm.add("Memoria para limpar primeiro", importance=0.5)
        stm.add("Memoria para limpar segundo", importance=0.5)

        assert len(stm) == 2

        stm.clear()

        assert len(stm) == 0

    def test_get_stats(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory(ttl_seconds=300, max_size=50)
        stm.add("Memoria para estatisticas teste", importance=0.5)

        stats = stm.get_stats()

        assert stats["current_size"] == 1
        assert stats["max_size"] == 50
        assert stats["ttl_seconds"] == 300
        assert stats["added"] >= 1

    def test_eviction_on_max_size(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory(max_size=3)
        stm.add("Memoria um para teste de evicao", importance=0.5)
        stm.add("Memoria dois para teste de evicao", importance=0.5)
        stm.add("Memoria tres para teste de evicao", importance=0.5)
        stm.add("Memoria quatro para teste evicao", importance=0.5)

        assert len(stm) == 3
        stats = stm.get_stats()
        assert stats["evicted"] >= 1

    def test_render_context(self):
        from src.data_memory.short_term_memory import ShortTermMemory

        stm = ShortTermMemory()
        stm.add("Meu nome e test_user e sou programador", importance=0.5)

        context = stm.render_context(max_chars=300)

        assert "[SHORT-TERM]" in context
        assert "test_user" in context


class TestShortTermMemorySingleton:
    def test_get_short_term_memory_returns_same_instance(self):
        from src.data_memory.short_term_memory import clear_all_short_term, get_short_term_memory

        clear_all_short_term()

        stm1 = get_short_term_memory("luna")
        stm2 = get_short_term_memory("luna")

        assert stm1 is stm2

    def test_different_entities_get_different_instances(self):
        from src.data_memory.short_term_memory import clear_all_short_term, get_short_term_memory

        clear_all_short_term()

        stm_luna = get_short_term_memory("luna")
        stm_eris = get_short_term_memory("eris")

        assert stm_luna is not stm_eris


class TestMemoryTierManager:
    def test_add_short_term(self):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term

        clear_all_short_term()
        manager = MemoryTierManager("test_entity")
        entry_id = manager.add_short_term("Memoria de curto prazo teste", importance=0.5)

        assert entry_id != ""

    def test_add_high_importance_schedules_promotion(self):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term

        clear_all_short_term()
        manager = MemoryTierManager("test_entity")

        with patch.object(manager, "_schedule_quick_promotion") as mock_schedule:
            manager.add_short_term("Memoria muito importante aqui", importance=0.9)
            mock_schedule.assert_called_once()

    def test_get_tier_stats(self):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term

        clear_all_short_term()
        manager = MemoryTierManager("test_entity")
        manager.add_short_term("Memoria para estatisticas aqui", importance=0.5)

        stats = manager.get_tier_stats()

        assert "entity_id" in stats
        assert stats["entity_id"] == "test_entity"
        assert "short_term" in stats
        assert "promotion_stats" in stats

    def test_clear_short_term(self):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term, get_short_term_memory

        clear_all_short_term()
        manager = MemoryTierManager("test_entity")
        manager.add_short_term("Memoria para limpar no teste", importance=0.5)

        stm = get_short_term_memory("test_entity")
        assert len(stm) == 1

        manager.clear_short_term()
        assert len(stm) == 0

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_promote_entry(self, mock_get_memory):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term, get_short_term_memory

        clear_all_short_term()

        mock_memory = MagicMock()
        mock_memory.add.return_value = "promoted_id"
        mock_get_memory.return_value = mock_memory

        manager = MemoryTierManager("test_entity_promote")
        entry_id = manager.add_short_term("Memoria para promocao real", importance=0.8)

        stm = get_short_term_memory("test_entity_promote")
        initial_count = len(stm)

        with patch.object(manager, "_store_medium_term", return_value=True):
            success = manager.force_promotion(entry_id)

        assert success is True
        assert manager._stats["manual_promotions"] == 1

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_promote_all_eligible(self, mock_get_memory):
        from src.data_memory.memory_tier_manager import MemoryTierManager
        from src.data_memory.short_term_memory import clear_all_short_term

        clear_all_short_term()

        mock_memory = MagicMock()
        mock_memory.add.return_value = "promoted_id"
        mock_get_memory.return_value = mock_memory

        manager = MemoryTierManager("test_entity_eligible")
        manager.add_short_term("Memoria baixa importancia aqui", importance=0.3)
        manager.add_short_term("Memoria alta importancia teste", importance=0.9)

        with patch.object(manager, "_store_medium_term", return_value=True):
            result = manager.promote_all_eligible()

        assert result["promoted"] >= 1
        assert manager._stats["auto_promotions"] >= 1


class TestMemoryTierManagerSingleton:
    def test_get_tier_manager_returns_same_instance(self):
        from src.data_memory.memory_tier_manager import get_tier_manager

        manager1 = get_tier_manager("luna")
        manager2 = get_tier_manager("luna")

        assert manager1 is manager2

    def test_different_entities_get_different_managers(self):
        from src.data_memory.memory_tier_manager import get_tier_manager

        manager_luna = get_tier_manager("luna_test")
        manager_eris = get_tier_manager("eris_test")

        assert manager_luna is not manager_eris


class TestMemoryTierIntegration:
    def test_full_lifecycle(self):
        from src.data_memory.short_term_memory import clear_all_short_term, get_short_term_memory

        clear_all_short_term()

        stm = get_short_term_memory("integration_test")

        entry_id = stm.add("Meu nome e test_user de cidade_teste", importance=0.4, category="user_info")
        assert entry_id != ""

        entries = stm.get("nome", limit=5)
        assert len(entries) >= 1
        assert entries[0].access_count >= 1

        recent = stm.get_recent(limit=3)
        assert len(recent) >= 1

        stats = stm.get_stats()
        assert stats["added"] >= 1

    def test_module_exports(self):
        from src.data_memory import (
            MemoryTierManager,
            ShortTermEntry,
            ShortTermMemory,
            get_short_term_memory,
            get_tier_manager,
        )

        assert ShortTermEntry is not None
        assert ShortTermMemory is not None
        assert get_short_term_memory is not None
        assert MemoryTierManager is not None
        assert get_tier_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
