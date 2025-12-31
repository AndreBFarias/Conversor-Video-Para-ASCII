#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[CLEANUP] Iniciando limpeza de arquivos residuais...${NC}"
echo ""

TOTAL_FREED=0

count_size() {
    local size=$(du -sb "$1" 2>/dev/null | cut -f1)
    echo "${size:-0}"
}

format_size() {
    local bytes=$1
    if [ "$bytes" -ge 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc) MB"
    elif [ "$bytes" -ge 1024 ]; then
        echo "$(echo "scale=2; $bytes/1024" | bc) KB"
    else
        echo "$bytes B"
    fi
}

if [ -d "src/logs" ]; then
    size_before=$(find src/logs -name "*.log" -exec du -cb {} + 2>/dev/null | tail -1 | cut -f1)
    size_before=${size_before:-0}
    find src/logs -name "*.log" -type f -delete 2>/dev/null
    TOTAL_FREED=$((TOTAL_FREED + size_before))
    echo -e "${GREEN}[OK]${NC} Logs de sessao (.log): $(format_size $size_before)"
fi

if [ -d "src/data_memory/cache" ]; then
    size_before=$(find src/data_memory/cache -name "*.db" -exec du -cb {} + 2>/dev/null | tail -1 | cut -f1)
    size_before=${size_before:-0}
    find src/data_memory/cache -name "*.db" -type f -delete 2>/dev/null
    TOTAL_FREED=$((TOTAL_FREED + size_before))
    echo -e "${GREEN}[OK]${NC} Cache SQLite (.db): $(format_size $size_before)"
fi

size_before=$(find src -type d -name "__pycache__" -exec du -sb {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
size_before=${size_before:-0}
find src -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
TOTAL_FREED=$((TOTAL_FREED + size_before))
echo -e "${GREEN}[OK]${NC} Bytecode (__pycache__): $(format_size $size_before)"

if [ -d "src/models" ]; then
    size_before=$(find src/models -path "*/xet/logs/*" -name "*.log" -exec du -cb {} + 2>/dev/null | tail -1 | cut -f1)
    size_before=${size_before:-0}
    find src/models -path "*/xet/logs/*" -name "*.log" -delete 2>/dev/null || true
    TOTAL_FREED=$((TOTAL_FREED + size_before))
    echo -e "${GREEN}[OK]${NC} Logs XET de modelos: $(format_size $size_before)"
fi

find . -name "*.pyc" -type f -delete 2>/dev/null || true
find . -name "*.pyo" -type f -delete 2>/dev/null || true
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
find . -name "*.tmp" -type f -delete 2>/dev/null || true
find . -name "*~" -type f -delete 2>/dev/null || true
echo -e "${GREEN}[OK]${NC} Arquivos temporarios (.pyc, .pyo, .tmp, ~)"

echo ""
echo -e "${YELLOW}[PRESERVADO]${NC} src/logs/*.json (eventos)"
echo -e "${YELLOW}[PRESERVADO]${NC} src/logs/qa_reports/"
echo -e "${YELLOW}[PRESERVADO]${NC} src/logs/screenshots/"
echo ""
echo -e "${GREEN}[CLEANUP COMPLETO]${NC} Espaco liberado: $(format_size $TOTAL_FREED)"
