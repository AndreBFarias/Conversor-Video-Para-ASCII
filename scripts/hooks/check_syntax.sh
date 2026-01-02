#!/bin/bash
# Hook de verificacao de sintaxe Python
# Verifica se todos os arquivos Python tem sintaxe valida

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

echo "[SYNTAX] Verificando sintaxe Python..."

ERRORS=0

while IFS= read -r -d '' file; do
    if ! $VENV_PYTHON -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}[ERRO] Sintaxe invalida: $file${NC}"
        $VENV_PYTHON -m py_compile "$file" 2>&1 | head -5
        ERRORS=$((ERRORS + 1))
    fi
done < <(find "$SRC_DIR" -name "*.py" -print0)

if ! $VENV_PYTHON -m py_compile "$PROJECT_ROOT/main.py" 2>/dev/null; then
    echo -e "${RED}[ERRO] Sintaxe invalida: main.py${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}[OK] Sintaxe verificada - Todos os arquivos validos${NC}"
    exit 0
else
    echo -e "${RED}[ERRO] $ERRORS arquivo(s) com sintaxe invalida${NC}"
    exit 1
fi
