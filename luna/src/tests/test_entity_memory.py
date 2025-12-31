import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEntityMemoryManagerInit:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_init_creates_stores(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm.entity_id == "luna"
            assert mock_store.call_count == 2

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_init_sets_defaults(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm.min_text_length == 20
            assert emm.dedup_threshold == 0.92
            assert emm.min_similarity == 0.40


class TestIsValidMemory:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_rejects_short_text(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm._is_valid_memory("oi") is False
            assert emm._is_valid_memory("abc") is False

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_rejects_filler_phrases(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm._is_valid_memory("ok") is False
            assert emm._is_valid_memory("entendi") is False
            assert emm._is_valid_memory("valeu") is False

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_rejects_commands(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm._is_valid_memory("/comando aqui") is False
            assert emm._is_valid_memory("!outro comando") is False

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_accepts_valid_text(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm._is_valid_memory("Este e um texto valido com mais de 20 caracteres") is True

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_rejects_none_and_empty(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            assert emm._is_valid_memory(None) is False
            assert emm._is_valid_memory("") is False
            assert emm._is_valid_memory("   ") is False


class TestGetStoreForSource:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_global_sources_use_global_store(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_global = MagicMock(count=MagicMock(return_value=0))
        mock_entity = MagicMock(count=MagicMock(return_value=0))
        mock_store.side_effect = [mock_global, mock_entity]

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            for source in ["user_profile", "face_recognition", "preference", "fact"]:
                store = emm._get_store_for_source(source)
                assert store == mock_global

    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_session_sources_use_entity_store(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_global = MagicMock(count=MagicMock(return_value=0))
        mock_entity = MagicMock(count=MagicMock(return_value=0))
        mock_store.side_effect = [mock_global, mock_entity]

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            for source in ["conversation", "user_input", "luna_response"]:
                store = emm._get_store_for_source(source)
                assert store == mock_entity


class TestGetStats:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_get_stats_returns_dict(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb_instance = MagicMock()
        mock_emb_instance.model_name = "test-model"
        mock_emb_instance.dimension = 384
        mock_emb.return_value = mock_emb_instance

        mock_store_instance = MagicMock()
        mock_store_instance.count.return_value = 10
        mock_store_instance.get_stats.return_value = {"indexed": True}
        mock_store.return_value = mock_store_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)
            stats = emm.get_stats()

            assert isinstance(stats, dict)
            assert stats["entity_id"] == "luna"
            assert "global_memories" in stats
            assert "entity_memories" in stats
            assert "total_memories" in stats


class TestSwitchEntity:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_switch_returns_new_manager(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb_instance = MagicMock()
        mock_emb_instance.model_name = "test-model"
        mock_emb.return_value = mock_emb_instance

        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)
            new_emm = emm.switch_entity("eris")

            assert new_emm.entity_id == "eris"
            assert new_emm is not emm


class TestEntityMemoryFactory:
    @patch("src.data_memory.entity_memory.EntityMemoryManager")
    def test_get_entity_memory_creates_new(self, mock_emm):
        from src.data_memory.entity_memory import _entity_memory_managers, get_entity_memory

        _entity_memory_managers.clear()
        mock_emm.return_value = MagicMock(entity_id="test_entity")

        result = get_entity_memory("test_entity")

        assert "test_entity" in _entity_memory_managers

    @patch("src.data_memory.entity_memory.EntityMemoryManager")
    def test_get_entity_memory_returns_cached(self, mock_emm):
        from src.data_memory.entity_memory import _entity_memory_managers, get_entity_memory

        _entity_memory_managers.clear()
        mock_instance = MagicMock(entity_id="cached_entity")
        mock_emm.return_value = mock_instance

        first = get_entity_memory("cached_entity")
        second = get_entity_memory("cached_entity")

        assert first is second
        assert mock_emm.call_count == 1


class TestSwitchEntityMemory:
    @patch("src.data_memory.entity_memory.get_entity_memory")
    def test_switch_returns_new_manager(self, mock_get):
        from src.data_memory.entity_memory import switch_entity_memory

        mock_new = MagicMock(entity_id="new_entity")
        mock_get.return_value = mock_new

        result = switch_entity_memory("old_entity", "new_entity")

        mock_get.assert_called_once_with("new_entity")
        assert result == mock_new


class TestCacheEmbedding:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_cache_stores_embedding(self, mock_store, mock_emb):
        import numpy as np

        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb_instance = MagicMock()
        mock_emb_instance.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_emb.return_value = mock_emb_instance

        mock_store.return_value = MagicMock(count=MagicMock(return_value=0))

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)

            vec1 = emm._get_cached_embedding("test text")
            vec2 = emm._get_cached_embedding("test text")

            assert mock_emb_instance.encode.call_count == 1
            assert np.array_equal(vec1, vec2)


class TestClearEntityMemories:
    @patch("src.data_memory.entity_memory._get_shared_embedding_gen")
    @patch("src.data_memory.entity_memory.OptimizedVectorStore")
    def test_clear_all_memories(self, mock_store, mock_emb):
        from src.data_memory.entity_memory import EntityMemoryManager

        mock_emb.return_value = MagicMock()
        mock_entity_store = MagicMock()
        mock_entity_store.count.return_value = 5
        mock_entity_store.memories = [1, 2, 3, 4, 5]

        mock_store.side_effect = [MagicMock(count=MagicMock(return_value=0)), mock_entity_store]

        with tempfile.TemporaryDirectory() as tmpdir:
            emm = EntityMemoryManager("luna", base_path=tmpdir)
            count = emm.clear_entity_memories()

            assert count == 5
            mock_entity_store.flush.assert_called_once()
