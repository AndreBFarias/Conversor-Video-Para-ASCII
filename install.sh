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

echo "[1/8] Atualizando selos arcanos (apt update)..."
sudo apt update || { echo "ERRO: Falha ao atualizar repositorios apt."; exit 1; }

echo "[2/8] Invocando dependencias (Python3, PIP, GTK, OpenCV, VTE, Kitty, PortAudio, FFmpeg)..."
sudo apt install -y python3-pip python3-venv python3-opencv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-vte-2.91 kitty desktop-file-utils imagemagick libgirepository1.0-dev libcairo2-dev portaudio19-dev ffmpeg libwebp-dev || { echo "ERRO: Falha ao instalar dependencias do sistema."; exit 1; }

echo "[3/8] Desenhando circulo de protecao (venv --system-site-packages)..."
if [ -d "${SCRIPT_DIR}/venv" ]; then
    echo "Removendo venv antigo..."
    rm -rf "${SCRIPT_DIR}/venv"
fi
python3 -m venv --system-site-packages "${SCRIPT_DIR}/venv" || { echo "ERRO: Falha ao criar ambiente virtual."; exit 1; }

echo "   -> Verificando acesso ao GTK no venv..."
if ! "${SCRIPT_DIR}/venv/bin/python3" -c "import gi; print('GTK bindings OK')" &> /dev/null; then
    echo "ERRO: O modulo 'gi' nao foi encontrado dentro do venv."
    echo "      Isso geralmente significa que 'python3-gi' nao esta instalado ou o venv nao foi criado com acesso aos pacotes do sistema."
    echo "      Tentando corrigir instalando dependencias novamente..."
    sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0

    # Re-check
    if ! "${SCRIPT_DIR}/venv/bin/python3" -c "import gi" &> /dev/null; then
         echo "FATAL: Ainda nao foi possivel acessar 'gi' no venv. Abortando."
         exit 1
    fi
fi

echo "[4/8] Instalando pacotes Python no venv..."
echo "NOTA: PyGObject/GTK ja esta disponivel via pacotes do sistema (--system-site-packages)"
echo "NOTA: Instalando PyTorch antes de MediaPipe para evitar conflitos de versao"
if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "ERRO: requirements.txt nao encontrado em ${SCRIPT_DIR}!"
    exit 1
fi

if command -v nvidia-smi &> /dev/null; then
    echo "   -> GPU NVIDIA detectada! Instalando suporte a CUDA (cupy-cuda12x)..."
else
    echo "   -> AVISO: GPU NVIDIA nao detectada. cupy pode falhar. Continuando instalacao..."
fi

"${SCRIPT_DIR}/venv/bin/pip" install --upgrade pip setuptools wheel || echo "Aviso: Falha ao atualizar ferramentas pip."

echo "   -> Instalando PyTorch com versoes fixas (torch 2.5.1, torchvision 0.20.1)..."
if command -v nvidia-smi &> /dev/null; then
    echo "   -> GPU NVIDIA detectada, instalando versao CUDA..."
    "${SCRIPT_DIR}/venv/bin/pip" install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121 || { echo "ERRO: Falha ao instalar PyTorch CUDA."; exit 1; }
else
    echo "   -> GPU nao detectada, instalando versao CPU..."
    "${SCRIPT_DIR}/venv/bin/pip" install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu || { echo "ERRO: Falha ao instalar PyTorch CPU."; exit 1; }
fi

echo "   -> Instalando dependencias basicas (opencv, numpy, pillow)..."
"${SCRIPT_DIR}/venv/bin/pip" install opencv-python "numpy>=1.24.0,<2.0.0" Pillow || { echo "ERRO: Falha ao instalar dependencias basicas."; exit 1; }

echo "   -> Tentando instalar suporte GPU (cupy-cuda12x)..."
if command -v nvidia-smi &> /dev/null; then
    if "${SCRIPT_DIR}/venv/bin/pip" install cupy-cuda12x 2>&1; then
        echo "   -> cupy-cuda12x instalado com sucesso!"
    else
        echo "   -> AVISO: Falha ao instalar cupy-cuda12x. Continuando sem suporte GPU."
        echo "   -> Para ativar GPU depois, execute: ${SCRIPT_DIR}/venv/bin/pip install cupy-cuda12x"
    fi
else
    echo "   -> Pulando instalacao de cupy (GPU nao detectada)."
fi

