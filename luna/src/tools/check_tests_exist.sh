#!/bin/bash
# src/tools/check_tests_exist.sh
# Verifica se novos arquivos Python têm testes correspondentes
# Bloqueia commit se arquivo de teste não existir
#
# NOTA: Arquivos dentro de pacotes modularizados (ex: src/core/animation/)
# herdam cobertura do teste do pacote (ex: test_animation.py)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Verificando testes para novos arquivos..."

MISSING_TESTS=()

# Lista de pacotes modularizados que herdam testes do pacote pai
MODULARIZED_PACKAGES=(
    "src/soul/boca"
    "src/soul/consciencia"
    "src/soul/visao"
    "src/soul/threading_manager"
    "src/soul/audio_threads"
    "src/soul/user_profiler"
    "src/soul/live_session"
    "src/soul/onboarding"
    "src/core/animation"
    "src/core/profiler"
    "src/core/ollama_client"
    "src/core/metricas"
    "src/core/desktop_integration"
    "src/data_memory/smart_memory"
    "src/ui/dashboard"
    "src/ui/theme_manager"
    "src/ui/banner"
    "src/ui/screens"
)

is_modularized_submodule() {
    local file="$1"
    local dir=$(dirname "$file")
    for pkg in "${MODULARIZED_PACKAGES[@]}"; do
        # Verifica se o diretório do arquivo começa com o caminho do pacote
        if [[ "$dir" == "$pkg" || "$dir" == "$pkg"/* ]]; then
            return 0
        fi
    done
    return 1
}

# Pegar arquivos Python staged (novos ou modificados)
STAGED_FILES=$(git diff --cached --name-only --diff-filter=A | grep -E "^src/(soul|core|data_memory|ui)/.*\.py$" | grep -v "__init__.py" | grep -v "test_" || true)

for file in $STAGED_FILES; do
    # Extrair nome do módulo
    BASENAME=$(basename "$file" .py)
    DIR=$(dirname "$file")

    # Pular arquivos que já são testes
    if [[ "$BASENAME" == test_* ]]; then
        continue
    fi

    # Pular submodulos de pacotes modularizados (herdam testes do pacote)
    if is_modularized_submodule "$file"; then
        continue
    fi

    # Verificar se teste existe
    TEST_FILE="src/tests/test_${BASENAME}.py"

    if [ ! -f "$TEST_FILE" ]; then
        MISSING_TESTS+=("$file -> $TEST_FILE")
    fi
done

# Resultado
if [ ${#MISSING_TESTS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}========================================"
    echo "  COMMIT BLOQUEADO: TESTES FALTANDO"
    echo -e "========================================${NC}"
    echo ""
    echo "Novos arquivos precisam de testes correspondentes:"
    echo ""
    for item in "${MISSING_TESTS[@]}"; do
        echo -e "  ${YELLOW}!${NC} $item"
    done
    echo ""
    echo "Crie os arquivos de teste ou use --no-verify para pular."
    echo ""
    echo "Template rápido:"
    echo '  echo "import pytest" > src/tests/test_NOME.py'
    echo ""
    exit 1
fi

echo -e "${GREEN}OK: Todos os novos arquivos têm testes${NC}"
exit 0
