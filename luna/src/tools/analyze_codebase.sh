#!/bin/bash
# src/tools/analyze_codebase.sh
# Analisa codebase e cria issues para problemas encontrados
# Uso: ./src/tools/analyze_codebase.sh [--dry-run]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ANALISE AUTOMATICA DO CODEBASE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

DRY_RUN="false"
if [ "$1" == "--dry-run" ]; then
    DRY_RUN="true"
    echo -e "${YELLOW}[MODO DRY-RUN] Nenhuma issue sera criada${NC}"
    echo ""
fi

ISSUES_CREATED=0

echo -e "${YELLOW}[1/4]${NC} Verificando TODOs sem labels..."

grep -rn "# TODO:" src/ --include="*.py" 2>/dev/null | while read line; do
    FILE=$(echo "$line" | cut -d: -f1)
    LINE_NUM=$(echo "$line" | cut -d: -f2)
    CONTENT=$(echo "$line" | cut -d: -f3- | sed 's/.*# TODO://' | xargs)

    NEXT_LINE=$(sed -n "$((LINE_NUM + 1))p" "$FILE" 2>/dev/null || echo "")
    if echo "$NEXT_LINE" | grep -q "# labels:"; then
        continue
    fi

    echo -e "  ${YELLOW}!${NC} TODO sem labels: $FILE:$LINE_NUM"
    echo "    $CONTENT"

    if [ "$DRY_RUN" == "false" ]; then
        EXISTING=$(gh issue list --search "$CONTENT" --json number --jq 'length' 2>/dev/null || echo "0")

        if [ "$EXISTING" -eq 0 ]; then
            gh issue create \
                --title "[TODO] $CONTENT" \
                --body "## Origem
Encontrado em \`$FILE:$LINE_NUM\`

## Acao
Implementar ou adicionar labels ao TODO.

---
*Issue criada por analyze_codebase.sh*" \
                --label "type:feature,status:ready,ai-task" \
                > /dev/null 2>&1 && echo -e "    ${GREEN}Issue criada${NC}"
        fi
    fi
done

echo ""
echo -e "${YELLOW}[2/4]${NC} Verificando arquivos grandes (>500 linhas)..."

find src/ -name "*.py" -exec wc -l {} \; 2>/dev/null | sort -rn | while read count file; do
    if [ "$count" -gt 500 ]; then
        echo -e "  ${RED}!${NC} $file: $count linhas"

        if [ "$DRY_RUN" == "false" ]; then
            FILENAME=$(basename "$file")
            EXISTING=$(gh issue list --search "Refatorar $FILENAME" --json number --jq 'length' 2>/dev/null || echo "0")

            if [ "$EXISTING" -eq 0 ]; then
                gh issue create \
                    --title "[DEBT] Refatorar $FILENAME ($count linhas)" \
                    --body "## Problema
\`$file\` tem $count linhas (limite: 500).

## Sugestao
Extrair para modulos menores.

---
*Issue criada por analyze_codebase.sh*" \
                    --label "type:refactor,P2-medium,status:ready" \
                    > /dev/null 2>&1 && echo -e "    ${GREEN}Issue criada${NC}"
            fi
        fi
    fi
done

echo ""
echo -e "${YELLOW}[3/4]${NC} Verificando modulos sem testes..."

for module in src/soul src/core src/data_memory; do
    if [ -d "$module" ]; then
        for file in "$module"/*.py; do
            [ -f "$file" ] || continue

            BASENAME=$(basename "$file" .py)

            if [[ "$BASENAME" == "__init__" ]] || [[ "$BASENAME" == *"test"* ]]; then
                continue
            fi

            TEST_FILE="src/tests/test_$BASENAME.py"

            if [ ! -f "$TEST_FILE" ]; then
                echo -e "  ${YELLOW}!${NC} Sem teste: $file"
            fi
        done
    fi
done

echo ""
echo -e "${YELLOW}[4/4]${NC} Verificando FIXMEs..."

FIXMES=$(grep -rn "# FIXME:" src/ --include="*.py" 2>/dev/null || true)
if [ -n "$FIXMES" ]; then
    echo "$FIXMES" | while read line; do
        echo -e "  ${RED}!${NC} $line"
    done
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Analise completa!${NC}"
echo ""
echo "Comandos uteis:"
echo "  gh issue list                    # Ver issues"
echo "  gh issue list --label ai-task    # Issues para IA"
