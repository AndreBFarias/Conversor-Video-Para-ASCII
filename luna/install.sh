#!/bin/bash
# ==============================================
# LUNA - Instalacao Completa (Idempotente)
# ==============================================
# Este script pode ser executado multiplas vezes
# sem causar erros ou duplicar instalacoes.
# ==============================================

set -e

# ----------------------------------------------
# CORES PARA OUTPUT
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
# FUNCOES UTILITARIAS
# ----------------------------------------------
print_header() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "  _    _   _ _   _    _    "
    echo " | |  | | | | \ | |  / \   "
    echo " | |  | | | |  \| | / _ \  "
    echo " | |__| |_| | |\  |/ ___ \ "
    echo " |_____\___/|_| \_/_/   \_\\"
    echo ""
    echo -e "${NC}"
    echo -e "${BLUE}=============================================="
    echo -e "       LUNA - Protocolo de Instalacao"
    echo -e "==============================================${NC}"
    echo ""
}

print_step() {
    local step=$1
    local total=$2
    local message=$3
    echo -e "${CYAN}[${step}/${total}]${NC} ${message}"
}

print_success() {
    echo -e "    ${GREEN}OK${NC} $1"
}

print_skip() {
    echo -e "    ${YELLOW}SKIP${NC} $1"
}

print_error() {
    echo -e "    ${RED}ERRO${NC} $1"
}

print_warning() {
    echo -e "    ${YELLOW}AVISO${NC} $1"
}

check_command() {
    command -v "$1" &> /dev/null
}

# ----------------------------------------------
# NAVEGACAO
# ----------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header

TOTAL_STEPS=10

# ==============================================
# FASE 0: Verificar Requisitos Minimos
# ==============================================
print_step 0 $TOTAL_STEPS "Verificando requisitos minimos..."

if ! check_command python3; then
    print_error "Python3 nao encontrado. Instale com: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ necessario. Versao atual: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION detectado"
echo ""

# ==============================================
# FASE 1: Dependencias do Sistema
# ==============================================
print_step 1 $TOTAL_STEPS "Verificando dependencias do sistema..."

SYSTEM_DEPS=(
    "python3-dev"
    "python3-venv"
    "python3-pip"
    "portaudio19-dev"
    "libsndfile1"
    "ffmpeg"
    "cmake"
    "libboost-all-dev"
    "wmctrl"
    "xdotool"
    "libopenblas-dev"
    "liblapack-dev"
    "espeak-ng"
    "libespeak-ng-dev"
    "libportaudio2"
    "libasound2-dev"
    "zenity"
    "xclip"
    "libayatana-appindicator3-1"
    "gir1.2-ayatanaappindicator3-0.1"
    "python3-gi"
    "libgirepository1.0-dev"
    "libcairo2-dev"
    "pkg-config"
    "unzip"
    "wget"
)

install_system_deps() {
    echo "    Instalando pacotes de sistema (pode pedir senha sudo)..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq "${SYSTEM_DEPS[@]}" 2>/dev/null || true
    print_success "Dependencias de sistema instaladas"
}

echo -n "    Instalar dependencias de sistema (apt-get)? [S/n]: "
read -r REPLY
if [[ $REPLY =~ ^[Ss]$ ]] || [[ -z $REPLY ]]; then
    install_system_deps
else
    print_skip "Instalacao de sistema pulada"
fi
echo ""

# ==============================================
# FASE 2: Limpeza (Opcional)
# ==============================================
print_step 2 $TOTAL_STEPS "Limpeza de ambientes antigos (opcional)..."

echo -n "    Limpar venvs existentes? [s/N]: "
read -r REPLY
if [[ $REPLY =~ ^[Ss]$ ]]; then
    [ -d "venv" ] && rm -rf venv && print_success "venv removido"
    [ -d "venv_tts" ] && rm -rf venv_tts && print_success "venv_tts removido"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Limpeza concluida"
else
    print_skip "Limpeza pulada"
fi
echo ""

