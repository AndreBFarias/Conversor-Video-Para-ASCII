#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SOCKET_PATH="/tmp/luna_tts_daemon.sock"
PID_FILE="/tmp/luna_tts_daemon.pid"

get_active_entity() {
    local profile="$PROJECT_ROOT/src/data_memory/user/profile.json"
    if [ -f "$profile" ]; then
        python3 -c "import json; print(json.load(open('$profile')).get('entity_id', 'luna'))" 2>/dev/null || echo "luna"
    else
        echo "luna"
    fi
}

get_tts_engine() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        grep -E "^TTS_ENGINE=" "$PROJECT_ROOT/.env" | cut -d= -f2 | tr -d '"' | tr -d "'" | tr '[:upper:]' '[:lower:]' || echo "chatterbox"
    else
        echo "chatterbox"
    fi
}

get_reference_audio() {
    local entity="$1"
    local engine="$2"
    local ref_path="$PROJECT_ROOT/src/assets/panteao/entities/$entity/voice/$engine/reference.wav"
    local ref_gz="$ref_path.gz"

    if [ -f "$ref_path" ]; then
        echo "$ref_path"
    elif [ -f "$ref_gz" ]; then
        echo "$ref_gz"
    else
        local luna_ref="$PROJECT_ROOT/src/assets/panteao/entities/luna/voice/$engine/reference.wav"
        if [ -f "$luna_ref" ]; then
            echo "$luna_ref"
        elif [ -f "$luna_ref.gz" ]; then
            echo "$luna_ref.gz"
        else
            echo ""
        fi
    fi
}

status() {
    if [ -S "$SOCKET_PATH" ] && [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}[OK]${NC} TTS Daemon rodando (PID: $pid)"
            return 0
        fi
    fi
    echo -e "${YELLOW}[OFF]${NC} TTS Daemon nao esta rodando"
    return 1
}

start() {
    if status > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARN]${NC} Daemon ja esta rodando"
        return 0
    fi

    local entity=$(get_active_entity)
    local engine=$(get_tts_engine)
    local reference=$(get_reference_audio "$entity" "$engine")

    if [ -z "$reference" ]; then
        echo -e "${RED}[ERRO]${NC} Reference audio nao encontrado para $entity/$engine"
        return 1
    fi

    if [ ! -d "$PROJECT_ROOT/venv_tts" ]; then
        echo -e "${RED}[ERRO]${NC} venv_tts nao encontrado"
        return 1
    fi

    echo -e "${YELLOW}[INFO]${NC} Iniciando TTS Daemon..."
    echo "  Engine: $engine"
    echo "  Entidade: $entity"
    echo "  Reference: $(basename "$reference")"

    cd "$PROJECT_ROOT"
    nohup "$PROJECT_ROOT/venv_tts/bin/python" -m src.tools.tts_daemon start \
        --engine "$engine" \
        --reference "$reference" \
        > /tmp/luna_tts_daemon.log 2>&1 &

    echo "  Aguardando modelo carregar (pode levar 30-60s)..."

    for i in {1..90}; do
        sleep 1
        if [ -S "$SOCKET_PATH" ]; then
            echo -e "${GREEN}[OK]${NC} TTS Daemon iniciado com sucesso"
            return 0
        fi

        if ! pgrep -f "tts_daemon start" > /dev/null 2>&1; then
            echo -e "${RED}[ERRO]${NC} Daemon falhou ao iniciar"
            tail -3 /tmp/luna_tts_daemon.log 2>/dev/null
            return 1
        fi
    done

    echo -e "${RED}[ERRO]${NC} Timeout ao iniciar daemon"
    echo "Verifique: cat /tmp/luna_tts_daemon.log"
    return 1
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}[INFO]${NC} Daemon nao esta rodando"
        return 0
    fi

    local pid=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}[INFO]${NC} Parando TTS Daemon (PID: $pid)..."
        kill "$pid" 2>/dev/null

        for i in {1..10}; do
            sleep 0.5
            if ! kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}[OK]${NC} Daemon parado"
                rm -f "$PID_FILE" "$SOCKET_PATH"
                return 0
            fi
        done

        kill -9 "$pid" 2>/dev/null
        rm -f "$PID_FILE" "$SOCKET_PATH"
        echo -e "${GREEN}[OK]${NC} Daemon forcado a parar"
    fi
    return 0
}

restart() {
    stop
    sleep 1
    start
}

logs() {
    if [ -f "/tmp/luna_tts_daemon.log" ]; then
        tail -f /tmp/luna_tts_daemon.log
    else
        echo "Log nao encontrado"
    fi
}

case "${1:-status}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    ensure)
        if ! status > /dev/null 2>&1; then
            start
        fi
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|ensure}"
        echo ""
        echo "  start   - Inicia o daemon TTS"
        echo "  stop    - Para o daemon TTS"
        echo "  restart - Reinicia o daemon TTS"
        echo "  status  - Verifica se o daemon esta rodando"
        echo "  logs    - Mostra logs em tempo real"
        echo "  ensure  - Inicia o daemon se nao estiver rodando"
        exit 1
        ;;
esac
