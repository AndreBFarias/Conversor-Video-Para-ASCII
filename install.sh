#!/bin/bash

echo "=== Iniciando o Ritual de Instalacao (Extase em 4R73) ==="
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="extase-em-4r73"
APP_DISPLAY_NAME="Extase em 4R73"
ICON_NAME="${APP_NAME}"
ICON_SOURCE_PATH="${SCRIPT_DIR}/assets/logo.png"

DESKTOP_ENTRY_DIR_USER="${HOME}/.local/share/applications"
ICON_INSTALL_SIZE_DIR_USER="${HOME}/.local/share/icons/hicolor/64x64/apps"
DESKTOP_ENTRY_DIR_SYSTEM="/usr/local/share/applications"
ICON_INSTALL_SIZE_DIR_SYSTEM="/usr/local/share/icons/hicolor/64x64/apps"

INSTALL_DIR=""
ICON_INSTALL_DIR=""
SUDO_CMD=""
mkdir -p "${DESKTOP_ENTRY_DIR_USER}"
mkdir -p "${ICON_INSTALL_SIZE_DIR_USER}"

if [[ -w "${DESKTOP_ENTRY_DIR_USER}" && -w "${ICON_INSTALL_SIZE_DIR_USER}" ]]; then
    INSTALL_DIR="${DESKTOP_ENTRY_DIR_USER}"
    ICON_INSTALL_DIR="${ICON_INSTALL_SIZE_DIR_USER}"
    echo "Instalando para o usuario atual (${USER})."
else
    echo "Diretorio do usuario nao gravavel ou inexistente. Tentando instalacao no sistema (requer sudo)."
    INSTALL_DIR="${DESKTOP_ENTRY_DIR_SYSTEM}"
    ICON_INSTALL_DIR="${ICON_INSTALL_SIZE_DIR_SYSTEM}"
    SUDO_CMD="sudo"
fi
DESKTOP_FILE_PATH="${INSTALL_DIR}/${APP_NAME}.desktop"
ICON_INSTALL_PATH="${ICON_INSTALL_DIR}/${ICON_NAME}.png"

echo "[1/7] Atualizando selos arcanos (apt update)..."
sudo apt update || { echo "ERRO: Falha ao atualizar repositorios apt."; exit 1; }

echo "[2/7] Invocando dependencias (Python3, PIP, GTK, OpenCV)..."
sudo apt install -y python3-pip python3-venv python3-opencv python3-gi python3-gi-cairo gir1.2-gtk-3.0 desktop-file-utils imagemagick libgirepository1.0-dev libcairo2-dev || { echo "ERRO: Falha ao instalar dependencias do sistema."; exit 1; }

echo "[3/7] Desenhando circulo de protecao (venv --system-site-packages)..."
if [ -d "${SCRIPT_DIR}/venv" ]; then
    echo "Removendo venv antigo..."
    rm -rf "${SCRIPT_DIR}/venv"
fi
python3 -m venv --system-site-packages "${SCRIPT_DIR}/venv" || { echo "ERRO: Falha ao criar ambiente virtual."; exit 1; }

echo "[4/7] Instalando pacotes Python no venv (numpy, opencv-python)..."
echo "NOTA: PyGObject/GTK ja esta disponivel via pacotes do sistema (--system-site-packages)"
if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "ERRO: requirements.txt nao encontrado em ${SCRIPT_DIR}!"
    exit 1
fi
"${SCRIPT_DIR}/venv/bin/pip" install --upgrade pip || echo "Aviso: Falha ao atualizar pip."
"${SCRIPT_DIR}/venv/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" || { echo "ERRO: Falha ao instalar pacotes Python do requirements.txt."; exit 1; }

echo "[5/7] Preparando os altares ('data_input' e 'data_output')..."
mkdir -p "${SCRIPT_DIR}/data_input" || echo "Aviso: Falha ao criar data_input."
mkdir -p "${SCRIPT_DIR}/data_output" || echo "Aviso: Falha ao criar data_output."

