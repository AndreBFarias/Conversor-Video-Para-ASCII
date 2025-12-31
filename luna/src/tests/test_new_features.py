#!/usr/bin/env python3

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.chdir(Path(__file__).parent.parent.parent)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        print(f"  [OK] {name}")
        self.passed += 1

    def fail(self, name, error=""):
        print(f"  [FAIL] {name}: {error}")
        self.failed += 1
        self.errors.append(f"{name}: {error}")


def test_optimized_vector_store():
    print("\n=== OptimizedVectorStore ===")
    result = TestResult()

    try:
        import numpy as np

        from src.data_memory.vector_store_optimized import OptimizedVectorStore

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            store = OptimizedVectorStore(storage_path=temp_path, auto_save_interval=1)

            vec1 = np.random.rand(384).astype(np.float32)
            store.add(id="test1", text="teste de memoria", vector=vec1, source="test")
            result.ok("add() funciona")

            if store.count() == 1:
                result.ok("count() retorna 1")
            else:
                result.fail("count()", f"esperado 1, obteve {store.count()}")

            results = store.search(vec1, limit=5)
            if results and results[0]["similarity"] > 0.99:
                result.ok("search() encontra vetor similar")
            else:
                result.fail("search()", "nao encontrou vetor similar")

            vec2 = np.random.rand(384).astype(np.float32)
            store.add(id="test2", text="outro teste", vector=vec2, source="test")
            if store.increment_frequency("test1"):
                result.ok("increment_frequency() funciona")
            else:
                result.fail("increment_frequency()", "retornou False")

            if store.delete("test2"):
                result.ok("delete() funciona")
            else:
                result.fail("delete()", "retornou False")

            if store.count() == 1:
                result.ok("count() apos delete")
            else:
                result.fail("count() apos delete", f"esperado 1, obteve {store.count()}")

            store.flush()
            if os.path.exists(temp_path):
                result.ok("flush() salva arquivo")
            else:
                result.fail("flush()", "arquivo nao existe")

            store.stop()
            result.ok("stop() funciona")

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        result.fail("import/setup", str(e))

    assert result.failed == 0, f"OptimizedVectorStore failures: {result.errors}"
    return result


def test_smart_memory():
    print("\n=== SmartMemory ===")
    result = TestResult()

    try:
        from src.data_memory.smart_memory import MemoryCategory, SmartMemory
        from src.data_memory.smart_memory.categorizer import MemoryCategorizer

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            memory = SmartMemory.__new__(SmartMemory)
            memory._storage_path = temp_path
            memory._embedding_model = "all-MiniLM-L6-v2"
            memory._max_context_chars = 800
            memory._similarity_threshold = 0.35
            memory._lazy_load = True
            memory._embedder = None
            memory._store = None
            memory._category_index = {}
            memory._summary_cache = {}
            memory._initialized = True
            memory._loaded = False
            memory._categorizer = MemoryCategorizer()

            result.ok("SmartMemory criado")

            cat = memory._categorizer.detect_category("Meu nome e test_user")
            if cat == MemoryCategory.USER_INFO:
                result.ok("detect_category() USER_INFO")
            else:
                result.fail("detect_category()", f"esperado USER_INFO, obteve {cat}")

            cat = memory._categorizer.detect_category("Gosto muito de Python")
            if cat == MemoryCategory.PREFERENCE:
                result.ok("detect_category() PREFERENCE")
            else:
                result.fail("detect_category()", f"esperado PREFERENCE, obteve {cat}")

            summary = memory._categorizer.generate_summary(
                "Este e um texto muito longo que precisa ser resumido para caber em 80 caracteres apenas", max_len=50
            )
            if len(summary) <= 53:
                result.ok("generate_summary() trunca corretamente")
            else:
                result.fail("generate_summary()", f"tamanho {len(summary)} > 53")

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        result.fail("import/setup", str(e))

    assert result.failed == 0, f"SmartMemory failures: {result.errors}"
    return result


def test_terminal_executor():
    print("\n=== TerminalExecutor ===")
    result = TestResult()

    try:
        from src.core.terminal_executor import (
            CommandCategory,
            TerminalCommandRegistry,
            TerminalExecutor,
            parse_natural_command,
        )

        registry = TerminalCommandRegistry()
        result.ok("TerminalCommandRegistry criado")

        if len(registry.commands) >= 0:
            result.ok(f"Comandos carregados: {len(registry.commands)}")

        executor = TerminalExecutor(registry)
        result.ok("TerminalExecutor criado")

        exit_code, stdout, stderr = executor.execute("echo 'teste'", timeout=5)
        if exit_code == 0 and "teste" in stdout:
            result.ok("execute() echo funciona")
        else:
            result.fail("execute()", f"exit={exit_code}, stderr={stderr}")

        exit_code, stdout, stderr = executor.execute("ls /tmp", timeout=5)
        if exit_code == 0:
            result.ok("execute() ls funciona")
        else:
            result.fail("execute() ls", f"exit={exit_code}")

        cmd = parse_natural_command("reiniciar o computador")
        if cmd == "sudo reboot":
            result.ok("parse_natural_command() reiniciar")
        else:
            result.fail("parse_natural_command()", f"esperado 'sudo reboot', obteve '{cmd}'")

        cmd = parse_natural_command("atualizar o sistema")
        if cmd and "apt" in cmd:
            result.ok("parse_natural_command() atualizar")
        else:
            result.fail("parse_natural_command()", f"obteve '{cmd}'")

        cmd = parse_natural_command("abrir a luna")
        if cmd == "santuario Luna":
            result.ok("parse_natural_command() abrir luna")
        else:
            result.fail("parse_natural_command()", f"obteve '{cmd}'")

        for cat in CommandCategory:
            cmds = registry.get_commands_by_category(cat)
            result.ok(f"Categoria {cat.value}: {len(cmds)} comandos")

    except Exception as e:
        result.fail("import/setup", str(e))

    assert result.failed == 0, f"TerminalExecutor failures: {result.errors}"
    return result


