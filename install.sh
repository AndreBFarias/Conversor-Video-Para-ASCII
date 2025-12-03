#!/bin/bash

echo "=== Iniciando o Ritual de Instalação (Êxtase em 4R73) ==="
# SCRIPT_DIR agora aponta para o diretório onde o script está localizado
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="extase-em-4r73"
APP_DISPLAY_NAME="Êxtase em 4R73"
ICON_NAME="${APP_NAME}"
ICON_SOURCE_PATH="${SCRIPT_DIR}/src/assets/logo.png"

# Destinos
DESKTOP_ENTRY_DIR_USER="${HOME}/.local/share/applications"
ICON_INSTALL_SIZE_DIR_USER="${HOME}/.local/share/icons/hicolor/64x64/apps" # Diretório específico para 64x64
DESKTOP_ENTRY_DIR_SYSTEM="/usr/local/share/applications"
ICON_INSTALL_SIZE_DIR_SYSTEM="/usr/local/share/icons/hicolor/64x64/apps"

# Escolhe diretório (prioriza usuário)
INSTALL_DIR=""
ICON_INSTALL_DIR=""
SUDO_CMD=""
mkdir -p "${DESKTOP_ENTRY_DIR_USER}"
mkdir -p "${ICON_INSTALL_SIZE_DIR_USER}" # Cria o diretório de ícone 64x64

if [[ -w "${DESKTOP_ENTRY_DIR_USER}" && -w "${ICON_INSTALL_SIZE_DIR_USER}" ]]; then
    INSTALL_DIR="${DESKTOP_ENTRY_DIR_USER}"
    ICON_INSTALL_DIR="${ICON_INSTALL_SIZE_DIR_USER}" # Instala no diretório 64x64
    echo "Instalando para o usuário atual (${USER})."
else
    echo "Diretório do usuário não gravável ou inexistente. Tentando instalação no sistema (requer sudo)."
    INSTALL_DIR="${DESKTOP_ENTRY_DIR_SYSTEM}"
    ICON_INSTALL_DIR="${ICON_INSTALL_SIZE_DIR_SYSTEM}" # Instala no diretório 64x64 do sistema
    SUDO_CMD="sudo"
fi
DESKTOP_FILE_PATH="${INSTALL_DIR}/${APP_NAME}.desktop"
ICON_INSTALL_PATH="${ICON_INSTALL_DIR}/${ICON_NAME}.png" # Nome do ícone instalado

# 1. Atualizar repositórios
echo "[1/7] Atualizando selos arcanos (apt update)..."
sudo apt update || { echo "ERRO: Falha ao atualizar repositórios apt."; exit 1; }

# 2. Instalar dependências do sistema
echo "[2/7] Invocando dependências (Python3, PIP, GTK, OpenCV)..."
# Garante python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, e ImageMagick para redimensionar ícone
# Adicionado libgirepository1.0-dev e libcairo2-dev para compilação do PyGObject via pip se necessário
sudo apt install -y python3-pip python3-venv python3-opencv python3-gi python3-gi-cairo gir1.2-gtk-3.0 desktop-file-utils imagemagick libgirepository1.0-dev libcairo2-dev || { echo "ERRO: Falha ao instalar dependências do sistema."; exit 1; }

# 3. Criar ambiente virtual COM ACESSO AOS PACOTES DO SISTEMA
echo "[3/7] Desenhando círculo de proteção (venv --system-site-packages)..."
# Remove venv antigo se existir
if [ -d "${SCRIPT_DIR}/venv" ]; then
    echo "Removendo venv antigo..."
    rm -rf "${SCRIPT_DIR}/venv"
fi
# A flag --system-site-packages é CRUCIAL
python3 -m venv --system-site-packages "${SCRIPT_DIR}/venv" || { echo "ERRO: Falha ao criar ambiente virtual."; exit 1; }

# 4. Instalar dependências Python no venv
echo "[4/7] Instalando pacotes Python no venv (numpy, opencv-python)..."
if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "ERRO: requirements.txt não encontrado em ${SCRIPT_DIR}!"
    exit 1
fi
# Usamos o pip do venv diretamente
"${SCRIPT_DIR}/venv/bin/pip" install --upgrade pip || echo "Aviso: Falha ao atualizar pip."
"${SCRIPT_DIR}/venv/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" || { echo "ERRO: Falha ao instalar pacotes Python do requirements.txt."; exit 1; }

# 5. Criar pastas de trabalho
echo "[5/7] Preparando os altares ('videos_entrada' e 'videos_saida')..."
mkdir -p "${SCRIPT_DIR}/videos_entrada" || echo "Aviso: Falha ao criar videos_entrada."
mkdir -p "${SCRIPT_DIR}/videos_saida" || echo "Aviso: Falha ao criar videos_saida."

