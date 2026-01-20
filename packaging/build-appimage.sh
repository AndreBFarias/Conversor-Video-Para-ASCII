#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-2.3.1}"
PACKAGE_NAME="extase-em-4r73"
APP_DIR="${SCRIPT_DIR}/AppDir"
OUTPUT_NAME="Extase_em_4R73-${VERSION}-x86_64.AppImage"

echo "=== Construindo AppImage para ${PACKAGE_NAME} v${VERSION} ==="

LINUXDEPLOY="${SCRIPT_DIR}/linuxdeploy-x86_64.AppImage"
if [ ! -f "$LINUXDEPLOY" ]; then
    echo "Baixando linuxdeploy..."
    curl -L -o "$LINUXDEPLOY" "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
    chmod +x "$LINUXDEPLOY"
fi

rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APP_DIR}/opt/${PACKAGE_NAME}"

echo "[1/6] Copiando codigo fonte..."
cp -r "${PROJECT_DIR}/src" "${APP_DIR}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/main.py" "${APP_DIR}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/config.ini" "${APP_DIR}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/requirements.txt" "${APP_DIR}/opt/${PACKAGE_NAME}/"
cp -r "${PROJECT_DIR}/assets" "${APP_DIR}/opt/${PACKAGE_NAME}/"

if [ -d "${PROJECT_DIR}/docs" ]; then
    cp -r "${PROJECT_DIR}/docs" "${APP_DIR}/opt/${PACKAGE_NAME}/"
fi

echo "[2/6] Criando ambiente virtual embarcado..."
python3 -m venv --system-site-packages "${APP_DIR}/opt/${PACKAGE_NAME}/venv"
"${APP_DIR}/opt/${PACKAGE_NAME}/venv/bin/pip" install --upgrade pip setuptools wheel
"${APP_DIR}/opt/${PACKAGE_NAME}/venv/bin/pip" install opencv-python numpy Pillow

if command -v nvidia-smi &> /dev/null; then
    echo "   -> Instalando suporte GPU (cupy-cuda12x)..."
    "${APP_DIR}/opt/${PACKAGE_NAME}/venv/bin/pip" install cupy-cuda12x 2>/dev/null || echo "   -> cupy-cuda12x falhou, continuando..."
fi

echo "   -> Instalando mediapipe e pyaudio..."
"${APP_DIR}/opt/${PACKAGE_NAME}/venv/bin/pip" install mediapipe 2>/dev/null || echo "   -> mediapipe falhou, continuando..."
"${APP_DIR}/opt/${PACKAGE_NAME}/venv/bin/pip" install pyaudio 2>/dev/null || echo "   -> pyaudio falhou, continuando..."

echo "[3/6] Instalando icone..."
if command -v convert &> /dev/null; then
    convert "${PROJECT_DIR}/assets/logo.png" -resize 256x256 "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${PACKAGE_NAME}.png"
else
    cp "${PROJECT_DIR}/assets/logo.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${PACKAGE_NAME}.png"
fi
cp "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${PACKAGE_NAME}.png" "${APP_DIR}/${PACKAGE_NAME}.png"

echo "[4/6] Criando arquivo .desktop..."
cat > "${APP_DIR}/usr/share/applications/${PACKAGE_NAME}.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.1
Name=Extase em 4R73
Comment=Conversor de Videos para Arte ASCII
Exec=${PACKAGE_NAME}
Icon=${PACKAGE_NAME}
Terminal=false
Type=Application
Categories=Video;AudioVideo;
StartupNotify=true
DESKTOP_EOF

cp "${APP_DIR}/usr/share/applications/${PACKAGE_NAME}.desktop" "${APP_DIR}/${PACKAGE_NAME}.desktop"

echo "[5/6] Criando AppRun..."
cat > "${APP_DIR}/AppRun" << 'APPRUN_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/opt/extase-em-4r73/venv/bin:${PATH}"
export PYTHONPATH="${HERE}/opt/extase-em-4r73:${PYTHONPATH}"

if [ -d "/opt/resolve/libs" ]; then
    export LD_LIBRARY_PATH="/opt/resolve/libs:$LD_LIBRARY_PATH"
fi

cd "${HERE}/opt/extase-em-4r73"
exec "${HERE}/opt/extase-em-4r73/venv/bin/python3" main.py "$@"
APPRUN_EOF
chmod +x "${APP_DIR}/AppRun"

echo "[6/6] Gerando AppImage..."
ARCH=x86_64 "$LINUXDEPLOY" --appdir="${APP_DIR}" --output appimage

if [ -f "${SCRIPT_DIR}/${PACKAGE_NAME}-x86_64.AppImage" ]; then
    mv "${SCRIPT_DIR}/${PACKAGE_NAME}-x86_64.AppImage" "${SCRIPT_DIR}/${OUTPUT_NAME}"
elif [ -f "${SCRIPT_DIR}/Extase_em_4R73-x86_64.AppImage" ]; then
    mv "${SCRIPT_DIR}/Extase_em_4R73-x86_64.AppImage" "${SCRIPT_DIR}/${OUTPUT_NAME}"
fi

rm -rf "${APP_DIR}"

echo "=== AppImage criado: ${SCRIPT_DIR}/${OUTPUT_NAME} ==="
echo "Para executar: chmod +x ${OUTPUT_NAME} && ./${OUTPUT_NAME}"
