#!/bin/bash
# src/tools/quick_check.sh
# Verificacao rapida para uso durante desenvolvimento
# Roda apenas checks essenciais (< 5 segundos)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Quick Check - Luna${NC}"
echo "═══════════════════════════════════════"

ERRORS=0

# 1. Anonimato (critico)
echo -n "Anonimato: "
if bash src/tools/check_anonymity.sh > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHOU${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. IDs Externos (critico)
echo -n "IDs Externos: "
if bash src/tools/check_external_ids.sh > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHOU${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 3. Lint (apenas erros criticos)
echo -n "Lint (E9,F63): "
LINT_ERRORS=$(ruff check src/ --select=E9,F63,F7,F82 --output-format=concise 2>/dev/null | wc -l || echo "0")
if [ "$LINT_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}$LINT_ERRORS erros${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 4. Import basico
echo -n "Imports: "
if python3 -c "import config" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHOU${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo "═══════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}Todos os checks passaram${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS erro(s) encontrado(s)${NC}"
    echo "Execute ./src/tools/validate_all.sh para detalhes"
    exit 1
fi