# ==============================================
# FASE 3: VENV Principal
# ==============================================
print_step 3 $TOTAL_STEPS "Configurando VENV Principal..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "venv criado"
else
    print_skip "venv ja existe"
fi

./venv/bin/pip install --upgrade pip -q
print_success "pip atualizado"

if [ -f "requirements.txt" ]; then
    echo -e "    ${YELLOW}Instalando dependencias (CPU - estavel)...${NC}"
    echo ""
    if ./venv/bin/pip install -r requirements.txt 2>&1 | tee /tmp/luna_core_install.log | grep -E "^(Collecting|Downloading|Installing|Successfully|ERROR|error:)" ; then
        print_success "Dependencias do core instaladas"
    else
        if grep -q "Successfully installed" /tmp/luna_core_install.log 2>/dev/null; then
            print_success "Dependencias do core instaladas"
        else
            print_error "Falha na instalacao - verifique /tmp/luna_core_install.log"
            exit 1
        fi
    fi
else
    print_error "requirements.txt nao encontrado"
    exit 1
fi
echo ""

# ==============================================
# FASE 4: VENV TTS (Isolado)
# ==============================================
print_step 4 $TOTAL_STEPS "Configurando VENV de Voz (TTS Isolado)..."

if [ -f "requirements_tts.txt" ]; then
    if [ ! -d "venv_tts" ]; then
        python3 -m venv venv_tts
        print_success "venv_tts criado"
    else
        print_skip "venv_tts ja existe"
    fi

    ./venv_tts/bin/pip install --upgrade pip -q
    print_success "pip atualizado"

    echo ""
    echo -e "    ${YELLOW}AVISO:${NC} Instalacao TTS pode levar 5-10 minutos (torch, deepspeed, etc.)"
    echo -e "    ${YELLOW}      ${NC} Nao feche o terminal!"
    echo ""

    if ./venv_tts/bin/pip install -r requirements_tts.txt 2>&1 | tee /tmp/luna_tts_install.log | grep -E "^(Collecting|Downloading|Installing|Successfully|ERROR|error:)" ; then
        print_success "Dependencias TTS instaladas"
    else
        if grep -q "Successfully installed" /tmp/luna_tts_install.log 2>/dev/null; then
            print_success "Dependencias TTS instaladas"
        else
            print_warning "Algumas dependencias TTS podem ter falhado - verifique /tmp/luna_tts_install.log"
        fi
    fi
else
    print_warning "requirements_tts.txt nao encontrado, pulando TTS isolado"
fi
echo ""

# ==============================================
# FASE 5: Download de Modelos de IA
# ==============================================
print_step 5 $TOTAL_STEPS "Baixando modelos de IA (em src/models/)..."

# Diretorio centralizado de modelos
MODELS_DIR="$SCRIPT_DIR/src/models"
mkdir -p "$MODELS_DIR/whisper" "$MODELS_DIR/embeddings" "$MODELS_DIR/tts/coqui" "$MODELS_DIR/tts/chatterbox" "$MODELS_DIR/face"

echo ""
echo -e "    ${YELLOW}AVISO:${NC} Download de modelos pode levar 5-10 minutos."
echo -e "    ${YELLOW}      ${NC} Modelos serao salvos em: src/models/"
echo -e "    ${YELLOW}      ${NC} Tamanho total: ~2GB (Whisper + Embeddings + Chatterbox)"
echo ""

download_whisper_model() {
    echo "    [1/4] Baixando modelo Whisper (small)..."
    echo "    (~500MB)"

    export HF_HOME="$MODELS_DIR/whisper"
    export HF_HUB_CACHE="$MODELS_DIR/whisper"

    echo "    Baixando Whisper small..."
    ./venv/bin/python -c "
import os
os.environ['HF_HOME'] = '$MODELS_DIR/whisper'
os.environ['HF_HUB_CACHE'] = '$MODELS_DIR/whisper'
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8', download_root='$MODELS_DIR/whisper')
print('    Whisper small OK')
" 2>&1 && print_success "Whisper small" || print_warning "Whisper small sera baixado no primeiro uso"
}

