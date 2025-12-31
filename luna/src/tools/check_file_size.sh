#!/bin/bash
# src/tools/check_file_size.sh
# Verifica se arquivos Python novos excedem 300 linhas (God Mode Prevention)
# Arquivos legados sao listados em src/tools/legacy_files.txt

MAX_LINES=300
GROWTH_THRESHOLD=30
ERRORS=0
WARNINGS=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_FILE="$SCRIPT_DIR/legacy_files.txt"

load_legacy_files() {
    if [ -f "$LEGACY_FILE" ]; then
        grep -v '^#' "$LEGACY_FILE" | grep -v '^$'
    fi
}

LEGACY_PATHS=$(load_legacy_files | tr '\n' ' ')

is_legacy_file() {
    local file="$1"
    for legacy in $LEGACY_PATHS; do
        if [[ "$file" == "$legacy" ]]; then
            return 0
        fi
    done
    return 1
}

echo "Verificando tamanho dos arquivos Python..."

for file in $(git diff --cached --name-only --diff-filter=AM | grep -E '\.py$'); do
    if [[ ! -f "$file" ]]; then
        continue
    fi

    if [[ "$file" == *"/tests/"* ]] || [[ "$file" == *"test_"* ]] || [[ "$file" == *"conftest.py" ]]; then
        continue
    fi

    if [[ "$file" == *"__init__.py" ]]; then
        continue
    fi

    if [[ "$file" == *"assets/"* ]]; then
        continue
    fi

    lines=$(wc -l < "$file")

    is_new=$(git diff --cached --name-only --diff-filter=A | grep -c "^${file}$")

    if [[ $is_new -gt 0 ]]; then
        # Arquivos novos que estao na lista de legacy sao permitidos
        if is_legacy_file "$file"; then
            if [[ $lines -gt $MAX_LINES ]]; then
                echo "INFO: Novo arquivo legado $file tem $lines linhas (permitido)"
            fi
        elif [[ $lines -gt $MAX_LINES ]]; then
            echo "ERRO: Novo arquivo $file tem $lines linhas (max: $MAX_LINES)"
            echo "  -> Divida o arquivo em modulos menores antes de commitar"
            ERRORS=$((ERRORS + 1))
        fi
    else
        if is_legacy_file "$file"; then
            old_lines=$(git show HEAD:"$file" 2>/dev/null | wc -l || echo "0")
            growth=$((lines - old_lines))
            if [[ $growth -gt $GROWTH_THRESHOLD ]]; then
                echo "AVISO: Arquivo legado $file cresceu $growth linhas"
                echo "  -> Considere refatorar ao inves de adicionar mais codigo"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            if [[ $lines -gt $MAX_LINES ]]; then
                old_lines=$(git show HEAD:"$file" 2>/dev/null | wc -l || echo "0")
                if [[ $old_lines -le $MAX_LINES ]]; then
                    echo "ERRO: $file ultrapassou $MAX_LINES linhas (era $old_lines, agora $lines)"
                    echo "  -> Divida o arquivo em modulos menores"
                    echo "  -> Ou adicione em src/tools/legacy_files.txt se for caso especial"
                    ERRORS=$((ERRORS + 1))
                fi
            fi
        fi
    fi
done

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "God Mode detectado! $ERRORS erro(s)."
    echo "Novos arquivos devem ter no maximo $MAX_LINES linhas."
    exit 1
fi

if [[ $WARNINGS -gt 0 ]]; then
    echo "AVISO: $WARNINGS arquivo(s) legado(s) crescendo - considere refatoracao"
fi

echo "OK: Verificacao de tamanho concluida"
exit 0
