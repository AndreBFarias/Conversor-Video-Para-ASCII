#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${MAGENTA}"
cat << 'EOF'
  ╔════════════════════════════════════════╗
  ║     LUNA - MODO ONBOARDING/DEBUG       ║
  ╚════════════════════════════════════════╝
EOF
echo -e "${NC}"

if [ ! -d "venv" ]; then
    echo -e "${RED}[ERRO]${NC} venv nao encontrado. Execute ./install.sh primeiro."
    exit 1
fi

source venv/bin/activate

PROFILE_PATH="src/data_memory/user/profile.json"
BACKUP_PATH="/tmp/luna_profile_backup_$$.json"

if [ -f "$PROFILE_PATH" ]; then
    cp "$PROFILE_PATH" "$BACKUP_PATH"
    echo -e "${CYAN}[DEBUG]${NC} Profile salvo em: $BACKUP_PATH"
fi

cleanup() {
    echo ""
    echo -e "${YELLOW}[DEBUG]${NC} Restaurando profile..."
    if [ -f "$BACKUP_PATH" ]; then
        cp "$BACKUP_PATH" "$PROFILE_PATH"
        rm "$BACKUP_PATH"
        echo -e "${CYAN}[DEBUG]${NC} Profile restaurado."
    fi
}

trap cleanup EXIT INT TERM

echo -e "${YELLOW}[DEBUG]${NC} Limpando profile para forcar onboarding..."
echo '{"onboarding_completed": false}' > "$PROFILE_PATH"

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export LUNA_DEBUG="1"

echo -e "${CYAN}[DEBUG]${NC} Iniciando Luna em modo onboarding..."
echo ""

python main.py "$@"

EXIT_CODE=$?

echo ""
echo -e "${MAGENTA}[DEBUG]${NC} Sessao de teste finalizada (codigo: $EXIT_CODE)"

exit $EXIT_CODE