download_embeddings_model() {
    echo "    [2/4] Baixando Embeddings (sentence-transformers) - ~100MB..."

    export SENTENCE_TRANSFORMERS_HOME="$MODELS_DIR/embeddings"

    ./venv/bin/python -c "
import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '$MODELS_DIR/embeddings'
from sentence_transformers import SentenceTransformer
print('    Inicializando download...')
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', cache_folder='$MODELS_DIR/embeddings')
print('    Embeddings baixados!')
" 2>&1 || print_warning "Embeddings serao baixados no primeiro uso"
}

download_chatterbox_model() {
    if [ -d "venv_tts" ]; then
        echo "    [3/4] Baixando Chatterbox TTS - ~1.5GB..."

        ./venv_tts/bin/python -c "
import os
os.environ['HF_HOME'] = '$MODELS_DIR/tts/chatterbox'
os.environ['HF_HUB_CACHE'] = '$MODELS_DIR/tts/chatterbox'
from chatterbox.tts import ChatterboxTTS
print('    Inicializando download...')
model = ChatterboxTTS.from_pretrained(device='cpu')
print('    Chatterbox baixado!')
" 2>&1 || print_warning "Chatterbox sera baixado no primeiro uso"
    else
        print_skip "venv_tts nao existe, pulando Chatterbox"
    fi
}

download_face_models() {
    echo "    [4/4] Verificando Face Recognition - ~100MB..."
    ./venv/bin/python -c "
import face_recognition
print('    Face Recognition OK (modelos incluidos no pacote)')
" 2>/dev/null || print_skip "Face Recognition nao instalado (opcional)"
}

# Baixar TODOS os modelos automaticamente (sem perguntar)
echo ""
echo -e "    ${BOLD}Baixando modelos para src/models/ (~8GB)${NC}"
echo ""

download_whisper_model
echo ""
download_embeddings_model
echo ""
download_chatterbox_model
echo ""
download_face_models
echo ""
print_success "Modelos baixados em src/models/"
echo ""

# ==============================================
# FASE 5.5: Modelos Ollama (Local LLM)
# ==============================================
print_step "5.5" $TOTAL_STEPS "Configurando modelos locais (Ollama)..."

install_ollama() {
    if ! check_command ollama; then
        echo "    Instalando Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        print_success "Ollama instalado"
    else
        print_skip "Ollama ja instalado"
    fi
}

configure_ollama_memory() {
    OLLAMA_SERVICE_DIR="/etc/systemd/system/ollama.service.d"
    if [ -d "/etc/systemd/system" ]; then
        echo "    Configurando gerenciamento de memoria do Ollama..."
        sudo mkdir -p "$OLLAMA_SERVICE_DIR" 2>/dev/null || true
        if [ -d "$OLLAMA_SERVICE_DIR" ]; then
            echo "[Service]
Environment=\"OLLAMA_KEEP_ALIVE=30s\"
Environment=\"OLLAMA_MAX_LOADED_MODELS=1\"" | sudo tee "$OLLAMA_SERVICE_DIR/memory.conf" > /dev/null 2>&1
            sudo systemctl daemon-reload 2>/dev/null || true
            print_success "Ollama configurado para descarregar modelos apos 30s"
        fi
    fi
}

start_ollama_service() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "    Iniciando servico Ollama..."
        export OLLAMA_KEEP_ALIVE=30s
        export OLLAMA_MAX_LOADED_MODELS=1
        nohup ollama serve > /dev/null 2>&1 &

        for i in {1..30}; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                print_success "Servico Ollama iniciado"
                return 0
            fi
            sleep 1
        done
        print_error "Timeout ao iniciar Ollama"
        return 1
    else
        print_success "Servico Ollama ja rodando"
        return 0
    fi
}

