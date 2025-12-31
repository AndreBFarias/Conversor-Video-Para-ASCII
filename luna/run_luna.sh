#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m'

if [ ! -d "venv" ]; then
    echo -e "${RED}[ERRO]${NC} venv nao encontrado. Execute ./install.sh primeiro."
    exit 1
fi

source venv/bin/activate

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

EXTRA_ARGS=""
NO_DAEMON=false
for arg in "$@"; do
    case "$arg" in
        --voice)
            export LUNA_START_MODE="voice"
            ;;
        --text)
            export LUNA_START_MODE="text"
            ;;
        --debug)
            export LUNA_DEBUG="1"
            ;;
        --gpu)
            EXTRA_ARGS="$EXTRA_ARGS --gpu"
            ;;
        --no-daemon)
            NO_DAEMON=true
            ;;
        --launch)
            ;;
    esac
done

if [ "$NO_DAEMON" = false ] && [ -d "venv_tts" ] && [ -f "scripts/tts_daemon.sh" ]; then
    echo -e "${MAGENTA}[TTS]${NC} Verificando daemon..."
    ./scripts/tts_daemon.sh ensure 2>/dev/null
fi

echo -e "${MAGENTA}"
cat << 'EOF'
  ╔════════════════════════════════════════╗
  ║                                        ║
  ║     ██╗     ██╗   ██╗███╗   ██╗ █████╗ ║
  ║     ██║     ██║   ██║████╗  ██║██╔══██╗║
  ║     ██║     ██║   ██║██╔██╗ ██║███████║║
  ║     ██║     ██║   ██║██║╚██╗██║██╔══██║║
  ║     ███████╗╚██████╔╝██║ ╚████║██║  ██║║
  ║     ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝║
  ║                                        ║
  ║        T E M P L O   D A   A L M A     ║
  ╚════════════════════════════════════════╝
EOF
echo -e "${NC}"

python main.py $EXTRA_ARGS

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}[Luna]${NC} Sessao encerrada com codigo: $EXIT_CODE"
fi

exit $EXIT_CODE