def test_session_history():
    print("\n=== SessionHistory ===")
    result = TestResult()

    try:
        from datetime import datetime

        from src.core.session_history import SessionHistoryManager, TimeGroup

        with tempfile.TemporaryDirectory() as temp_dir:
            sessions_dir = Path(temp_dir) / "sessions"
            manifest_file = Path(temp_dir) / "manifest.json"
            sessions_dir.mkdir()

            test_session = {"test_session_1": {"date": datetime.now().isoformat(), "title": "Teste de sessao"}}
            with open(manifest_file, "w") as f:
                json.dump(test_session, f)

            session_file = sessions_dir / "test_session_1.json"
            with open(session_file, "w") as f:
                json.dump(
                    [{"role": "user", "parts": ["Ola Luna"]}, {"role": "assistant", "parts": ["E ai, mortal"]}], f
                )

            manager = SessionHistoryManager(sessions_dir=sessions_dir, manifest_file=manifest_file)
            result.ok("SessionHistoryManager criado")

            sessions = manager.get_all_sessions()
            if len(sessions) == 1:
                result.ok("get_all_sessions() retorna 1")
            else:
                result.fail("get_all_sessions()", f"esperado 1, obteve {len(sessions)}")

            grouped = manager.get_sessions_grouped()
            if TimeGroup.TODAY in grouped:
                result.ok("get_sessions_grouped() tem TODAY")
            else:
                result.fail("get_sessions_grouped()", "falta TODAY")

            results = manager.search_sessions("teste")
            if len(results) == 1:
                result.ok("search_sessions() encontra por titulo")
            else:
                result.fail("search_sessions()", f"esperado 1, obteve {len(results)}")

            content = manager.get_session_content("test_session_1")
            if content and len(content) == 2:
                result.ok("get_session_content() retorna mensagens")
            else:
                result.fail("get_session_content()", "conteudo invalido")

            stats = manager.get_stats()
            if stats["total_sessions"] == 1:
                result.ok("get_stats() correto")
            else:
                result.fail("get_stats()", f"total_sessions={stats['total_sessions']}")

    except Exception as e:
        result.fail("import/setup", str(e))

    assert result.failed == 0, f"SessionHistory failures: {result.errors}"
    return result


def test_response_parser():
    print("\n=== ResponseParser ===")
    result = TestResult()

    try:
        from src.soul.response_parser import UniversalResponseParser, get_simple_prompt_format

        parser = UniversalResponseParser()
        result.ok("UniversalResponseParser criado")

        json_input = '{"fala_tts": "Ola mortal", "leitura": "tedio", "log_terminal": "[Luna olha]", "animacao": "Luna_sarcastica", "comando_visao": false}'
        data, method = parser.parse(json_input)
        if method == "json" and data.get("fala_tts") == "Ola mortal":
            result.ok("parse() JSON direto")
        else:
            result.fail("parse() JSON", f"method={method}, data={data}")

        semicolon_input = "E ai mortal; tom: tedio; animacao: Luna_sarcastica; visao: false"
        data, method = parser.parse(semicolon_input)
        if method in ["semicolon", "field_extraction", "raw_fallback"]:
            result.ok(f"parse() semicolon -> {method}")
        else:
            result.fail("parse() semicolon", f"method={method}")

        raw_input = "Isso e um texto puro sem nenhum formato especial mas ainda assim uma resposta valida"
        data, method = parser.parse(raw_input)
        if data.get("fala_tts"):
            result.ok(f"parse() raw -> {method}")
        else:
            result.fail("parse() raw", "fala_tts vazio")

        empty_data, method = parser.parse("")
        if method == "empty":
            result.ok("parse() vazio retorna 'empty'")
        else:
            result.fail("parse() vazio", f"method={method}")

        prompt = get_simple_prompt_format()
        if "fala:" in prompt and "animacao:" in prompt:
            result.ok("get_simple_prompt_format() retorna formato")
        else:
            result.fail("get_simple_prompt_format()", "formato invalido")

    except Exception as e:
        result.fail("import/setup", str(e))

    assert result.failed == 0, f"ResponseParser failures: {result.errors}"
    return result


def main():
    print("\n" + "=" * 70)
    print("  LUNA NEW FEATURES TEST SUITE")
    print("=" * 70)

    all_results = []

    all_results.append(test_optimized_vector_store())
    all_results.append(test_smart_memory())
    all_results.append(test_terminal_executor())
    all_results.append(test_session_history())
    all_results.append(test_response_parser())

    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)

    print("\n" + "=" * 70)
    print(f"  RESULTADO: {total_passed} passed, {total_failed} failed")
    print("=" * 70)

    if total_failed > 0:
        print("\nErros:")
        for r in all_results:
            for err in r.errors:
                print(f"  - {err}")
        return 1

    print("\nTodos os testes passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