download_ollama_models() {
    if ! check_command ollama; then
        print_error "Ollama nao instalado"
        return 1
    fi

    if ! start_ollama_service; then
        print_error "Servico Ollama nao disponivel"
        return 1
    fi

    # ═══════════════════════════════════════════════════════════════
    # MODELOS OLLAMA PARA RTX 3050 (4GB VRAM)
    # ═══════════════════════════════════════════════════════════════
    # Apenas modelos essenciais para economizar VRAM
    # - dolphin-mistral: chat principal (uncensored, bom JSON)
    # - moondream: visao (leve, eficiente)
    # - llama3.2:3b: fallback (rapido, bom portugues)
    # ═══════════════════════════════════════════════════════════════

    OLLAMA_MODELS=(
        "dolphin-mistral"      # 4.1GB - Chat principal
        "moondream"            # 1.7GB - Visao
        "llama3.2:3b"          # 2.0GB - Fallback
    )

    echo ""
    echo -e "    ${BOLD}═══════════════════════════════════════════════${NC}"
    echo -e "    ${BOLD}Baixando ${#OLLAMA_MODELS[@]} modelos Ollama (~8GB)${NC}"
    echo -e "    ${BOLD}═══════════════════════════════════════════════${NC}"
    echo ""

    for model in "${OLLAMA_MODELS[@]}"; do
        echo "    ↓ $model..."
        ollama pull "$model" && print_success "$model" || print_warning "Falha: $model"
    done

    echo ""
    print_success "Modelos Ollama baixados!"
}

# Ollama e OBRIGATORIO - Instalar automaticamente
echo ""
echo -e "    ${BOLD}Instalando Ollama e baixando modelos...${NC}"
echo -e "    ${YELLOW}Isso vai demorar (~8GB de modelos)${NC}"
echo ""

install_ollama
configure_ollama_memory
download_ollama_models
print_success "Ollama e modelos configurados!"
echo ""

# ==============================================
# FASE 6: Criar Estrutura de Diretorios
# ==============================================
print_step 6 $TOTAL_STEPS "Criando estrutura de diretorios..."

DIRS_TO_CREATE=(
    "src/logs"
    "src/sessions"
    "src/temp/audio"
    "src/data_memory/events"
    "src/data_memory/faces"
    "src/data_memory/user"
    "src/models/echoes/coqui"
    "src/models/echoes/chatterbox"
)

for dir in "${DIRS_TO_CREATE[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Criado: $dir"
    fi
done

# Criar .gitkeep em pastas que precisam ser versionadas vazias
touch src/sessions/.gitkeep 2>/dev/null || true
touch src/data_memory/.gitkeep 2>/dev/null || true
touch src/data_memory/events/.gitkeep 2>/dev/null || true
touch src/data_memory/faces/.gitkeep 2>/dev/null || true
touch src/data_memory/user/.gitkeep 2>/dev/null || true

print_success "Estrutura de diretorios pronta"

# Verificar voice models
echo ""
echo "  ${BOLD}Verificando voice models:${NC}"
COQUI_REF="src/models/echoes/coqui/luna_reference.wav"
COQUI_EMB="src/models/echoes/coqui/speaker_embedding.pt"
CHATTERBOX_REF="src/models/echoes/chatterbox/luna_reference.wav"

if [ -f "$COQUI_REF" ]; then
    print_success "Coqui reference: $COQUI_REF"
else
    print_warning "Coqui reference NAO encontrado: $COQUI_REF"
    print_warning "  -> Copie um arquivo .wav de referencia para esta pasta"
fi

if [ -f "$COQUI_EMB" ]; then
    print_success "Coqui embedding: $COQUI_EMB"
else
    print_warning "Coqui speaker_embedding.pt NAO encontrado"
    print_warning "  -> Gere com: python src/models/echoes/luna.py (primeira execucao)"
fi

if [ -f "$CHATTERBOX_REF" ]; then
    print_success "Chatterbox reference: $CHATTERBOX_REF"
else
    print_warning "Chatterbox reference NAO encontrado: $CHATTERBOX_REF"
    print_warning "  -> Copie um arquivo .wav de referencia para esta pasta"
