#!/bin/bash
# src/tools/check_type_hints.sh
# Verifica type hints em funcoes publicas

set -e

echo "Verificando type hints em funcoes publicas..."

python3 << 'PYEOF'
import ast
import sys
from pathlib import Path
import subprocess

result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
    capture_output=True, text=True
)
changed_files = [f for f in result.stdout.strip().split('\n')
                 if f.endswith('.py') and f.startswith('src/') and '/tests/' not in f]

MISSING_RETURN = []
MISSING_ARGS = []

IGNORE_FILES = ["__init__.py", "conftest.py"]
IGNORE_FUNCS = ["__init__", "__str__", "__repr__", "__eq__", "__hash__"]

for filepath in changed_files:
    if not filepath or any(ig in filepath for ig in IGNORE_FILES):
        continue

    path = Path(filepath)
    if not path.exists():
        continue

    try:
        tree = ast.parse(path.read_text())
    except Exception:
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_') and node.name not in IGNORE_FUNCS:
                continue
            if node.name in IGNORE_FUNCS:
                continue

            is_method = node.col_offset > 0

            if node.returns is None and node.name not in IGNORE_FUNCS:
                MISSING_RETURN.append(f"{filepath}:{node.lineno} -> {node.name}()")

            for i, arg in enumerate(node.args.args):
                if arg.arg in ('self', 'cls'):
                    continue
                if arg.annotation is None:
                    MISSING_ARGS.append(f"{filepath}:{node.lineno} -> {node.name}({arg.arg})")

total = len(MISSING_RETURN) + len(MISSING_ARGS)

if MISSING_RETURN:
    print(f"\n{len(MISSING_RETURN)} FUNCOES SEM RETURN TYPE:")
    for m in MISSING_RETURN[:10]:
        print(f"  - {m}")
    if len(MISSING_RETURN) > 10:
        print(f"  ... e mais {len(MISSING_RETURN) - 10}")

if MISSING_ARGS:
    print(f"\n{len(MISSING_ARGS)} ARGUMENTOS SEM TYPE HINT:")
    for a in MISSING_ARGS[:10]:
        print(f"  - {a}")
    if len(MISSING_ARGS) > 10:
        print(f"  ... e mais {len(MISSING_ARGS) - 10}")

if total == 0:
    print("OK: Todas as funcoes publicas tem type hints")
    sys.exit(0)
else:
    print(f"\nAVISO: {total} itens sem type hints (nao bloqueante no commit)")
    sys.exit(0)  # Warning only
PYEOF
