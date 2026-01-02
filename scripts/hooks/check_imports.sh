#!/bin/bash
# Hook de verificacao de imports
# Verifica se os imports principais funcionam

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}[ERRO] venv nao encontrado em $PROJECT_ROOT/venv${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "[IMPORTS] Verificando imports principais..."

ERRORS=0

if ! $VENV_PYTHON -c "from src.app import App; print('App OK')" 2>/dev/null; then
    echo -e "${RED}[ERRO] Falha ao importar src.app.App${NC}"
    $VENV_PYTHON -c "from src.app import App" 2>&1 | tail -5
    ERRORS=$((ERRORS + 1))
fi

if ! $VENV_PYTHON -c "from src.core.converter import iniciar_conversao; print('Converter OK')" 2>/dev/null; then
    echo -e "${RED}[ERRO] Falha ao importar src.core.converter${NC}"
    ERRORS=$((ERRORS + 1))
fi

if ! $VENV_PYTHON -c "from src.utils.logger import setup_logger; print('Logger OK')" 2>/dev/null; then
    echo -e "${RED}[ERRO] Falha ao importar src.utils.logger${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}[OK] Imports verificados - Todos funcionando${NC}"
    exit 0
else
    echo -e "${RED}[ERRO] $ERRORS import(s) falharam${NC}"
    exit 1
fi