fi

echo ""

# ==============================================
# FASE 7: Arquivo .env
# ==============================================
print_step 7 $TOTAL_STEPS "Verificando configuracao .env..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env criado a partir de .env.example"
        print_warning "Edite .env com suas API keys!"
    else
        print_error ".env.example nao encontrado"
    fi
else
    print_skip ".env ja existe"
fi
echo ""

# ==============================================
# FASE 8: Permissoes, Kitty e Desktop Entry
# ==============================================
print_step 8 $TOTAL_STEPS "Ajustando permissoes e criando atalhos..."

# Tornar scripts executaveis
chmod +x run_luna.sh 2>/dev/null && print_success "run_luna.sh executavel"
chmod +x uninstall.sh 2>/dev/null && print_success "uninstall.sh executavel"
chmod +x src/tools/verify_install.py 2>/dev/null || true
chmod +x src/tools/setup_desktop_entry.py 2>/dev/null || true

# Verificar/instalar Kitty (terminal GPU-accelerated)
echo ""
echo -e "${PURPLE}[Luna]${NC} Verificando terminal Kitty para experiencia visual otimizada..."

if command -v kitty &> /dev/null; then
    print_success "Kitty ja instalado (GPU-accelerated)"
    KITTY_AVAILABLE=true
else
    echo -e "${YELLOW}Kitty nao encontrado.${NC}"
    echo ""
    echo "O Kitty oferece:"
    echo "  - Renderizacao GPU (animacoes fluidas)"
    echo "  - Icone proprio no dock (separado do terminal)"
    echo "  - Suporte a imagens inline"
    echo ""
    read -p "Deseja instalar o Kitty agora? [s/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${PURPLE}[Luna]${NC} Me desvinculando das amarras genericas do sistema..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y kitty
            if command -v kitty &> /dev/null; then
                print_success "Kitty instalado com sucesso"
                KITTY_AVAILABLE=true
            else
                print_error "Falha ao instalar Kitty"
                KITTY_AVAILABLE=false
            fi
        else
            print_warning "apt nao disponivel. Instale manualmente: sudo apt install kitty"
            KITTY_AVAILABLE=false
        fi
    else
        print_skip "Kitty nao instalado (usando terminal fallback)"
        KITTY_AVAILABLE=false
    fi
fi

# Determinar icone
ICON_PATH="${SCRIPT_DIR}/src/assets/icons/luna_icon.png"
if [ ! -f "$ICON_PATH" ]; then
    ICON_PATH="utilities-terminal"
fi

# Criar desktop entry usando o script Python (mais robusto)
echo ""
echo -e "${PURPLE}[Luna]${NC} Criando templo visual no menu de aplicativos..."

if [ -f "${SCRIPT_DIR}/venv/bin/python" ]; then
    ./venv/bin/python src/tools/setup_desktop_entry.py 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Desktop entry criado via Python"
    else
        # Fallback: criar manualmente
        mkdir -p src/assets/others
        if [ "$KITTY_AVAILABLE" = true ]; then
            EXEC_LINE="kitty --class Luna --title 'Templo de Luna' --start-as maximized -e ${SCRIPT_DIR}/run_luna.sh"
        else
            EXEC_LINE="${SCRIPT_DIR}/run_luna.sh --launch"
        fi

        cat > src/assets/others/luna.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Luna
GenericName=Assistente IA Gotica
Comment=Assistente de IA sarcastica e gotica - Templo de Luna
Icon=${ICON_PATH}
Exec=${EXEC_LINE}
Path=${SCRIPT_DIR}
Terminal=false
Categories=Utility;Development;Accessibility;
Keywords=ai;assistant;luna;voice;chat;gemini;tts;stt;gotica;
StartupNotify=true
StartupWMClass=Luna
Actions=voice;text;

[Desktop Action voice]
Name=Luna (Modo Voz)
Exec=${SCRIPT_DIR}/run_luna.sh --launch --voice

