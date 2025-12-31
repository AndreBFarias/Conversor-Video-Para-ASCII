#!/bin/bash
# src/tools/check_test_quality.sh
# Detecta testes fake, vazios e asserts fracos

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== VERIFICANDO QUALIDADE DOS TESTES ==="

python3 << 'PYEOF'
import ast
import sys
from pathlib import Path

FAKE_TESTS = []
EMPTY_FUNCS = []
WEAK_ASSERTS = []

test_dir = Path("src/tests")
if not test_dir.exists():
    print("  ! Diretório src/tests/ não encontrado")
    sys.exit(0)

for pyfile in test_dir.rglob("test_*.py"):
    try:
        tree = ast.parse(pyfile.read_text())
    except Exception as e:
        print(f"  ! Erro ao parsear: {pyfile}: {e}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("test_"):
                continue

            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    FAKE_TESTS.append(f"{pyfile.name}:{node.lineno} -> {node.name}() = pass")
                    continue
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    if stmt.value.value == ...:
                        FAKE_TESTS.append(f"{pyfile.name}:{node.lineno} -> {node.name}() = ...")
                        continue

            assert_count = 0
            has_real_assert = False

            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    assert_count += 1
                    if isinstance(child.test, ast.Constant):
                        if child.test.value in (True, 1, "ok"):
                            WEAK_ASSERTS.append(f"{pyfile.name}:{node.lineno} -> {node.name}(): assert True")
                        else:
                            has_real_assert = True
                    else:
                        has_real_assert = True

                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        attr = child.func.attr
                        # unittest assertions
                        if attr.startswith("assert") or attr.startswith("Assert"):
                            has_real_assert = True
                        # pytest assertions
                        elif attr in ("raises", "warns", "approx"):
                            has_real_assert = True
                        # mock assertions
                        elif attr.startswith("assert_called"):
                            has_real_assert = True

            if assert_count == 0 and not has_real_assert:
                EMPTY_FUNCS.append(f"{pyfile.name}:{node.lineno} -> {node.name}(): sem assert")

errors = 0

if FAKE_TESTS:
    print(f"\n{len(FAKE_TESTS)} TESTES FAKE (so pass/...):")
    for t in FAKE_TESTS[:15]:
        print(f"  ! {t}")
    if len(FAKE_TESTS) > 15:
        print(f"  ... e mais {len(FAKE_TESTS) - 15}")
    errors += len(FAKE_TESTS)

if WEAK_ASSERTS:
    print(f"\n{len(WEAK_ASSERTS)} ASSERTS FRACOS (assert True):")
    for t in WEAK_ASSERTS[:15]:
        print(f"  ! {t}")
    if len(WEAK_ASSERTS) > 15:
        print(f"  ... e mais {len(WEAK_ASSERTS) - 15}")
    errors += len(WEAK_ASSERTS)

if EMPTY_FUNCS:
    print(f"\n{len(EMPTY_FUNCS)} TESTES SEM ASSERT:")
    for t in EMPTY_FUNCS[:15]:
        print(f"  ! {t}")
    if len(EMPTY_FUNCS) > 15:
        print(f"  ... e mais {len(EMPTY_FUNCS) - 15}")
    errors += len(EMPTY_FUNCS)

if errors == 0:
    print("\n✓ Todos os testes têm conteúdo real")
    sys.exit(0)
else:
    print(f"\n✗ {errors} problemas de qualidade encontrados")
    sys.exit(1)
PYEOF
