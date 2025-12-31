#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

if [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
else
    PYTHON="python3"
fi

$PYTHON src/tools/check_acentuacao.py
