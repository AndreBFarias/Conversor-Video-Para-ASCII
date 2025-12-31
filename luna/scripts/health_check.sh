#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local status="$2"
    local msg="$3"

    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}[OK]${NC} $name"
        ((PASS++))
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}[WARN]${NC} $name: $msg"
        ((WARN++))
    else
        echo -e "${RED}[FAIL]${NC} $name: $msg"
        ((FAIL++))
    fi
}

echo ""
echo "================================"
echo "  LUNA HEALTH CHECK"
echo "================================"
echo ""

echo "[1/6] Ambiente Python"
if [ -f "./venv/bin/python" ]; then
    PYTHON_VERSION=$(./venv/bin/python --version 2>&1)
    check "Virtual env" "ok"
    check "Python version" "ok" "$PYTHON_VERSION"
else
    check "Virtual env" "fail" "venv nao encontrado"
fi

echo ""
echo "[2/6] Dependencias Criticas"
if [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
else
    PYTHON="python3"
fi

declare -A PKGS=(
    ["textual"]="textual"
    ["rich"]="rich"
    ["google-generativeai"]="google.generativeai"
    ["ollama"]="ollama"
    ["openai-whisper"]="whisper"
    ["torch"]="torch"
    ["numpy"]="numpy"
)

for name in "${!PKGS[@]}"; do
    import="${PKGS[$name]}"
    if $PYTHON -c "import $import" 2>/dev/null; then
        check "$name" "ok"
    else
        check "$name" "warn" "nao instalado"
    fi
done

echo ""
echo "[3/6] Estrutura de Arquivos"
for f in main.py config.py requirements.txt; do
    if [ -f "$f" ]; then
        check "$f" "ok"
    else
        check "$f" "fail" "arquivo nao encontrado"
    fi
done

for d in src/soul src/core src/ui src/data_memory src/assets; do
    if [ -d "$d" ]; then
        check "$d/" "ok"
    else
        check "$d/" "fail" "diretorio nao encontrado"
    fi
done

echo ""
echo "[4/6] Configuracao de Entidades"
if [ -f "src/assets/panteao/registry.json" ]; then
    check "registry.json" "ok"
else
    check "registry.json" "fail" "registro de entidades nao encontrado"
fi

ENTITY_COUNT=$(ls -1d src/assets/panteao/entities/*/ 2>/dev/null | wc -l)
if [ "$ENTITY_COUNT" -gt 0 ]; then
    check "Entidades instaladas" "ok" "$ENTITY_COUNT entidades"
else
    check "Entidades instaladas" "fail" "nenhuma entidade encontrada"
fi

echo ""
echo "[5/6] Servicos Externos"
if command -v ollama &> /dev/null; then
    if ollama list &>/dev/null; then
        MODEL_COUNT=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
        check "Ollama" "ok" "$MODEL_COUNT modelos"
    else
        check "Ollama" "warn" "instalado mas nao respondendo"
    fi
else
    check "Ollama" "warn" "nao instalado (opcional)"
fi

if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU_NAME" ]; then
        check "GPU NVIDIA" "ok" "$GPU_NAME"
    else
        check "GPU NVIDIA" "warn" "driver instalado mas GPU nao detectada"
    fi
else
    check "GPU NVIDIA" "warn" "nvidia-smi nao encontrado (CPU mode)"
fi

echo ""
echo "[6/6] Imports Criticos"
if $PYTHON -c "from src.soul import Consciencia" 2>/dev/null; then
    check "src.soul.Consciencia" "ok"
else
    check "src.soul.Consciencia" "fail" "erro de import"
fi

if $PYTHON -c "from src.app import TemploDaAlma" 2>/dev/null; then
    check "src.app.TemploDaAlma" "ok"
else
    check "src.app.TemploDaAlma" "fail" "erro de import"
fi

if $PYTHON -c "from src.core.entity_loader import EntityLoader" 2>/dev/null; then
    check "src.core.EntityLoader" "ok"
else
    check "src.core.EntityLoader" "fail" "erro de import"
fi

echo ""
echo "================================"
echo "  RESULTADO"
echo "================================"
echo -e "  ${GREEN}PASS:${NC} $PASS"
echo -e "  ${YELLOW}WARN:${NC} $WARN"
echo -e "  ${RED}FAIL:${NC} $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}Sistema operacional!${NC}"
    exit 0
else
    echo -e "${RED}Problemas detectados. Verifique os itens FAIL acima.${NC}"
    exit 1
fi
