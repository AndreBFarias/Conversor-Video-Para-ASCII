#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=true
if [[ "$1" == "--execute" ]]; then
    DRY_RUN=false
fi

echo -e "${BLUE}=== Analise de Arquivos Obsoletos ===${NC}"
echo ""

TOTAL_SAVED=0

log_action() {
    local action="$1"
    local size="$2"
    local path="$3"

    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $action: $path ($size)"
    else
        echo -e "${GREEN}[EXEC]${NC} $action: $path ($size)"
    fi
}

echo -e "${BLUE}1. Cache Python (__pycache__)${NC}"
PYCACHE_COUNT=$(find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./venv/*" -not -path "./venv_tts/*" 2>/dev/null | wc -l)
PYCACHE_SIZE=$(find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./venv/*" -not -path "./venv_tts/*" -exec du -sh {} \; 2>/dev/null | awk '{sum += $1} END {print sum}')
echo "   Encontrados: $PYCACHE_COUNT diretorios"
if ! $DRY_RUN; then
    find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./venv/*" -not -path "./venv_tts/*" -exec rm -rf {} + 2>/dev/null || true
    echo -e "   ${GREEN}Removidos${NC}"
fi

echo ""
echo -e "${BLUE}2. Logs antigos (>7 dias)${NC}"
OLD_LOGS=$(find src/logs -type f \( -name "*.log" -o -name "*.json" \) -mtime +7 2>/dev/null | wc -l)
OLD_LOGS_SIZE=$(find src/logs -type f \( -name "*.log" -o -name "*.json" \) -mtime +7 -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
echo "   Encontrados: $OLD_LOGS arquivos ($OLD_LOGS_SIZE)"
if ! $DRY_RUN; then
    find src/logs -type f \( -name "*.log" -o -name "*.json" \) -mtime +7 -delete 2>/dev/null || true
    echo -e "   ${GREEN}Removidos${NC}"
fi

echo ""
echo -e "${BLUE}3. Pastas de teste vazias${NC}"
TEST_DIRS=$(find src/data_memory/sessions -type d -name "test_entity*" 2>/dev/null | wc -l)
echo "   Encontradas: $TEST_DIRS pastas"
if ! $DRY_RUN; then
    find src/data_memory/sessions -type d -name "test_entity*" -exec rm -rf {} + 2>/dev/null || true
    echo -e "   ${GREEN}Removidas${NC}"
fi

echo ""
echo -e "${BLUE}4. Arquivos de lock vazios${NC}"
LOCK_FILES=$(find src/models -type f -name "*.lock" -size 0 2>/dev/null | wc -l)
echo "   Encontrados: $LOCK_FILES arquivos"
if ! $DRY_RUN; then
    find src/models -type f -name "*.lock" -size 0 -delete 2>/dev/null || true
    echo -e "   ${GREEN}Removidos${NC}"
fi

echo ""
echo -e "${BLUE}5. Diretorio .no_exist (sentence-transformers)${NC}"
NO_EXIST=$(find src/models -type d -name ".no_exist" 2>/dev/null | wc -l)
echo "   Encontrados: $NO_EXIST diretorios"
if ! $DRY_RUN; then
    find src/models -type d -name ".no_exist" -exec rm -rf {} + 2>/dev/null || true
    echo -e "   ${GREEN}Removidos${NC}"
fi

echo ""
echo -e "${BLUE}6. Cache TTS duplicado${NC}"
if [ -d "src/models/tts/hub" ] && [ -d "src/models/tts/chatterbox" ]; then
    HUB_SIZE=$(du -sh src/models/tts/hub 2>/dev/null | cut -f1)
    echo "   src/models/tts/hub: $HUB_SIZE (duplicado de chatterbox)"
    echo -e "   ${YELLOW}[MANUAL]${NC} Remover manualmente se confirmado duplicado"
else
    echo "   Nenhum duplicado encontrado"
fi

echo ""
echo -e "${BLUE}7. Pastas vazias${NC}"
EMPTY_DIRS=$(find src -type d -empty -not -path "./.git/*" 2>/dev/null | wc -l)
echo "   Encontradas: $EMPTY_DIRS pastas vazias"
if ! $DRY_RUN; then
    find src -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true
    echo -e "   ${GREEN}Removidas${NC}"
fi

echo ""
echo -e "${BLUE}=== Resumo ===${NC}"
if $DRY_RUN; then
    echo -e "${YELLOW}Modo DRY-RUN: nenhuma alteracao foi feita${NC}"
    echo "Execute com --execute para aplicar as mudancas"
else
    echo -e "${GREEN}Limpeza concluida!${NC}"
fi

echo ""
echo "Espaco atual do projeto (excluindo .git e venvs):"
du -sh . --exclude=.git --exclude=venv --exclude=venv_tts 2>/dev/null
