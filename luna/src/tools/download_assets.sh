#!/bin/bash
set -euo pipefail

REPO_OWNER="AndreBFarias"
REPO_NAME="Luna"
RELEASE_TAG="v3.6.0-assets"
BASE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${RELEASE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ASSETS_DIR="${PROJECT_ROOT}/src/assets/panteao/entities"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

show_banner() {
    echo ""
    echo "  _    _   _ _   _    _"
    echo " | |  | | | | \ | |  / \\"
    echo " | |  | | | |  \| | / _ \\"
    echo " | |__| |_| | |\  |/ ___ \\"
    echo " |_____\___/|_| \_/_/   \_\\"
    echo ""
    echo "=========================================="
    echo "   Download de Assets (Voice Models)"
    echo "=========================================="
    echo ""
}

check_deps() {
    local missing=()

    for cmd in curl tar; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Dependencias ausentes: ${missing[*]}"
        echo ""
        echo "Instale com:"
        echo "  Ubuntu/Debian: sudo apt install ${missing[*]}"
        echo "  Fedora: sudo dnf install ${missing[*]}"
        exit 1
    fi

    log_success "Dependencias verificadas"
}

check_asset_exists() {
    local asset_name="$1"
    local check_path="$2"

    if [ -e "$check_path" ]; then
        return 0
    fi
    return 1
}

download_file() {
    local url="$1"
    local output="$2"
    local name="$3"

    log_info "Baixando ${name}..."

    if curl -fSL --progress-bar -o "$output" "$url"; then
        log_success "${name} baixado"
        return 0
    else
        log_error "Falha ao baixar ${name}"
        return 1
    fi
}

extract_archive() {
    local archive="$1"
    local dest="$2"
    local name="$3"

    log_info "Extraindo ${name}..."

    mkdir -p "$dest"

    if tar -xzf "$archive" -C "$dest"; then
        log_success "${name} extraido"
        rm -f "$archive"
        return 0
    else
        log_error "Falha ao extrair ${name}"
        return 1
    fi
}

download_voice_models_female() {
    local archive_name="voice-models-female.tar.gz"
    local check_file="${ASSETS_DIR}/luna/voice/coqui/reference.wav"

    if check_asset_exists "female-voices" "$check_file"; then
        log_warn "Vozes femininas ja instaladas (pulando)"
        return 0
    fi

    local tmp_file="/tmp/${archive_name}"

    if download_file "${BASE_URL}/${archive_name}" "$tmp_file" "Vozes Femininas (~100MB)"; then
        extract_archive "$tmp_file" "$ASSETS_DIR" "Vozes Femininas"
    fi
}

download_entity_voice() {
    local entity="$1"
    local size="$2"
    local archive_name="voice-${entity}.tar.gz"
    local check_file="${ASSETS_DIR}/${entity}/voice/coqui/model_final.pt"

    if [ -f "$check_file" ]; then
        log_warn "${entity}: modelo ja instalado (pulando)"
        return 0
    fi

    local tmp_file="/tmp/${archive_name}"

    if download_file "${BASE_URL}/${archive_name}" "$tmp_file" "${entity} (${size})"; then
        extract_archive "$tmp_file" "$ASSETS_DIR" "${entity}"
    fi
}

download_voice_models_male() {
    local lars_check="${ASSETS_DIR}/lars/voice/coqui/model_final.pt"
    local mars_check="${ASSETS_DIR}/mars/voice/coqui/model_final.pt"
    local somn_check="${ASSETS_DIR}/somn/voice/coqui/model_final.pt"

    if [ -f "$lars_check" ] && [ -f "$mars_check" ] && [ -f "$somn_check" ]; then
        log_warn "Vozes masculinas ja instaladas (pulando)"
        return 0
    fi

    echo ""
    log_warn "Vozes masculinas sao grandes (~1.7GB cada, ~5.1GB total)"
    echo "Entidades: Lars, Mars, Somn"
    echo ""
    echo -n "Deseja baixar todas? [s/N] "
    read -r response

    if [[ ! "$response" =~ ^[sS]$ ]]; then
        log_info "Download de vozes masculinas pulado"
        return 0
    fi

    download_entity_voice "lars" "1.7GB"
    download_entity_voice "mars" "1.7GB"
    download_entity_voice "somn" "1.7GB"
}

verify_installation() {
    echo ""
    echo "=========================================="
    echo "   Verificacao de Assets"
    echo "=========================================="
    echo ""

    local entities=("luna" "eris" "juno" "lars" "mars" "somn")
    local missing=0

    for entity in "${entities[@]}"; do
        local voice_dir="${ASSETS_DIR}/${entity}/voice"
        local coqui_ref="${voice_dir}/coqui/reference.wav"
        local coqui_ref_speaker="${voice_dir}/coqui/reference_speaker.wav"
        local chat_ref="${voice_dir}/chatterbox/reference.wav"
        local model_pt="${voice_dir}/coqui/model_final.pt"

        if [ -f "$model_pt" ]; then
            log_success "${entity}: modelo treinado instalado (1.8GB)"
        elif [ -f "$coqui_ref" ] || [ -f "$coqui_ref_speaker" ] || [ -f "$chat_ref" ]; then
            log_success "${entity}: voice reference instalado"
        elif [ -f "${coqui_ref}.gz" ] || [ -f "${coqui_ref_speaker}.gz" ] || [ -f "${chat_ref}.gz" ]; then
            log_success "${entity}: voice reference comprimido (runtime)"
        else
            log_warn "${entity}: sem voice model (fallback do sistema)"
            ((missing++))
        fi
    done

    echo ""

    if [ $missing -eq 0 ]; then
        log_success "Todos os assets instalados"
    else
        log_warn "${missing} entidade(s) sem voice model dedicado"
        echo "O sistema usara TTS do sistema como fallback para essas entidades."
    fi
}

show_help() {
    echo "Uso: $0 [opcao]"
    echo ""
    echo "Opcoes:"
    echo "  --all       Baixar todos os assets"
    echo "  --female    Baixar apenas vozes femininas"
    echo "  --male      Baixar apenas vozes masculinas"
    echo "  --verify    Verificar assets instalados"
    echo "  --help      Mostrar esta ajuda"
    echo ""
    echo "Sem opcao: modo interativo"
}

main() {
    show_banner
    check_deps

    case "${1:-}" in
        --all)
            download_voice_models_female
            download_voice_models_male
            ;;
        --female)
            download_voice_models_female
            ;;
        --male)
            download_voice_models_male
            ;;
        --verify)
            verify_installation
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "O que deseja baixar?"
            echo ""
            echo "  1) Vozes femininas (~100MB) - Luna, Eris, Juno"
            echo "  2) Vozes masculinas (~5.4GB) - Lars, Mars, Somn"
            echo "  3) Todos os assets"
            echo "  4) Apenas verificar instalacao"
            echo "  5) Sair"
            echo ""
            echo -n "Opcao [1-5]: "
            read -r choice

            case "$choice" in
                1) download_voice_models_female ;;
                2) download_voice_models_male ;;
                3)
                    download_voice_models_female
                    download_voice_models_male
                    ;;
                4)
                    verify_installation
                    exit 0
                    ;;
                5)
                    log_info "Saindo..."
                    exit 0
                    ;;
                *)
                    log_error "Opcao invalida"
                    exit 1
                    ;;
            esac
            ;;
    esac

    verify_installation

    echo ""
    log_success "Download concluido"
    echo ""
    echo "Para iniciar Luna:"
    echo "  ./run_luna.sh"
    echo ""
}

main "$@"
