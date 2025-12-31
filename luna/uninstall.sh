#!/bin/bash
# ==============================================
# LUNA - Desinstalacao Completa
# ==============================================
# Remove ambientes, caches, sessoes e dados
# Modelos de IA sao opcionais (pergunta ao user)
# ==============================================

# ----------------------------------------------
# CORES
# ----------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ----------------------------------------------
# FUNCOES
# ----------------------------------------------
print_header() {
    echo ""
    echo -e "${RED}${BOLD}"
    echo "  _    _   _ _   _    _    "
    echo " | |  | | | | \ | |  / \   "
    echo " | |  | | | |  \| | / _ \  "
    echo " | |__| |_| | |\  |/ ___ \ "
    echo " |_____\___/|_| \_/_/   \_\\"
    echo ""
    echo -e "${NC}"
    echo -e "${RED}=============================================="
    echo -e "       LUNA - Protocolo de Limpeza"
    echo -e "==============================================${NC}"
    echo ""
}

print_item() {
    echo -e "    ${CYAN}>${NC} $1"
}

print_success() {
    echo -e "    ${GREEN}OK${NC} $1"
}

print_skip() {
    echo -e "    ${YELLOW}SKIP${NC} $1"
}

print_warning() {
    echo -e "    ${YELLOW}AVISO${NC} $1"
}

get_size() {
    du -sh "$1" 2>/dev/null | cut -f1 || echo "0"
}

# ----------------------------------------------
# NAVEGACAO
# ----------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header

# ----------------------------------------------
# MOSTRAR O QUE SERA REMOVIDO
# ----------------------------------------------
echo -e "${YELLOW}${BOLD}O que sera removido automaticamente:${NC}"
echo ""

[ -d "venv" ] && print_item "venv/ ($(get_size venv))"
[ -d "venv_tts" ] && print_item "venv_tts/ ($(get_size venv_tts))"
print_item "__pycache__/ e *.pyc (cache Python)"
print_item "build/, dist/, *.egg-info/ (artefatos)"
print_item "src/temp/audio/* (arquivos temporarios)"
print_item "logs/*.log (logs de execucao)"
print_item "src/sessions/*.json (historico de conversas)"
print_item "src/data_memory/ (memorias, faces, embeddings)"
print_item "Atalho do menu e icone do sistema"

echo ""
echo -e "${GREEN}${BOLD}O que sera MANTIDO:${NC}"
echo ""
print_item ".env (suas configuracoes API)"
print_item "Codigo fonte completo"
print_item "Modelos de IA (voce escolhe depois)"

echo ""
echo -n -e "${RED}${BOLD}Iniciar limpeza? [s/N]: ${NC}"
read -r REPLY
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operacao cancelada."
    exit 0
fi

TOTAL_STEPS=9

# ==============================================
# FASE 1: Remover VENVs
# ==============================================
echo -e "${CYAN}[1/${TOTAL_STEPS}]${NC} Removendo ambientes virtuais..."

if [ -d "venv" ]; then
    rm -rf venv
    print_success "venv removido"
else
    print_skip "venv nao existe"
fi

if [ -d "venv_tts" ]; then
    rm -rf venv_tts
    print_success "venv_tts removido"
else
    print_skip "venv_tts nao existe"
fi
echo ""

# ==============================================
# FASE 2: Limpar Caches Python
# ==============================================
echo -e "${CYAN}[2/${TOTAL_STEPS}]${NC} Removendo caches Python..."

PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

if [ "$PYCACHE_COUNT" -gt 0 ]; then
    print_success "Removidos $PYCACHE_COUNT diretorios __pycache__"
else
    print_skip "Nenhum cache encontrado"
fi
echo ""

# ==============================================
# FASE 3: Limpar Artefatos de Build
# ==============================================
echo -e "${CYAN}[3/${TOTAL_STEPS}]${NC} Removendo artefatos de build..."

