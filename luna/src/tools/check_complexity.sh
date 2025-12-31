#!/bin/bash
# src/tools/check_complexity.sh
# Verifica complexidade ciclomatica de funcoes Python
# Funcoes muito complexas sao dificeis de manter e testar

set -e

MAX_COMPLEXITY=15
ERRORS=0
WARNINGS=0

echo "Verificando complexidade ciclomatica..."

python3 << 'PYEOF'
import ast
import sys
from pathlib import Path
import subprocess

MAX_COMPLEXITY = 15
WARNING_THRESHOLD = 10

result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
    capture_output=True, text=True
)
changed_files = [f for f in result.stdout.strip().split('\n')
                 if f.endswith('.py') and f.startswith('src/') and '/tests/' not in f]

HIGH_COMPLEXITY = []
WARNINGS = []

IGNORE_FILES = ["__init__.py", "conftest.py"]

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

def calculate_complexity(node):
    visitor = ComplexityVisitor()
    visitor.visit(node)
    return visitor.complexity

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
            complexity = calculate_complexity(node)

            if complexity > MAX_COMPLEXITY:
                HIGH_COMPLEXITY.append(
                    f"{filepath}:{node.lineno} -> {node.name}() = {complexity}"
                )
            elif complexity > WARNING_THRESHOLD:
                WARNINGS.append(
                    f"{filepath}:{node.lineno} -> {node.name}() = {complexity}"
                )

if WARNINGS:
    print(f"\n{len(WARNINGS)} FUNCOES COM COMPLEXIDADE ALTA (>{WARNING_THRESHOLD}):")
    for w in WARNINGS[:10]:
        print(f"  ! {w}")
    if len(WARNINGS) > 10:
        print(f"  ... e mais {len(WARNINGS) - 10}")

if HIGH_COMPLEXITY:
    print(f"\n{len(HIGH_COMPLEXITY)} FUNCOES COM COMPLEXIDADE CRITICA (>{MAX_COMPLEXITY}):")
    for h in HIGH_COMPLEXITY[:10]:
        print(f"  ! {h}")
    if len(HIGH_COMPLEXITY) > 10:
        print(f"  ... e mais {len(HIGH_COMPLEXITY) - 10}")
    print("\nConsidere:")
    print("  - Extrair funcoes auxiliares")
    print("  - Usar early returns")
    print("  - Simplificar condicoes aninhadas")
    sys.exit(1)

if not WARNINGS and not HIGH_COMPLEXITY:
    print("OK: Complexidade dentro dos limites")

sys.exit(0)
PYEOF
