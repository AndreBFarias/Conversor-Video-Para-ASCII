#!/bin/bash
# src/tools/check_orphan_code.sh
# Detecta modulos Python que nao sao importados em nenhum lugar (codigo orfao)
# Uso: ./src/tools/check_orphan_code.sh

set -e

ORPHANS=()
WARNINGS=()

# Diretorios a verificar
DIRS=(
    "src/soul"
    "src/core"
    "src/data_memory"
    "src/ui"
    "src/app"
    "src/web"
)

# Arquivos a ignorar (entry points, __init__, etc)
IGNORE_PATTERNS=(
    "__init__.py"
    "__pycache__"
    "conftest.py"
)

check_module_usage() {
    local file="$1"
    local module_name=$(basename "$file" .py)
    local dir_name=$(dirname "$file")

    # Ignorar arquivos especiais
    for pattern in "${IGNORE_PATTERNS[@]}"; do
        if [[ "$file" == *"$pattern"* ]]; then
            return 0
        fi
    done

    # Construir nome do modulo para import
    # src/soul/foo.py -> src.soul.foo ou soul.foo
    local import_path="${file%.py}"
    import_path="${import_path//\//.}"

    # Verificar se e importado em algum lugar (src/ + main.py + run_*.py)
    local short_import="from.*${module_name}|import.*${module_name}"
    local found=$(grep -rlE "$short_import" src/ main.py run_*.py --include="*.py" 2>/dev/null | grep -v "$file" | grep -v "test_" | head -1)

    if [[ -z "$found" ]]; then
        # Verificar se tem teste correspondente
        local test_file="src/tests/test_${module_name}.py"
        if [[ -f "$test_file" ]]; then
            # Tem teste mas nao e usado - warning
            WARNINGS+=("$file (tem teste mas nao e importado)")
        else
            # Nao tem teste E nao e usado - orfao
            ORPHANS+=("$file")
        fi
    fi
}

echo "Verificando modulos orfaos..."
echo ""

for dir in "${DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        for file in "$dir"/*.py; do
            if [[ -f "$file" ]]; then
                check_module_usage "$file"
            fi
        done
    fi
done

# Reportar warnings
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "WARNINGS (tem teste mas nao e importado):"
    for w in "${WARNINGS[@]}"; do
        echo "  - $w"
    done
    echo ""
fi

# Reportar orfaos
if [[ ${#ORPHANS[@]} -gt 0 ]]; then
    echo "ERRO: Modulos orfaos detectados (sem importacao E sem teste):"
    for o in "${ORPHANS[@]}"; do
        echo "  - $o"
    done
    echo ""
    echo "Acoes necessarias:"
    echo "  1. Integrar o modulo em algum fluxo principal, OU"
    echo "  2. Criar teste em src/tests/test_<modulo>.py, OU"
    echo "  3. Remover o modulo se nao for necessario"
    exit 1
fi

echo "OK - Nenhum modulo orfao detectado"
exit 0
