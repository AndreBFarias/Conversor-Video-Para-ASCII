import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_memory.embeddings import EmbeddingGenerator
from src.data_memory.memory_manager import MemoryManager
from src.data_memory.vector_store import JSONVectorStore


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name: str, elapsed: float = 0):
        self.passed += 1
        print(f"  [OK] {name} ({elapsed:.3f}s)")

    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"TOTAL: {self.passed}/{total} testes passaram")
        if self.errors:
            print("\nFalhas:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        return self.failed == 0


def test_embedding_generator():
    print("\n=== TESTE: EmbeddingGenerator ===")
    results = TestResults()

    start = time.time()
    eg = EmbeddingGenerator()
    results.ok("Inicializacao", time.time() - start)

    start = time.time()
    vec = eg.encode("Ola mundo")
    elapsed = time.time() - start
    if vec.shape[0] == 384:
        results.ok(f"Encode simples (dim={vec.shape[0]})", elapsed)
    else:
        results.fail("Encode simples", f"Dimensao errada: {vec.shape[0]}")

    start = time.time()
    vec2 = eg.encode("Ola mundo")
    elapsed2 = time.time() - start
    if elapsed2 < elapsed * 0.5:
        results.ok("Cache de modelo", elapsed2)
    else:
        results.ok("Segunda query (sem cache significativo)", elapsed2)

    start = time.time()
    vecs = eg.batch_encode(["texto 1", "texto 2", "texto 3"])
    if vecs.shape == (3, 384):
        results.ok(f"Batch encode (shape={vecs.shape})", time.time() - start)
    else:
        results.fail("Batch encode", f"Shape errado: {vecs.shape}")

    vec_empty = eg.encode("")
    if np.allclose(vec_empty, np.zeros(384)):
        results.ok("Texto vazio retorna zeros", 0)
    else:
        results.fail("Texto vazio", "Deveria retornar zeros")

    assert results.failed == 0, f"EmbeddingGenerator failures: {results.errors}"
    return results


def test_vector_store():
    print("\n=== TESTE: JSONVectorStore ===")
    results = TestResults()

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_memories.json"

        start = time.time()
        store = JSONVectorStore(storage_path=store_path)
        results.ok("Inicializacao", time.time() - start)

        if store.count() == 0:
            results.ok("Store vazio inicialmente", 0)
        else:
            results.fail("Store vazio", f"Deveria ter 0, tem {store.count()}")

        vec1 = np.random.rand(384).astype(np.float32)
        start = time.time()
        store.add("id1", "Meu nome e test_user", vec1, "user", {"tag": "nome"})
        results.ok("Adicionar memoria", time.time() - start)

        if store.count() == 1:
            results.ok("Count apos adicao", 0)
        else:
            results.fail("Count", f"Esperado 1, obtido {store.count()}")

        vec2 = np.random.rand(384).astype(np.float32)
        vec3 = np.random.rand(384).astype(np.float32)
        store.add("id2", "Gosto de programar Python", vec2, "user", {})
        store.add("id3", "O clima esta frio hoje", vec3, "user", {})

        start = time.time()
        results_search = store.search(vec1, limit=2)
        elapsed = time.time() - start
        if len(results_search) == 2 and results_search[0]["id"] == "id1":
            results.ok("Busca por similaridade", elapsed)
        else:
            results.fail("Busca", f"Resultado inesperado: {results_search}")

        if store.delete("id3"):
            if store.count() == 2:
                results.ok("Delete memoria", 0)
            else:
                results.fail("Delete", f"Count deveria ser 2, e {store.count()}")
        else:
            results.fail("Delete", "Retornou False")

        store.increment_frequency("id1")
        for mem in store.memories:
            if mem["id"] == "id1":
                freq = mem.get("metadata", {}).get("frequency", 0)
                if freq == 1:
                    results.ok("Increment frequency", 0)
                else:
                    results.fail("Frequency", f"Esperado 1, obtido {freq}")
                break

        store2 = JSONVectorStore(storage_path=store_path)
        if store2.count() == 2:
            results.ok("Persistencia em disco", 0)
        else:
            results.fail("Persistencia", f"Recarregou {store2.count()} memorias")

    assert results.failed == 0, f"JSONVectorStore failures: {results.errors}"
    return results


def test_memory_manager():
    print("\n=== TESTE: MemoryManager ===")
    results = TestResults()

    import src.data_memory.embeddings_cache as ec
    import src.data_memory.embeddings as emb

    ec._cache_instance = None
    emb._generator_instance = None

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_memories.json"

        start = time.time()
        mm = MemoryManager(storage_path=store_path)
        results.ok("Inicializacao", time.time() - start)

        start = time.time()
        mem_id = mm.add_memory("Meu nome e test_user Farias e eu moro em Sao Paulo")
        elapsed = time.time() - start
        if mem_id:
            results.ok("Adicionar memoria valida", elapsed)
        else:
            results.fail("Adicionar memoria", "Retornou None")

        short_id = mm.add_memory("oi")
        if short_id is None:
            results.ok("Rejeita texto curto", 0)
        else:
            results.fail("Texto curto", "Deveria rejeitar 'oi'")

        filler_id = mm.add_memory("ok")
        if filler_id is None:
            results.ok("Rejeita filler phrase", 0)
        else:
            results.fail("Filler", "Deveria rejeitar 'ok'")

        mm.add_memory("Eu trabalho com inteligencia artificial e machine learning")
        mm.add_memory("O tempo esta muito quente hoje em Sao Paulo capital")

        start = time.time()
        ctx = mm.retrieve_context("Onde o test_user mora?", min_similarity=0.3)
        elapsed = time.time() - start
        if ctx and "BIBLIOTECA" in ctx:
            results.ok("Retrieve context", elapsed)
        else:
            results.fail("Retrieve", "Contexto vazio ou invalido")

        same_id = mm.add_memory("Meu nome e test_user Farias e eu moro em Sao Paulo")
        if same_id == mem_id:
            results.ok("Deduplicacao funciona", 0)
        else:
            results.fail("Deduplicacao", f"IDs diferentes: {mem_id} vs {same_id}")

        stats = mm.get_stats()
        if stats["total_memories"] == 3:
            results.ok(f"Stats corretas ({stats['total_memories']} mems)", 0)
        else:
            results.fail("Stats", f"Esperado 3, obtido {stats['total_memories']}")

    assert results.failed == 0, f"MemoryManager failures: {results.errors}"
    return results


def test_similarity_thresholds():
    print("\n=== TESTE: Thresholds de Similaridade ===")
    results = TestResults()

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_memories.json"
        mm = MemoryManager(storage_path=store_path)

        mm.add_memory("Meu cachorro se chama Rex e ele e um labrador preto")
        mm.add_memory("Eu gosto de pizza de calabresa com muito queijo")
        mm.add_memory("O futebol brasileiro e muito competitivo e emocionante")
        mm.add_memory("Python e uma linguagem de programacao muito versatil")

        ctx_high = mm.retrieve_context("Qual o nome do cachorro?", min_similarity=0.8)
        ctx_med = mm.retrieve_context("Qual o nome do cachorro?", min_similarity=0.5)
        ctx_low = mm.retrieve_context("Qual o nome do cachorro?", min_similarity=0.3)

        if len(ctx_low) >= len(ctx_med) >= len(ctx_high):
            results.ok("Threshold inversamente proporcional", 0)
        else:
            results.fail("Threshold", "Relacao invertida")

        ctx_unrelated = mm.retrieve_context("astronomia e galaxias", min_similarity=0.7)
        if len(ctx_unrelated) < 100:
            results.ok("Query nao relacionada retorna pouco", 0)
        else:
            results.fail("Query nao relacionada", f"Retornou {len(ctx_unrelated)} chars")

    assert results.failed == 0, f"Thresholds failures: {results.errors}"
    return results


def test_performance():
    print("\n=== TESTE: Performance ===")
    results = TestResults()

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/perf_memories.json"
        mm = MemoryManager(storage_path=store_path)

        frases = [
            "O usuario gosta de musica classica e jazz",
            "Ele trabalha como desenvolvedor de software",
            "Mora em uma cidade grande com muito transito",
            "Tem um gato chamado Mimi que e muito brincalhao",
            "Prefere cafe sem acucar pela manha",
            "Costuma acordar cedo para fazer exercicios",
            "Le livros de ficcao cientifica nos fins de semana",
            "Viajou para a Europa no ano passado",
            "Estuda inteligencia artificial como hobby",
            "Gosta de cozinhar pratos italianos",
        ]

        start = time.time()
        for frase in frases:
            mm.add_memory(frase)
        add_time = time.time() - start
        results.ok("Adicionar 10 memorias", add_time)

        start = time.time()
        for _ in range(5):
            mm.retrieve_context("O que o usuario gosta de fazer?", min_similarity=0.3)
        query_time = (time.time() - start) / 5
        results.ok("Query media (5 runs)", query_time)

        if query_time < 0.5:
            results.ok("Performance aceitavel (<500ms)", 0)
        else:
            results.fail("Performance", f"Query muito lenta: {query_time:.3f}s")

    assert results.failed == 0, f"Performance failures: {results.errors}"
    return results


def test_smart_memory():
    print("\n=== TESTE: SmartMemory ===")
    results = TestResults()

    import src.data_memory.embeddings_cache as ec
    import src.data_memory.embeddings as emb

    ec._cache_instance = None
    emb._generator_instance = None

    from src.data_memory.smart_memory import MemoryCategory, SmartMemory

    SmartMemory._instance = None

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/smart_memories.json"

        start = time.time()
        sm = SmartMemory(storage_path=store_path, lazy_load=False)
        results.ok("Inicializacao", time.time() - start)

        start = time.time()
        mem_id = sm.add("Meu nome e test_user e eu moro em Sao Paulo capital")
        if mem_id:
            results.ok("Adicionar memoria", time.time() - start)
        else:
            results.fail("Adicionar memoria", "Retornou None")

        sm.add("Eu adoro programar em Python e JavaScript")
        sm.add("Ontem fui ao cinema assistir um filme de terror")
        sm.add("Estou muito feliz hoje com os resultados do projeto")

        stats = sm.get_stats()
        if stats["total_memories"] == 4:
            results.ok(f"Stats corretas ({stats['total_memories']} mems)", 0)
        else:
            results.fail("Stats", f"Esperado 4, obtido {stats['total_memories']}")

        start = time.time()
        ctx = sm.retrieve("Onde o test_user mora?")
        elapsed = time.time() - start
        if ctx and "[MEM]" in ctx:
            results.ok(f"Retrieve compacto ({len(ctx)} chars)", elapsed)
        else:
            results.fail("Retrieve", f"Contexto invalido: {ctx[:50] if ctx else 'vazio'}")

        if len(ctx) < 500:
            results.ok("Contexto compacto (<500 chars)", 0)
        else:
            results.fail("Contexto compacto", f"Muito grande: {len(ctx)} chars")

        slices = sm.retrieve_by_category(MemoryCategory.PREFERENCE, limit=3)
        if isinstance(slices, list):
            results.ok(f"Retrieve by category ({len(slices)} slices)", 0)
        else:
            results.fail("Retrieve by category", "Tipo invalido")

        profile = sm.get_user_profile_context()
        if isinstance(profile, str):
            results.ok(f"User profile context ({len(profile)} chars)", 0)
        else:
            results.fail("User profile", "Tipo invalido")

    assert results.failed == 0, f"SmartMemory failures: {results.errors}"
    return results


def run_all_tests():
    print("=" * 60)
    print("SUITE DE TESTES - BANCO VETORIAL LUNA")
    print("=" * 60)

    all_results = []

    all_results.append(test_embedding_generator())
    all_results.append(test_vector_store())
    all_results.append(test_memory_manager())
    all_results.append(test_similarity_thresholds())
    all_results.append(test_performance())
    all_results.append(test_smart_memory())

    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} testes passaram")

    if total_failed > 0:
        print("\nFalhas encontradas:")
        for r in all_results:
            for name, reason in r.errors:
                print(f"  - {name}: {reason}")
        return False

    print("\nTodos os testes passaram!")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
