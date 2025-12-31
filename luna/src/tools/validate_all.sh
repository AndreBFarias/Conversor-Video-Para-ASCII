#!/bin/bash
# src/tools/validate_all.sh
# Roda TODAS as validações de qualidade

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║     VALIDAÇÃO COMPLETA DE QUALIDADE    ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

TOTAL_ERRORS=0
TOTAL_WARNINGS=0

# 1. Anonimato
echo ""
echo -e "${BLUE}[1/7] ANONIMATO${NC}"
if [ -f "src/tools/check_anonymity.sh" ]; then
    bash src/tools/check_anonymity.sh || TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "  ${YELLOW}! Script não encontrado${NC}"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

# 2. IDs Externos (Voice IDs, API Keys)
echo ""
echo -e "${BLUE}[2/7] IDS EXTERNOS${NC}"
if [ -f "src/tools/check_external_ids.sh" ]; then
    bash src/tools/check_external_ids.sh || TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "  ${YELLOW}! Script não encontrado${NC}"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

# 3. Dados de teste
echo ""
echo -e "${BLUE}[3/7] DADOS DE TESTE${NC}"
if [ -f "src/tools/check_test_data.sh" ]; then
    bash src/tools/check_test_data.sh || TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "  ${YELLOW}! Script não encontrado${NC}"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

# 4. Qualidade dos testes
echo ""
echo -e "${BLUE}[4/7] QUALIDADE DOS TESTES${NC}"
if [ -f "src/tools/check_test_quality.sh" ]; then
    bash src/tools/check_test_quality.sh || TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
else
    echo -e "  ${YELLOW}! Script não encontrado${NC}"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

# 5. Testes existem
echo ""
echo -e "${BLUE}[5/7] ARQUIVOS DE TESTE${NC}"
MISSING=0
for file in $(find src/soul src/core src/data_memory -name "*.py" -not -name "__init__.py" 2>/dev/null | head -20); do
    BASENAME=$(basename "$file" .py)
    TEST_FILE="src/tests/test_${BASENAME}.py"
    if [ ! -f "$TEST_FILE" ]; then
        echo -e "  ${YELLOW}!${NC} Sem teste: $file"
        MISSING=$((MISSING + 1))
    fi
done
if [ $MISSING -gt 0 ]; then
    echo -e "  ${YELLOW}$MISSING módulos sem teste${NC}"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
else
    echo -e "  ${GREEN}✓ Todos os módulos têm testes${NC}"
fi

# 6. Lint
echo ""
echo -e "${BLUE}[6/7] LINTING${NC}"
if command -v ruff &>/dev/null; then
    LINT_ERRORS=$(ruff check src/ --output-format=concise 2>/dev/null | wc -l || echo "0")
    if [ "$LINT_ERRORS" -gt 0 ]; then
        echo -e "  ${YELLOW}$LINT_ERRORS problemas de lint${NC}"
        ruff check src/ --output-format=concise 2>/dev/null | head -10
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
    else
        echo -e "  ${GREEN}✓ Lint OK${NC}"
    fi
else
    echo -e "  ${YELLOW}! ruff não instalado${NC}"
fi

# 7. Integração básica
echo ""
echo -e "${BLUE}[7/7] INTEGRAÇÃO${NC}"

echo "  Verificando imports..."
python3 << 'EOF' 2>/dev/null || echo "  ! Alguns imports falharam"
import sys
errors = 0

modules = [
    "config",
    "src.core.logging_config",
    "src.core.file_lock",
]

for mod in modules:
    try:
        __import__(mod)
        print(f"    ✓ {mod}")
    except Exception as e:
        print(f"    ✗ {mod}: {e}")
        errors += 1

sys.exit(errors)
EOF

IMPORT_RESULT=$?
if [ $IMPORT_RESULT -gt 0 ]; then
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
fi

# Resultado final
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"

if [ $TOTAL_ERRORS -eq 0 ] && [ $TOTAL_WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ TODAS AS VALIDAÇÕES PASSARAM${NC}"
    exit 0
elif [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $TOTAL_WARNINGS avisos (não bloqueantes)${NC}"
    exit 0
else
    echo -e "${RED}✗ $TOTAL_ERRORS erro(s) bloqueante(s)${NC}"
    echo -e "${YELLOW}⚠ $TOTAL_WARNINGS aviso(s)${NC}"
    exit 1
fi