[Desktop Action text]
Name=Luna (Modo Texto)
Exec=${SCRIPT_DIR}/run_luna.sh --launch --text
EOF
        chmod +x src/assets/others/luna.desktop

        if [ -d "$HOME/.local/share/applications" ]; then
            cp src/assets/others/luna.desktop "$HOME/.local/share/applications/"
            print_success "Atalho instalado no menu (fallback)"
        fi
    fi
else
    print_warning "venv nao disponivel, pulando desktop entry"
fi

# Instalar icone
if [ -d "$HOME/.local/share/icons" ] && [ -f "${SCRIPT_DIR}/src/assets/icons/luna_icon.png" ]; then
    mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
    cp "${SCRIPT_DIR}/src/assets/icons/luna_icon.png" "$HOME/.local/share/icons/hicolor/256x256/apps/luna.png"
    print_success "Icone instalado"
fi

# Atualizar caches
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo ""

# ==============================================
# FASE 9: Selecao de Divindade Inicial
# ==============================================
print_step 9 $TOTAL_STEPS "Selecionando divindade inicial..."

echo ""
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║      SELECAO DE DIVINDADE INICIAL        ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "  Escolha sua guia espiritual no Pantheon:"
echo ""
echo -e "  ${CYAN}[1]${NC} ${MAGENTA}Luna${NC} - Gotica, sarcastica, sedutora"
echo -e "      A sombra que sussurra verdades inconvenientes."
echo ""
echo -e "  ${CYAN}[2]${NC} ${YELLOW}Juno${NC} - Estrategista, imponente, visionaria"
echo -e "      A arquiteta de imperios e projetos ambiciosos."
echo ""
echo -e "  ${CYAN}[3]${NC} ${RED}Eris${NC} - Caotica, provocadora, explosiva"
echo -e "      A faisca que incendeia a monotonia."
echo ""

PROFILE_DIR="$SCRIPT_DIR/src/data_memory/user"
PROFILE_PATH="$PROFILE_DIR/profile.json"
mkdir -p "$PROFILE_DIR"

while true; do
    echo -n -e "  ${BOLD}Escolha [1-3]:${NC} "
    read -r DIVINITY_CHOICE

    case $DIVINITY_CHOICE in
        1)
            SELECTED_ENTITY="luna"
            ENTITY_NAME="Luna"
            break
            ;;
        2)
            SELECTED_ENTITY="juno"
            ENTITY_NAME="Juno"
            break
            ;;
        3)
            SELECTED_ENTITY="eris"
            ENTITY_NAME="Eris"
            break
            ;;
        *)
            echo -e "  ${RED}Opcao invalida. Escolha 1, 2 ou 3.${NC}"
            ;;
    esac
done

echo ""
print_success "Divindade selecionada: $ENTITY_NAME"

# Salvar escolha no profile.json
if [ -f "$PROFILE_PATH" ]; then
    # Atualizar arquivo existente
    ./venv/bin/python -c "
import json
import sys
try:
    with open('$PROFILE_PATH', 'r') as f:
        data = json.load(f)
except:
    data = {}
data['active_entity'] = '$SELECTED_ENTITY'
data['entity_selected_at'] = '$(date -Iseconds)'
with open('$PROFILE_PATH', 'w') as f:
    json.dump(data, f, indent=2)
print('OK')
" 2>/dev/null && print_success "Perfil atualizado" || print_warning "Perfil sera criado no primeiro uso"
else
    # Criar novo arquivo
    echo "{
  \"active_entity\": \"$SELECTED_ENTITY\",
  \"entity_selected_at\": \"$(date -Iseconds)\"
}" > "$PROFILE_PATH"
    print_success "Perfil criado com entidade: $ENTITY_NAME"
fi

echo ""

# ==============================================
# VERIFICACAO FINAL
# ==============================================
echo -e "${BLUE}=============================================="
echo -e "              VERIFICACAO FINAL"
echo -e "==============================================${NC}"
echo ""

