#!/bin/bash

echo "=== Iniciando o Ritual de Banimento (Extase em 4R73) ==="
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="extase-em-4r73"
ICON_NAME="${APP_NAME}"

DESKTOP_ENTRY_DIR_USER="${HOME}/.local/share/applications"
ICON_INSTALL_SIZE_DIR_USER="${HOME}/.local/share/icons/hicolor/64x64/apps"
DESKTOP_ENTRY_DIR_SYSTEM="/usr/local/share/applications"
ICON_INSTALL_SIZE_DIR_SYSTEM="/usr/local/share/icons/hicolor/64x64/apps"

DESKTOP_FILE_PATH_USER="${DESKTOP_ENTRY_DIR_USER}/${APP_NAME}.desktop"
ICON_INSTALL_PATH_USER="${ICON_INSTALL_SIZE_DIR_USER}/${ICON_NAME}.png"
DESKTOP_FILE_PATH_SYSTEM="${DESKTOP_ENTRY_DIR_SYSTEM}/${APP_NAME}.desktop"
ICON_INSTALL_PATH_SYSTEM="${ICON_INSTALL_SIZE_DIR_SYSTEM}/${ICON_NAME}.png"

SUDO_CMD=""
if [[ -f "${DESKTOP_FILE_PATH_SYSTEM}" || -f "${ICON_INSTALL_PATH_SYSTEM}" ]]; then
    if [[ $(id -u) -ne 0 ]]; then
        SUDO_CMD="sudo"
        echo "Permissoes elevadas (sudo) podem ser necessarias para remover arquivos do sistema."
    fi
fi



echo "[1/5] Exorcizando pacotes do sistema (DEB/Flatpak)..."
if dpkg -l | grep -q "extase-em-4r73"; then
    echo "   -> Removendo pacote .deb (requer sudo)..."
    if [[ -z "$SUDO_CMD" ]]; then SUDO_CMD="sudo"; fi # Force sudo for apt
    $SUDO_CMD apt remove -y extase-em-4r73 || echo "   -> Aviso: Falha ao remover pacote .deb."
else
    echo "   -> Pacote .deb nao encontrado."
fi

if command -v flatpak &> /dev/null; then
    if flatpak list | grep -q "com.github.andrebfarias.extase-em-4r73"; then
        echo "   -> Removendo Flatpak..."
        flatpak uninstall -y com.github.andrebfarias.extase-em-4r73 || echo "   -> Aviso: Falha ao remover Flatpak."
    else
        echo "   -> Flatpak nao encontrado."
    fi
fi

echo "[2/5] Quebrando o circulo de protecao (venv)..."
rm -rf "${SCRIPT_DIR}/venv"

echo "[3/5] Apagando o sigilo de invocacao (.desktop)..."
if [[ -f "${DESKTOP_FILE_PATH_USER}" ]]; then
    rm -f "${DESKTOP_FILE_PATH_USER}" && echo "Lancador do usuario removido." || echo "Aviso: Falha ao remover lancador do usuario."
fi
if [[ -f "${DESKTOP_FILE_PATH_SYSTEM}" ]]; then
    $SUDO_CMD rm -f "${DESKTOP_FILE_PATH_SYSTEM}" && echo "Lancador do sistema removido." || echo "Aviso: Falha ao remover lancador do sistema (Verifique permissoes sudo)."
fi

echo "[4/5] Desconsagrando o icone..."
if [[ -f "${ICON_INSTALL_PATH_USER}" ]]; then
    rm -f "${ICON_INSTALL_PATH_USER}" && echo "   -> Icone do usuario removido." || echo "   -> Aviso: Falha ao remover icone do usuario."
fi
if [[ -f "${ICON_INSTALL_PATH_SYSTEM}" ]]; then
    $SUDO_CMD rm -f "${ICON_INSTALL_PATH_SYSTEM}" && echo "   -> Icone do sistema removido." || echo "   -> Aviso: Falha ao remover icone do sistema (Verifique permissoes sudo)."
fi

NEED_DB_UPDATE=false
if command -v update-desktop-database &> /dev/null; then NEED_DB_UPDATE=true; fi
NEED_ICON_UPDATE=false
if command -v gtk-update-icon-cache &> /dev/null; then NEED_ICON_UPDATE=true; fi

if $NEED_DB_UPDATE ; then
    echo "   -> Atualizando database de aplicativos..."
    if [[ -d "${DESKTOP_ENTRY_DIR_USER}" ]]; then update-desktop-database "${DESKTOP_ENTRY_DIR_USER}" >/dev/null 2>&1; fi
    if [[ -d "${DESKTOP_ENTRY_DIR_SYSTEM}" ]]; then $SUDO_CMD update-desktop-database "${DESKTOP_ENTRY_DIR_SYSTEM}" >/dev/null 2>&1; fi
fi
if $NEED_ICON_UPDATE ; then
     echo "   -> Atualizando cache de icones..."
     ICON_BASE_DIR_USER="$HOME/.local/share/icons/hicolor/"
     ICON_BASE_DIR_SYSTEM="/usr/local/share/icons/hicolor/"
     if [[ -d "$ICON_BASE_DIR_USER" ]]; then gtk-update-icon-cache "$ICON_BASE_DIR_USER" -f -t >/dev/null 2>&1; fi
     if [[ -d "$ICON_BASE_DIR_SYSTEM" ]]; then $SUDO_CMD gtk-update-icon-cache "$ICON_BASE_DIR_SYSTEM" -f -t >/dev/null 2>&1; fi
fi

echo "[5/5] Limpando cache Python, atlas GPU, logs e dados temporarios..."
# User Config/Cache specifics
rm -rf "${HOME}/.config/extase-em-4r73" 2>/dev/null && echo "   -> Configurações (~/.config/extase-em-4r73) removidas."
rm -rf "${HOME}/.cache/extase-em-4r73" 2>/dev/null && echo "   -> Cache do usuário (~/.cache/extase-em-4r73) removido."
find "${SCRIPT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${SCRIPT_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "${SCRIPT_DIR}" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
rm -rf "${SCRIPT_DIR}/.cache" 2>/dev/null && echo "   -> Atlas GPU (.cache) removido."
rm -rf "${SCRIPT_DIR}/logs" 2>/dev/null && echo "   -> Logs removidos."
rm -f "${SCRIPT_DIR}/*.stats" 2>/dev/null && echo "   -> Arquivos de profile removidos."
rm -rf "${SCRIPT_DIR}/benchmark_output" 2>/dev/null && echo "   -> Benchmarks removidos."
echo "   -> Limpeza concluida."

echo "=== Banimento Concluido ==="
echo "As dependencias do sistema (GTK, OpenCV) foram mantidas."
