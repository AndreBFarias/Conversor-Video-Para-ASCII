#!/bin/bash
# validate_docs.sh - Valida que documentos de guia referenciam arquivos existentes
# Uso: ./scripts/validate_docs.sh [--fix]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

ERRORS=0
WARNINGS=0
FIX_MODE=false

if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "=== Validando Documentos de Guia ==="
echo ""

# Cores
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Funcao para verificar arquivo Python mencionado
check_py_reference() {
    local doc_file="$1"
    local line_num=0
    local in_pending_section=false

    while IFS= read -r line; do
        line_num=$((line_num + 1))

        # Detectar secoes de pendente/nao implementado
        if [[ "$line" =~ "PENDENTE" ]] || [[ "$line" =~ "NAO IMPLEMENTADO" ]] || \
           [[ "$line" =~ "esperado:" ]] || [[ "$line" =~ "sugerido" ]]; then
            in_pending_section=true
        fi

        # Reset ao encontrar nova secao
        if [[ "$line" =~ ^"## " ]] || [[ "$line" =~ ^"### " ]]; then
            in_pending_section=false
        fi

        # Buscar padroes src/*.py
        if [[ "$line" =~ (src/[a-zA-Z0-9_/]+\.py) ]]; then
            file="${BASH_REMATCH[1]}"

            # Ignorar se estiver em bloco de codigo como exemplo
            if [[ "$line" =~ "touch " ]] || [[ "$line" =~ "# " ]] || \
               [[ "$line" =~ "pytest " ]] || [[ "$line" =~ "python -c" ]] || \
               [[ "$line" =~ "python -m" ]] || [[ "$line" =~ "from " ]]; then
                continue
            fi

            # Ignorar arquivos em secoes de pendente (documentados como nao existentes)
            if $in_pending_section; then
                continue
            fi

            if [ ! -f "$file" ]; then
                echo -e "${RED}[ERRO]${NC} $doc_file:$line_num"
                echo "       Arquivo nao existe: $file"
                ERRORS=$((ERRORS + 1))
            fi
        fi

        # Buscar padroes dev-journey/*.md
        if [[ "$line" =~ (dev-journey/[a-zA-Z0-9_/-]+\.md) ]]; then
            file="${BASH_REMATCH[1]}"
            if [ ! -f "$file" ]; then
                echo -e "${YELLOW}[WARN]${NC} $doc_file:$line_num"
                echo "       Doc nao existe: $file"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi

    done < "$doc_file"
}

# Verificar documentos principais
DOCS_TO_CHECK=(
    "LUNA_GUIA_AUTONOMO.md"
    "LUNA_AUDITORIA_E_CORRECOES.md"
    "CLAUDE.md"
)

for doc in "${DOCS_TO_CHECK[@]}"; do
    if [ -f "$doc" ]; then
        echo "Verificando $doc..."
        check_py_reference "$doc"
    else
        echo -e "${YELLOW}[WARN]${NC} $doc nao encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "=== Verificando Estrutura de Entidades ==="

# Verificar que todas as entidades tem arquivos obrigatorios
ENTITIES_DIR="src/assets/panteao/entities"
REQUIRED_FILES=("config.json" "alma.txt")

for entity_dir in "$ENTITIES_DIR"/*/; do
    entity_name=$(basename "$entity_dir")

    for req_file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "${entity_dir}${req_file}" ]; then
            echo -e "${RED}[ERRO]${NC} Entidade $entity_name falta: $req_file"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Verificar CSS
    css_file="${entity_dir}templo_de_${entity_name}.css"
    if [ ! -f "$css_file" ]; then
        echo -e "${YELLOW}[WARN]${NC} Entidade $entity_name falta CSS"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "=== Verificando dev-journey/ ==="

# Verificar que documentos criticos existem
CRITICAL_DOCS=(
    "dev-journey/04-implementation/CURRENT_STATUS.md"
    "dev-journey/05-future/TECHNICAL_DEBT.md"
    "dev-journey/04-implementation/DEPENDENCY_MAP.md"
)

for doc in "${CRITICAL_DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        echo -e "${RED}[ERRO]${NC} Documento critico falta: $doc"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}[OK]${NC} $doc"
    fi
done

echo ""
echo "=== Resumo ==="
echo -e "Erros:   ${RED}$ERRORS${NC}"
echo -e "Avisos:  ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}Documentacao desatualizada. Corrigir antes de commit.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}Documentacao OK${NC}"
    exit 0
fi