# 6. Instalar o Ícone
echo "[6/7] Consagrando o ícone em ${ICON_INSTALL_DIR}..."
if [ ! -f "${ICON_SOURCE_PATH}" ]; then
    echo "ERRO: Ícone '${ICON_SOURCE_PATH}' não encontrado!"
    exit 1
fi
$SUDO_CMD mkdir -p "${ICON_INSTALL_DIR}"
# Redimensiona ícone para 64x64 usando 'convert'
if command -v convert &> /dev/null; then
     echo "Redimensionando ícone para 64x64..."
     $SUDO_CMD convert "${ICON_SOURCE_PATH}" -resize 64x64 "${ICON_INSTALL_PATH}" || { echo "ERRO: Falha ao redimensionar ou copiar ícone."; exit 1; }
else
     echo "ERRO: 'convert' (ImageMagick) não encontrado. Não é possível redimensionar o ícone."
     echo "Instale com: sudo apt install imagemagick"
     exit 1
fi
# Atualiza cache de ícones
if command -v gtk-update-icon-cache &> /dev/null; then
    CACHE_DIR_TO_UPDATE=""
    if [[ -n "$SUDO_CMD" ]]; then CACHE_DIR_TO_UPDATE="/usr/local/share/icons/hicolor/"; else CACHE_DIR_TO_UPDATE="$HOME/.local/share/icons/hicolor/"; fi
    if [[ -d "$CACHE_DIR_TO_UPDATE" ]]; then
      echo "Atualizando cache de ícones em ${CACHE_DIR_TO_UPDATE}..."
      $SUDO_CMD gtk-update-icon-cache "$CACHE_DIR_TO_UPDATE" -f -t || echo "Aviso: Falha ao atualizar cache de ícones."
    fi
fi


# 7. Criar o Lançador (.desktop)
echo "[7/7] Forjando o sigilo de invocação (${DESKTOP_FILE_PATH})..."
$SUDO_CMD mkdir -p "${INSTALL_DIR}"

# --- Exec= CORRIGIDO ---
PYTHON_VENV_PATH="${SCRIPT_DIR}/venv/bin/python3"
MAIN_SCRIPT_PATH="${SCRIPT_DIR}/main.py" # main.py está na raiz
# Garante que os caminhos sejam absolutos e escapados
EXEC_COMMAND="\"${PYTHON_VENV_PATH}\" \"${MAIN_SCRIPT_PATH}\""

# Categorias Corrigidas
CATEGORIES="AudioVideo;Video;Graphics;" # Padrão recomendado

# Usa printf para criar o arquivo .desktop
$SUDO_CMD printf "[Desktop Entry]\nVersion=1.0\nName=%s\nComment=Conversor de Vídeos para Arte ASCII\nExec=%s\nIcon=%s\nTerminal=false\nType=Application\nCategories=%s\nStartupNotify=true\nPath=%s\n" \
    "${APP_DISPLAY_NAME}" \
    "${EXEC_COMMAND}" \
    "${ICON_NAME}" \
    "${CATEGORIES}" \
    "${SCRIPT_DIR}" \
    > "${DESKTOP_FILE_PATH}" || { echo "ERRO: Falha ao criar arquivo .desktop."; exit 1; }


# Valida o arquivo .desktop
if command -v desktop-file-validate &> /dev/null; then
    if ! desktop-file-validate "${DESKTOP_FILE_PATH}" >/dev/null; then
         echo "Aviso: Arquivo .desktop (${DESKTOP_FILE_PATH}) pode conter erros. Validação:"
         desktop-file-validate "${DESKTOP_FILE_PATH}" # Mostra o erro se houver
    else
         echo "Arquivo .desktop validado com sucesso."
    fi
fi

# Atualiza database de apps
if command -v update-desktop-database &> /dev/null; then
    DB_DIR_TO_UPDATE=""
     if [[ -n "$SUDO_CMD" ]]; then DB_DIR_TO_UPDATE="${DESKTOP_ENTRY_DIR_SYSTEM}"; else DB_DIR_TO_UPDATE="${DESKTOP_ENTRY_DIR_USER}"; fi
     if [[ -d "$DB_DIR_TO_UPDATE" ]]; then
       echo "Atualizando database de aplicativos em ${DB_DIR_TO_UPDATE}..."
       $SUDO_CMD update-desktop-database "${DB_DIR_TO_UPDATE}" || echo "Aviso: Falha ao atualizar database de apps."
     fi
fi


echo "=== Ritual Concluído ==="
echo "Você agora pode encontrar '${APP_DISPLAY_NAME}' no seu menu de aplicativos."
echo "Para invocar manualmente, navegue até '${SCRIPT_DIR}' e execute:"
echo "source venv/bin/activate"
echo "python3 main.py"