[ -d "build" ] && rm -rf build/ && print_success "build/ removido"
[ -d "dist" ] && rm -rf dist/ && print_success "dist/ removido"
rm -rf *.egg-info/ 2>/dev/null || true
[ -d ".pytest_cache" ] && rm -rf .pytest_cache/ && print_success ".pytest_cache/ removido"
rm -rf .mypy_cache/ .ruff_cache/ .coverage htmlcov/ 2>/dev/null || true

echo ""

# ==============================================
# FASE 4: Limpar Arquivos Temporarios
# ==============================================
echo -e "${CYAN}[4/${TOTAL_STEPS}]${NC} Limpando arquivos temporarios..."

if [ -d "src/temp/audio" ]; then
    TEMP_COUNT=$(find src/temp/audio -type f 2>/dev/null | wc -l)
    rm -rf src/temp/audio/*
    mkdir -p src/temp/audio
    touch src/temp/audio/.gitkeep
    [ "$TEMP_COUNT" -gt 0 ] && print_success "Removidos $TEMP_COUNT arquivos temporarios"
fi

echo ""

# ==============================================
# FASE 5: Limpar Logs
# ==============================================
echo -e "${CYAN}[5/${TOTAL_STEPS}]${NC} Limpando logs..."

rm -rf src/logs/*.log 2>/dev/null || true
rm -rf logs/*.log 2>/dev/null || true
rm -f startup.log 2>/dev/null || true
rm -f *.log 2>/dev/null || true

print_success "Logs removidos"
echo ""

# ==============================================
# FASE 6: Remover Sessoes e Dados
# ==============================================
echo -e "${CYAN}[6/${TOTAL_STEPS}]${NC} Removendo sessoes e dados coletados..."

# Sessoes de chat
if [ -d "src/sessions" ]; then
    SESSION_COUNT=$(find src/sessions -name "*.json" 2>/dev/null | wc -l)
    rm -rf src/sessions/*.json 2>/dev/null || true
    touch src/sessions/.gitkeep
    [ "$SESSION_COUNT" -gt 0 ] && print_success "Removidas $SESSION_COUNT sessoes"
fi

# Memorias e dados de visao
if [ -d "src/data_memory" ]; then
    rm -rf src/data_memory/memories.json 2>/dev/null || true
    rm -rf src/data_memory/events/*.json 2>/dev/null || true
    rm -rf src/data_memory/events/*.jpg 2>/dev/null || true
    rm -rf src/data_memory/events/*.png 2>/dev/null || true
    rm -rf src/data_memory/faces/*.json 2>/dev/null || true
    rm -rf src/data_memory/faces/*.pkl 2>/dev/null || true
    rm -rf src/data_memory/embeddings_cache/ 2>/dev/null || true
    touch src/data_memory/.gitkeep
    touch src/data_memory/events/.gitkeep 2>/dev/null || true
    touch src/data_memory/faces/.gitkeep 2>/dev/null || true
    print_success "Memorias e dados de visao removidos"
fi

# Cache local
rm -rf src/data_memory/cache/ 2>/dev/null || true
rm -rf .cache/ 2>/dev/null || true

echo ""

# ==============================================
# FASE 7: Remover Atalhos do Sistema
# ==============================================
echo -e "${CYAN}[7/${TOTAL_STEPS}]${NC} Removendo atalhos do menu e icone..."

if [ -f "$HOME/.local/share/applications/luna.desktop" ]; then
    rm "$HOME/.local/share/applications/luna.desktop"
    print_success "Atalho do menu removido"
else
    print_skip "Atalho nao encontrado"
fi

if [ -f "$HOME/.local/share/icons/hicolor/256x256/apps/luna.png" ]; then
    rm "$HOME/.local/share/icons/hicolor/256x256/apps/luna.png"
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    print_success "Icone removido"
fi

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""

# ==============================================
# FASE 8: Modelos de IA (OPCIONAL)
# ==============================================
echo -e "${CYAN}[8/${TOTAL_STEPS}]${NC} Modelos de IA..."
echo ""
echo -e "    ${YELLOW}Os modelos ocupam bastante espaco mas demoram para baixar.${NC}"
echo -e "    ${YELLOW}Voce pode mante-los para reinstalacoes mais rapidas.${NC}"
echo ""

# HuggingFace cache (Whisper, sentence-transformers)
if [ -d "$HOME/.cache/huggingface" ]; then
    HF_SIZE=$(get_size "$HOME/.cache/huggingface")
    echo -n "    Remover modelos Whisper e embeddings ($HF_SIZE)? [s/N]: "
    read -r REPLY
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf "$HOME/.cache/huggingface"
        print_success "HuggingFace cache removido ($HF_SIZE liberados)"
    else
        print_skip "Modelos Whisper/embeddings mantidos"
    fi
fi

# Coqui TTS models (voz da Luna - cache global)
if [ -d "$HOME/.local/share/tts" ]; then
    TTS_SIZE=$(get_size "$HOME/.local/share/tts")
    echo -n "    Remover modelos de voz Coqui TTS ($TTS_SIZE)? [s/N]: "
    read -r REPLY
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf "$HOME/.local/share/tts"
        print_success "Modelos de voz removidos ($TTS_SIZE liberados)"
    else
        print_skip "Modelos de voz mantidos"
    fi
fi

# Voice reference files (Luna voice profiles)
if [ -d "src/models/echoes" ]; then
    VOICE_SIZE=$(get_size "src/models/echoes")
    echo -n "    Remover voice profiles Luna (coqui/chatterbox refs) ($VOICE_SIZE)? [s/N]: "
    read -r REPLY
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf src/models/echoes/coqui/*.wav 2>/dev/null || true
        rm -rf src/models/echoes/coqui/*.pt 2>/dev/null || true
        rm -rf src/models/echoes/chatterbox/*.wav 2>/dev/null || true
        print_success "Voice profiles removidos"
    else
        print_skip "Voice profiles mantidos"
    fi
fi

# Modelos Ollama
if command -v ollama &> /dev/null; then
    OLLAMA_MODELS=$(ollama list 2>/dev/null | tail -n +2)
    if [ -n "$OLLAMA_MODELS" ]; then
        echo ""
        echo -e "    ${BLUE}Modelos Ollama instalados:${NC}"
        ollama list 2>/dev/null | tail -n +2 | while read line; do
            echo "      - $line"
        done

        echo ""
        echo -n "    Remover modelos Ollama do Luna? [s/N]: "
        read -r REPLY
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            LUNA_MODELS=("dolphin-mistral" "moondream" "llama3.2:3b" "qwen2.5-coder:7b" "nous-hermes2:mistral" "llava-phi3" "deepseek-coder:6.7b")
            for model in "${LUNA_MODELS[@]}"; do
                if ollama list 2>/dev/null | grep -q "$model"; then
                    ollama rm "$model" 2>/dev/null && print_success "$model removido" || print_warning "Falha ao remover $model"
                fi
            done
        else
            print_skip "Modelos Ollama mantidos"
        fi

        echo -n "    Remover TODOS os modelos Ollama? [s/N]: "
        read -r REPLY
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | while read model; do
                ollama rm "$model" 2>/dev/null && print_success "$model removido" || true
            done
        fi
    fi
fi

echo ""

# ==============================================
# FASE 9: Arquivo .env (OPCIONAL)
# ==============================================
echo -e "${CYAN}[9/${TOTAL_STEPS}]${NC} Configuracoes..."

echo -n "    Remover .env (suas API keys)? [s/N]: "
read -r REPLY
if [[ $REPLY =~ ^[Ss]$ ]]; then
    rm -f .env 2>/dev/null || true
    print_success ".env removido"
else
    print_skip ".env mantido"
fi

echo ""

# ==============================================
# CONCLUSAO
# ==============================================
echo -e "${GREEN}${BOLD}"
echo "=============================================="
echo "       Limpeza Concluida!"
echo "=============================================="
echo -e "${NC}"
echo ""
echo "  O codigo fonte foi mantido intacto."
echo ""
echo "  Para reinstalar Luna:"
echo "    ./install.sh"
echo ""
