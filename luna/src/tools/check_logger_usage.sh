#!/bin/bash
# src/tools/check_logger_usage.sh
# Verifica se modulos Python usam logger ao inves de print()

set -e

ERRORS=0
WARNINGS=0

IGNORE_FILES=(
    "conftest.py"
    "__init__.py"
    "run_tests.py"
)

is_ignored() {
    local file="$1"
    for pattern in "${IGNORE_FILES[@]}"; do
        if [[ "$file" == *"$pattern"* ]]; then
            return 0
        fi
    done
    return 1
}

echo "Verificando uso de logger..."

for file in $(git diff --cached --name-only --diff-filter=AM | grep -E '\.py$'); do
    if [[ ! -f "$file" ]]; then
        continue
    fi

    if [[ "$file" == *"/tests/"* ]]; then
        continue
    fi

    if is_ignored "$file"; then
        continue
    fi

    has_logger=$(grep -c "from src.core.logging_config import" "$file" 2>/dev/null || echo "0")
    has_print=$(grep -cE "^\s*print\(" "$file" 2>/dev/null || echo "0")

    if [[ $has_print -gt 0 ]]; then
        if [[ $has_logger -eq 0 ]]; then
            echo "ERRO: $file usa print() sem logger configurado"
            echo "  -> Adicione: from src.core.logging_config import get_logger"
            echo "  -> Use: logger = get_logger(__name__)"
            ERRORS=$((ERRORS + 1))
        else
            echo "AVISO: $file tem $has_print print() que podem ser convertidos para logger"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "FALHA: $ERRORS arquivo(s) sem logger configurado usando print()"
    exit 1
fi

if [[ $WARNINGS -gt 0 ]]; then
    echo "AVISO: $WARNINGS arquivo(s) com print() que podem ser migrados para logger"
fi

echo "OK: Verificacao de logger concluida"
exit 0
