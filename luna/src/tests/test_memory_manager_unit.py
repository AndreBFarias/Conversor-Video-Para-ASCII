import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMemoryManagerInit:
    def test_init_creates_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = f"{tmpdir}/memories.json"

            with patch("src.data_memory.memory_manager.EmbeddingGenerator") as mock_gen:
                mock_gen.return_value = MagicMock()

                from src.data_memory.memory_manager import MemoryManager

                mm = MemoryManager(storage_path=storage_path)

                assert mm is not None
                assert mm.vector_store is not None

    def test_init_with_custom_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = f"{tmpdir}/custom_memories.json"

            with patch("src.data_memory.memory_manager.EmbeddingGenerator") as mock_gen:
                mock_gen.return_value = MagicMock()

                from src.data_memory.memory_manager import MemoryManager

                mm = MemoryManager(storage_path=custom_path)

                assert str(custom_path) in str(mm.vector_store._storage.storage_path)


class TestMemoryValidation:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_rejects_short_text(self, mock_gen):
        mock_gen.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            result = mm.add_memory("oi")

            assert result is None

    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_rejects_filler_phrases(self, mock_gen):
        mock_gen.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")

            assert mm.add_memory("ok") is None
            assert mm.add_memory("entendi") is None
            assert mm.add_memory("certo") is None


class TestAddMemory:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_add_valid_memory_returns_id(self, mock_gen):
        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = np.random.rand(384)
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            result = mm.add_memory("Este e um texto valido com mais de vinte caracteres")

            assert result is not None
            assert isinstance(result, str)


class TestRetrieveContext:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_retrieve_returns_string(self, mock_gen):
        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = np.random.rand(384)
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            mm.add_memory("Meu nome e test_user e eu trabalho com IA")

            context = mm.retrieve_context("Qual o nome do usuario")

            assert isinstance(context, str)

    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_retrieve_empty_query(self, mock_gen):
        mock_gen.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            context = mm.retrieve_context("")

            assert context == "" or isinstance(context, str)


class TestGetStats:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_get_stats_returns_dict(self, mock_gen):
        mock_gen.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            stats = mm.get_stats()

            assert isinstance(stats, dict)
            assert "total_memories" in stats


class TestDeduplication:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_duplicate_returns_same_id(self, mock_gen):
        mock_embedding = MagicMock()
        fixed_vec = np.random.rand(384)
        mock_embedding.encode.return_value = fixed_vec
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            text = "Este e um texto unico para teste de deduplicacao"

            id1 = mm.add_memory(text)
            id2 = mm.add_memory(text)

            assert id1 == id2


class TestClearMemories:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_clear_old_memories(self, mock_gen):
        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = np.random.rand(384)
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            mm.add_memory("Memoria para teste de limpeza com mais de vinte caracteres")

            initial_count = mm.get_stats()["total_memories"]

            mm.clear_old_memories(days=0)

            assert mm.get_stats()["total_memories"] <= initial_count


class TestMinSimilarity:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_retrieve_with_high_threshold(self, mock_gen):
        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = np.random.rand(384)
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            mm.add_memory("Gosto muito de programar em Python e JavaScript")

            context = mm.retrieve_context("programacao", min_similarity=0.99)

            assert isinstance(context, str)


class TestSourceMetadata:
    @patch("src.data_memory.memory_manager.EmbeddingGenerator")
    def test_add_memory_with_source(self, mock_gen):
        mock_embedding = MagicMock()
        mock_embedding.encode.return_value = np.random.rand(384)
        mock_gen.return_value = mock_embedding

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.memory_manager import MemoryManager

            mm = MemoryManager(storage_path=f"{tmpdir}/mem.json")
            result = mm.add_memory("Memoria com source customizado para teste", source="custom_source")

            assert result is not None
