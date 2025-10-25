#!/bin/bash
#
# RITUAL DE BANIMENTO (SEGURO): Êxtase em 4R73
#

echo "=== Iniciando o Ritual de Banimento (Êxtase em 4R73) ==="
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="extase-em-4r73"
ICON_NAME="${APP_NAME}"

# Locais possíveis
DESKTOP_ENTRY_DIR_USER="${HOME}/.local/share/applications"
ICON_INSTALL_SIZE_DIR_USER="${HOME}/.local/share/icons/hicolor/64x64/apps"
DESKTOP_ENTRY_DIR_SYSTEM="/usr/local/share/applications"
ICON_INSTALL_SIZE_DIR_SYSTEM="/usr/local/share/icons/hicolor/64x64/apps"

DESKTOP_FILE_PATH_USER="${DESKTOP_ENTRY_DIR_USER}/${APP_NAME}.desktop"
ICON_INSTALL_PATH_USER="${ICON_INSTALL_SIZE_DIR_USER}/${ICON_NAME}.png"
DESKTOP_FILE_PATH_SYSTEM="${DESKTOP_ENTRY_DIR_SYSTEM}/${APP_NAME}.desktop"
ICON_INSTALL_PATH_SYSTEM="${ICON_INSTALL_SIZE_DIR_SYSTEM}/${ICON_NAME}.png"

SUDO_CMD=""
# Determina se precisa de sudo
if [[ -f "${DESKTOP_FILE_PATH_SYSTEM}" || -f "${ICON_INSTALL_PATH_SYSTEM}" ]]; then
    if [[ $(id -u) -ne 0 ]]; then
        SUDO_CMD="sudo"
        echo "Permissões elevadas (sudo) podem ser necessárias para remover arquivos do sistema."
    fi
fi

# 1. Remover ambiente virtual
echo "[1/4] Quebrando o círculo de proteção (venv)..."
rm -rf "${SCRIPT_DIR}/venv"

# 2. Remover o Lançador (.desktop)
echo "[2/4] Apagando o sigilo de invocação (.desktop)..."
if [[ -f "${DESKTOP_FILE_PATH_USER}" ]]; then
    rm -f "${DESKTOP_FILE_PATH_USER}" && echo "Lançador do usuário removido." || echo "Aviso: Falha ao remover lançador do usuário."
fi
if [[ -f "${DESKTOP_FILE_PATH_SYSTEM}" ]]; then
    $SUDO_CMD rm -f "${DESKTOP_FILE_PATH_SYSTEM}" && echo "Lançador do sistema removido." || echo "Aviso: Falha ao remover lançador do sistema (Verifique permissões sudo)."
fi

# 3. Remover o Ícone
echo "[3/4] Desconsagrando o ícone..."
if [[ -f "${ICON_INSTALL_PATH_USER}" ]]; then
    rm -f "${ICON_INSTALL_PATH_USER}" && echo "Ícone do usuário removido." || echo "Aviso: Falha ao remover ícone do usuário."
fi
if [[ -f "${ICON_INSTALL_PATH_SYSTEM}" ]]; then
    $SUDO_CMD rm -f "${ICON_INSTALL_PATH_SYSTEM}" && echo "Ícone do sistema removido." || echo "Aviso: Falha ao remover ícone do sistema (Verifique permissões sudo)."
fi

# Atualiza caches (se possível e necessário)
NEED_DB_UPDATE=false
if command -v update-desktop-database &> /dev/null; then NEED_DB_UPDATE=true; fi
NEED_ICON_UPDATE=false
if command -v gtk-update-icon-cache &> /dev/null; then NEED_ICON_UPDATE=true; fi

if $NEED_DB_UPDATE ; then
    echo "Atualizando database de aplicativos..."
    if [[ -d "${DESKTOP_ENTRY_DIR_USER}" ]]; then update-desktop-database "${DESKTOP_ENTRY_DIR_USER}" >/dev/null 2>&1; fi
    if [[ -d "${DESKTOP_ENTRY_DIR_SYSTEM}" ]]; then $SUDO_CMD update-desktop-database "${DESKTOP_ENTRY_DIR_SYSTEM}" >/dev/null 2>&1; fi
fi
if $NEED_ICON_UPDATE ; then
     echo "Atualizando cache de ícones..."
     ICON_BASE_DIR_USER="$HOME/.local/share/icons/hicolor/"
     ICON_BASE_DIR_SYSTEM="/usr/local/share/icons/hicolor/"
     if [[ -d "$ICON_BASE_DIR_USER" ]]; then gtk-update-icon-cache "$ICON_BASE_DIR_USER" -f -t >/dev/null 2>&1; fi
     if [[ -d "$ICON_BASE_DIR_SYSTEM" ]]; then $SUDO_CMD gtk-update-icon-cache "$ICON_BASE_DIR_SYSTEM" -f -t >/dev/null 2>&1; fi
fi

# --- FIM DA PERGUNTA SEGURA ---

echo "=== Banimento Concluído ==="
echo "As dependências do sistema (GTK, OpenCV) foram mantidas."