echo "[6/7] Consagrando o icone em ${ICON_INSTALL_DIR}..."
if [ ! -f "${ICON_SOURCE_PATH}" ]; then
    echo "ERRO: Icone '${ICON_SOURCE_PATH}' nao encontrado!"
    exit 1
fi
$SUDO_CMD mkdir -p "${ICON_INSTALL_DIR}"
if command -v convert &> /dev/null; then
     echo "Redimensionando icone para 64x64..."
     $SUDO_CMD convert "${ICON_SOURCE_PATH}" -resize 64x64 "${ICON_INSTALL_PATH}" || { echo "ERRO: Falha ao redimensionar ou copiar icone."; exit 1; }
else
     echo "ERRO: 'convert' (ImageMagick) nao encontrado. Nao e possivel redimensionar o icone."
     echo "Instale com: sudo apt install imagemagick"
     exit 1
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    CACHE_DIR_TO_UPDATE=""
    if [[ -n "$SUDO_CMD" ]]; then CACHE_DIR_TO_UPDATE="/usr/local/share/icons/hicolor/"; else CACHE_DIR_TO_UPDATE="$HOME/.local/share/icons/hicolor/"; fi
    if [[ -d "$CACHE_DIR_TO_UPDATE" ]]; then
      echo "Atualizando cache de icones em ${CACHE_DIR_TO_UPDATE}..."
      $SUDO_CMD gtk-update-icon-cache "$CACHE_DIR_TO_UPDATE" -f -t || echo "Aviso: Falha ao atualizar cache de icones."
    fi
fi

echo "[7/7] Forjando o sigilo de invocacao (${DESKTOP_FILE_PATH})..."
$SUDO_CMD mkdir -p "${INSTALL_DIR}"

PYTHON_VENV_PATH="${SCRIPT_DIR}/venv/bin/python3"
MAIN_SCRIPT_PATH="${SCRIPT_DIR}/main.py"
EXEC_COMMAND="\"${PYTHON_VENV_PATH}\" \"${MAIN_SCRIPT_PATH}\""

CATEGORIES="AudioVideo;Video;Graphics;"

$SUDO_CMD printf "[Desktop Entry]\nVersion=2.0\nName=%s\nComment=Conversor de Videos e Imagens para Arte ASCII\nExec=%s\nIcon=%s\nTerminal=false\nType=Application\nCategories=%s\nStartupNotify=true\nPath=%s\n" \
    "${APP_DISPLAY_NAME}" \
    "${EXEC_COMMAND}" \
    "${ICON_NAME}" \
    "${CATEGORIES}" \
    "${SCRIPT_DIR}" \
    > "${DESKTOP_FILE_PATH}" || { echo "ERRO: Falha ao criar arquivo .desktop."; exit 1; }

if command -v desktop-file-validate &> /dev/null; then
    if ! desktop-file-validate "${DESKTOP_FILE_PATH}" >/dev/null; then
         echo "Aviso: Arquivo .desktop (${DESKTOP_FILE_PATH}) pode conter erros. Validacao:"
         desktop-file-validate "${DESKTOP_FILE_PATH}"
    else
         echo "Arquivo .desktop validado com sucesso."
    fi
fi

if command -v update-desktop-database &> /dev/null; then
    DB_DIR_TO_UPDATE=""
     if [[ -n "$SUDO_CMD" ]]; then DB_DIR_TO_UPDATE="${DESKTOP_ENTRY_DIR_SYSTEM}"; else DB_DIR_TO_UPDATE="${DESKTOP_ENTRY_DIR_USER}"; fi
     if [[ -d "$DB_DIR_TO_UPDATE" ]]; then
       echo "Atualizando database de aplicativos em ${DB_DIR_TO_UPDATE}..."
       $SUDO_CMD update-desktop-database "${DB_DIR_TO_UPDATE}" || echo "Aviso: Falha ao atualizar database de apps."
     fi
fi

echo "=== Ritual Concluido ==="
echo "Voce agora pode encontrar '${APP_DISPLAY_NAME}' no seu menu de aplicativos."
echo "Para invocar manualmente, navegue ate '${SCRIPT_DIR}' e execute:"
echo "source venv/bin/activate"
echo "python3 main.py"