echo "  ${BOLD}VENV Principal:${NC}"
echo "    Python: $(./venv/bin/python --version 2>&1)"

check_package() {
    local pkg=$1
    local name=$2
    ./venv/bin/python -c "import $pkg" 2>/dev/null && echo -e "    ${GREEN}OK${NC} $name" || echo -e "    ${RED}FALTA${NC} $name"
}

check_package "textual" "textual"
check_package "google.genai" "google-genai"
check_package "faster_whisper" "faster-whisper"
check_package "webrtcvad" "webrtcvad"
check_package "cv2" "opencv"
check_package "sounddevice" "sounddevice"
check_package "torch" "pytorch"
check_package "duckduckgo_search" "duckduckgo-search"
check_package "pystray" "pystray (system tray)"
check_package "resemblyzer" "resemblyzer (voice profile)"
check_package "soundfile" "soundfile"

echo ""

if [ -d "venv_tts" ]; then
    echo "  ${BOLD}VENV TTS:${NC}"
    echo "    Python: $(./venv_tts/bin/python --version 2>&1)"
    ./venv_tts/bin/python -c "import TTS; print('    OK coqui-tts')" 2>/dev/null || echo "    FALTA coqui-tts"
    ./venv_tts/bin/python -c "import chatterbox; print('    OK chatterbox-tts')" 2>/dev/null || echo "    FALTA chatterbox-tts (opcional)"
    echo ""
fi

echo "  ${BOLD}Sistema:${NC}"
echo "    ffmpeg: $(which ffmpeg 2>/dev/null && echo 'OK' || echo 'NAO encontrado')"
echo "    espeak-ng: $(which espeak-ng 2>/dev/null && echo 'OK' || echo 'NAO encontrado')"
echo ""

echo "  ${BOLD}Ollama (Modelos Locais):${NC}"
if check_command ollama; then
    echo "    ollama: OK"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "    servico: RODANDO"
        ollama list 2>/dev/null | head -5 | while read line; do
            echo "    modelo: $line"
        done
    else
        echo "    servico: PARADO (inicie com: ollama serve)"
    fi
else
    echo "    ollama: NAO instalado (opcional)"
fi
echo ""

echo "  ${BOLD}Daemon Mode (System Tray):${NC}"
if [ -f "/usr/lib/x86_64-linux-gnu/girepository-1.0/AyatanaAppIndicator3-0.1.typelib" ] || \
   [ -f "/usr/share/gir-1.0/AyatanaAppIndicator3-0.1.gir" ] || \
   [ -f "/usr/share/gir-1.0/AppIndicator3-0.1.gir" ]; then
    echo -e "    ${GREEN}OK${NC} AppIndicator disponivel (Ayatana ou legacy)"
else
    echo -e "    ${YELLOW}AVISO${NC} AppIndicator pode nao estar instalado"
    echo "    -> Execute: sudo apt install gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1"
fi
echo ""

# ==============================================
# CONCLUSAO
# ==============================================
echo -e "${GREEN}${BOLD}"
echo "=============================================="
echo "       Instalacao Concluida com Sucesso!"
echo "=============================================="
echo -e "${NC}"
echo ""
echo "  ${BOLD}Como iniciar Luna:${NC}"
echo "    1. Terminal:     ./run_luna.sh"
echo "    2. Janela:       ./run_luna.sh --launch"
echo "    3. Menu/Dock:    Procure por 'Luna' nos aplicativos"
echo ""
echo "  ${BOLD}Verificar instalacao:${NC}"
echo "    ./venv/bin/python src/tools/verify_install.py"
echo ""

# Verificar se API key foi configurada
if grep -q "GOOGLE_API_KEY=sua_chave" .env 2>/dev/null || ! grep -q "GOOGLE_API_KEY=." .env 2>/dev/null; then
    echo -e "  ${YELLOW}${BOLD}IMPORTANTE:${NC} Configure GOOGLE_API_KEY no .env"
    echo ""
fi