echo "   -> Instalando MediaPipe para segmentacao automatica..."
"${SCRIPT_DIR}/venv/bin/pip" install mediapipe || echo "Aviso: Falha ao instalar mediapipe. Auto Seg nao funcionara."

echo "   -> Instalando PyAudio para audio-reactive..."
"${SCRIPT_DIR}/venv/bin/pip" install pyaudio || echo "Aviso: Falha ao instalar pyaudio. Audio-reactive nao funcionara."

echo "   -> Instalando Sphinx para documentacao..."
"${SCRIPT_DIR}/venv/bin/pip" install --ignore-installed sphinx sphinx_rtd_theme 2>&1 | grep -v "Not uninstalling" | grep -v "Can't uninstall" || true

echo "   -> Instalando pytest para testes..."
"${SCRIPT_DIR}/venv/bin/pip" install pytest pytest-cov coverage || echo "Aviso: Falha ao instalar pytest."

echo "[5/8] Preparando os altares (data_input, data_output, .cache, logs, models)..."
mkdir -p "${SCRIPT_DIR}/data_input" || echo "Aviso: Falha ao criar data_input."
mkdir -p "${SCRIPT_DIR}/data_output" || echo "Aviso: Falha ao criar data_output."
mkdir -p "${SCRIPT_DIR}/.cache" || echo "Aviso: Falha ao criar .cache (para atlas Braille)."
mkdir -p "${SCRIPT_DIR}/logs" || echo "Aviso: Falha ao criar logs."
mkdir -p "${SCRIPT_DIR}/assets/models" || echo "Aviso: Falha ao criar assets/models."

MODEL_URL="https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"
MODEL_PATH="${SCRIPT_DIR}/assets/models/selfie_segmenter.tflite"
if [ ! -f "${MODEL_PATH}" ]; then
    echo "   -> Baixando modelo de segmentacao automatica..."
    curl -L -o "${MODEL_PATH}" "${MODEL_URL}" || echo "Aviso: Falha ao baixar modelo. Auto Seg nao funcionara."
else
    echo "   -> Modelo de segmentacao ja existe."
fi

echo "[6/8] Consagrando o icone em ${ICON_INSTALL_DIR}..."
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

echo "[7/8] Forjando o sigilo de invocacao (${DESKTOP_FILE_PATH})..."
$SUDO_CMD mkdir -p "${INSTALL_DIR}"

PYTHON_VENV_PATH="${SCRIPT_DIR}/venv/bin/python3"
MAIN_SCRIPT_PATH="${SCRIPT_DIR}/main.py"
EXEC_COMMAND="\"${PYTHON_VENV_PATH}\" \"${MAIN_SCRIPT_PATH}\""

CATEGORIES="Video;AudioVideo;"

$SUDO_CMD printf "[Desktop Entry]\nVersion=1.0\nName=%s\nComment=Conversor de Videos e Imagens para Arte ASCII v2.3.1\nExec=%s\nIcon=%s\nTerminal=false\nType=Application\nCategories=%s\nStartupNotify=true\nStartupWMClass=%s\nPath=%s\n" \
    "${APP_DISPLAY_NAME}" \
    "${EXEC_COMMAND}" \
    "${ICON_NAME}" \
    "${CATEGORIES}" \
    "${APP_NAME}" \
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

echo "[8/8] Verificacao final..."
if [ -f "${DESKTOP_FILE_PATH}" ] && [ -f "${ICON_INSTALL_PATH}" ] && [ -d "${SCRIPT_DIR}/venv" ]; then
    echo "   -> Todos os componentes instalados com sucesso."
else
    echo "   -> AVISO: Alguns componentes podem nao ter sido instalados corretamente."
    [ ! -f "${DESKTOP_FILE_PATH}" ] && echo "      - Falta: ${DESKTOP_FILE_PATH}"
    [ ! -f "${ICON_INSTALL_PATH}" ] && echo "      - Falta: ${ICON_INSTALL_PATH}"
    [ ! -d "${SCRIPT_DIR}/venv" ] && echo "      - Falta: ${SCRIPT_DIR}/venv"
fi

echo "=== Ritual Concluido ==="
echo "Voce agora pode encontrar '${APP_DISPLAY_NAME}' no seu menu de aplicativos."
echo "Para invocar manualmente, navegue ate '${SCRIPT_DIR}' e execute:"
echo "  source venv/bin/activate"
echo "  python3 main.py          # GUI GTK"
echo "  python cli.py info       # CLI headless (diagnostico)"
echo "  python cli.py --help     # CLI ajuda completa"
