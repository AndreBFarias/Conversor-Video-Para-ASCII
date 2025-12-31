import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest


class TestSmartMemoryLocks:
    def test_ensure_loaded_thread_safety(self):
        from src.data_memory.smart_memory import SmartMemory

        SmartMemory._instance = None

        load_count = {"count": 0}
        original_init_embedder = None

        def mock_embedder(*args, **kwargs):
            load_count["count"] += 1
            time.sleep(0.01)
            mock = MagicMock()
            mock.encode.return_value = [0.1] * 384
            return mock

        def mock_store(*args, **kwargs):
            mock = MagicMock()
            mock.count.return_value = 0
            mock.memories = []
            return mock

        with patch("src.data_memory.smart_memory.core.EmbeddingGenerator", mock_embedder):
            with patch("src.data_memory.smart_memory.core.OptimizedVectorStore", mock_store):
                memory = SmartMemory(lazy_load=True)

                def call_ensure_loaded():
                    memory._ensure_loaded()

                threads = []
                for _ in range(10):
                    t = threading.Thread(target=call_ensure_loaded)
                    threads.append(t)

                for t in threads:
                    t.start()

                for t in threads:
                    t.join()

                assert (
                    load_count["count"] == 1
                ), f"EmbeddingGenerator inicializado {load_count['count']} vezes (esperado 1)"

        SmartMemory._instance = None

    def test_double_checked_locking_pattern(self):
        from src.data_memory.smart_memory import SmartMemory

        SmartMemory._instance = None

        def mock_store(*args, **kwargs):
            mock = MagicMock()
            mock.count.return_value = 0
            mock.memories = []
            return mock

        def mock_embedder(*args, **kwargs):
            mock = MagicMock()
            mock.encode.return_value = [0.1] * 384
            return mock

        with patch("src.data_memory.smart_memory.core.EmbeddingGenerator", mock_embedder):
            with patch("src.data_memory.smart_memory.core.OptimizedVectorStore", mock_store):
                memory = SmartMemory(lazy_load=True)

                assert memory._loaded is False

                memory._ensure_loaded()

                assert memory._loaded is True

                first_embedder = memory._embedder

                memory._ensure_loaded()

                assert memory._embedder is first_embedder

        SmartMemory._instance = None

    def test_ensure_loaded_raises_memory_load_error(self):
        from src.data_memory import MemoryLoadError
        from src.data_memory.smart_memory import SmartMemory

        SmartMemory._instance = None

        with patch(
            "src.data_memory.smart_memory.core.EmbeddingGenerator", side_effect=Exception("Modelo nao encontrado")
        ):
            memory = SmartMemory(lazy_load=True)

            with pytest.raises(MemoryLoadError) as exc_info:
                memory._ensure_loaded()

            assert "Nao foi possivel carregar memoria" in str(exc_info.value)
            assert memory._loaded is False

        SmartMemory._instance = None

    def test_concurrent_entity_memory_creation(self):
        from src.data_memory.smart_memory import get_entity_smart_memory
        from src.data_memory.smart_memory.singletons import _entity_smart_memories

        _entity_smart_memories.clear()

        entity_id = f"test_entity_{time.time()}"
        created_memories = []

        def create_memory():
            mem = get_entity_smart_memory(entity_id)
            created_memories.append(id(mem))
            return mem

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_memory) for _ in range(5)]
            for future in as_completed(futures):
                future.result()

        unique_ids = set(created_memories)
        assert len(unique_ids) == 1, f"Multiplas instancias criadas: {len(unique_ids)}"

        _entity_smart_memories.clear()


class TestEntityMemoryLocks:
    def test_shared_embedding_gen_thread_safety(self):
        import src.data_memory.entity_memory as em

        em._shared_embedding_gen = None

        init_count = {"count": 0}

        def mock_embedder(*args, **kwargs):
            init_count["count"] += 1
            time.sleep(0.01)
            mock = MagicMock()
            mock.model_name = "test-model"
            mock.dimension = 384
            return mock

        with patch("src.data_memory.entity_memory.EmbeddingGenerator", mock_embedder):

            def get_gen():
                return em._get_shared_embedding_gen()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(get_gen) for _ in range(10)]
                results = [f.result() for f in as_completed(futures)]

            assert init_count["count"] == 1, f"EmbeddingGenerator inicializado {init_count['count']} vezes (esperado 1)"

        em._shared_embedding_gen = None

    def test_shared_embedding_gen_raises_memory_load_error(self):
        import src.data_memory.entity_memory as em
        from src.data_memory import MemoryLoadError

        em._shared_embedding_gen = None

        with patch("src.data_memory.entity_memory.EmbeddingGenerator", side_effect=Exception("GPU nao disponivel")):
            with pytest.raises(MemoryLoadError) as exc_info:
                em._get_shared_embedding_gen()

            assert "Nao foi possivel carregar EmbeddingGenerator" in str(exc_info.value)

        em._shared_embedding_gen = None


class TestCustomExceptions:
    def test_memory_error_hierarchy(self):
        from src.data_memory import MemoryError, MemoryLoadError, MemoryLockError, MemoryWriteError

        assert issubclass(MemoryLoadError, MemoryError)
        assert issubclass(MemoryWriteError, MemoryError)
        assert issubclass(MemoryLockError, MemoryError)

    def test_memory_load_error_from_chain(self):
        from src.data_memory import MemoryLoadError

        original = ValueError("valor invalido")
        error = MemoryLoadError("Falha ao carregar")
        error.__cause__ = original

        assert error.__cause__ is original

    def test_exception_can_be_caught_as_base(self):
        from src.data_memory import MemoryError, MemoryLoadError

        try:
            raise MemoryLoadError("teste")
        except MemoryError as e:
            assert "teste" in str(e)
