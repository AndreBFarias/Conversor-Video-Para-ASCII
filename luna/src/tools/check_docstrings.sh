#!/bin/bash
# src/tools/check_docstrings.sh
# Verifica se modulos e classes publicas tem docstrings

set -e

echo "Verificando docstrings em modulos novos/modificados..."

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

MISSING_MODULE = []
MISSING_CLASS = []
MISSING_PUBLIC = []

IGNORE_FILES = ["__init__.py", "conftest.py"]

for filepath in changed_files:
    if not filepath or any(ig in filepath for ig in IGNORE_FILES):
        continue

    path = Path(filepath)
    if not path.exists():
        continue

    try:
        content = path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        print(f"  ! Erro ao parsear {filepath}: {e}")
        continue

    if not ast.get_docstring(tree):
        MISSING_MODULE.append(filepath)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith('_') and not ast.get_docstring(node):
                MISSING_CLASS.append(f"{filepath}:{node.lineno} -> class {node.name}")

        if isinstance(node, ast.FunctionDef):
            if (not node.name.startswith('_') and
                node.col_offset == 0 and
                not ast.get_docstring(node)):
                MISSING_PUBLIC.append(f"{filepath}:{node.lineno} -> def {node.name}()")

total = len(MISSING_MODULE) + len(MISSING_CLASS) + len(MISSING_PUBLIC)

if MISSING_MODULE:
    print(f"\n{len(MISSING_MODULE)} MODULOS SEM DOCSTRING:")
    for m in MISSING_MODULE[:10]:
        print(f"  ! {m}")

if MISSING_CLASS:
    print(f"\n{len(MISSING_CLASS)} CLASSES PUBLICAS SEM DOCSTRING:")
    for c in MISSING_CLASS[:10]:
        print(f"  ! {c}")

if MISSING_PUBLIC:
    print(f"\n{len(MISSING_PUBLIC)} FUNCOES PUBLICAS (top-level) SEM DOCSTRING:")
    for f in MISSING_PUBLIC[:10]:
        print(f"  ! {f}")

if total == 0:
    print("OK: Todos os modulos modificados tem docstrings")
    sys.exit(0)
else:
    print(f"\nAVISO: {total} itens sem docstring (nao bloqueante)")
    sys.exit(0)  # Warning only, nao bloqueia commit
PYEOF
