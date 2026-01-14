#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-2.1.0}"
PACKAGE_NAME="extase-em-4r73"
BUILD_DIR="${SCRIPT_DIR}/build"
DEB_ROOT="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}"

echo "=== Construindo pacote .deb para ${PACKAGE_NAME} v${VERSION} ==="

rm -rf "${BUILD_DIR}"
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/opt/${PACKAGE_NAME}"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/icons/hicolor/64x64/apps"
mkdir -p "${DEB_ROOT}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${DEB_ROOT}/usr/bin"

echo "[1/5] Copiando arquivos de controle..."
cp "${PROJECT_DIR}/debian/control" "${DEB_ROOT}/DEBIAN/"
cp "${PROJECT_DIR}/debian/postinst" "${DEB_ROOT}/DEBIAN/"
# Check if postrm exists before copying
if [ -f "${PROJECT_DIR}/debian/postrm" ]; then
    cp "${PROJECT_DIR}/debian/postrm" "${DEB_ROOT}/DEBIAN/"
    chmod 755 "${DEB_ROOT}/DEBIAN/postrm"
fi

if [ -f "${PROJECT_DIR}/debian/prerm" ]; then
    cp "${PROJECT_DIR}/debian/prerm" "${DEB_ROOT}/DEBIAN/"
    chmod 755 "${DEB_ROOT}/DEBIAN/prerm"
fi

chmod 755 "${DEB_ROOT}/DEBIAN/postinst"

# Update version in control file
sed -i "s/^Version: .*/Version: ${VERSION}/" "${DEB_ROOT}/DEBIAN/control"

echo "[2/5] Copiando codigo fonte..."
cp -r "${PROJECT_DIR}/src" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/main.py" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/config.ini" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"
cp "${PROJECT_DIR}/requirements.txt" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"
cp -r "${PROJECT_DIR}/assets" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"

if [ -d "${PROJECT_DIR}/docs" ]; then
    cp -r "${PROJECT_DIR}/docs" "${DEB_ROOT}/opt/${PACKAGE_NAME}/"
fi

echo "[3/5] Instalando icones..."
if command -v convert &> /dev/null; then
    convert "${PROJECT_DIR}/assets/logo.png" -resize 64x64 "${DEB_ROOT}/usr/share/icons/hicolor/64x64/apps/${PACKAGE_NAME}.png"
    convert "${PROJECT_DIR}/assets/logo.png" -resize 128x128 "${DEB_ROOT}/usr/share/icons/hicolor/128x128/apps/${PACKAGE_NAME}.png"
else
    cp "${PROJECT_DIR}/assets/logo.png" "${DEB_ROOT}/usr/share/icons/hicolor/64x64/apps/${PACKAGE_NAME}.png"
fi

echo "[4/5] Instalando arquivo .desktop..."
cp "${PROJECT_DIR}/debian/extase-em-4r73.desktop" "${DEB_ROOT}/usr/share/applications/${PACKAGE_NAME}.desktop"

echo "[5/5] Criando wrapper script..."
cat > "${DEB_ROOT}/usr/bin/${PACKAGE_NAME}" << 'WRAPPER_EOF'
#!/bin/bash
INSTALL_DIR="/opt/extase-em-4r73"
LOG_FILE="/tmp/extase-em-4r73.log"

show_error() {
    echo "$1" | tee -a "$LOG_FILE"
    if command -v zenity &> /dev/null; then
        zenity --error --title="Extase em 4R73" --text="$1" 2>/dev/null &
    elif command -v notify-send &> /dev/null; then
        notify-send "Extase em 4R73" "$1" 2>/dev/null &
    fi
}

if [ ! -d "$INSTALL_DIR" ]; then
    show_error "Diretorio de instalacao nao encontrado: $INSTALL_DIR\nReinstale o pacote: sudo apt reinstall extase-em-4r73"
    exit 1
fi

cd "$INSTALL_DIR"

# CUDA libs do DaVinci Resolve (se disponivel)
if [ -d "/opt/resolve/libs" ]; then
    export LD_LIBRARY_PATH="/opt/resolve/libs:$LD_LIBRARY_PATH"
fi

if [ ! -d "venv" ] || [ ! -f "venv/bin/python3" ]; then
    show_error "Ambiente virtual nao encontrado.\nExecutando configuracao inicial..."

    if [ -f "/var/lib/dpkg/info/extase-em-4r73.postinst" ]; then
        pkexec /var/lib/dpkg/info/extase-em-4r73.postinst configure 2>> "$LOG_FILE"
    else
        show_error "Falha na configuracao. Reinstale: sudo apt reinstall extase-em-4r73"
        exit 1
    fi

    if [ ! -d "venv" ]; then
        show_error "Falha ao criar ambiente virtual. Verifique: $LOG_FILE"
        exit 1
    fi
fi

exec ./venv/bin/python3 main.py "$@" 2>&1 | tee -a "$LOG_FILE"
WRAPPER_EOF
chmod 755 "${DEB_ROOT}/usr/bin/${PACKAGE_NAME}"

echo "Construindo pacote .deb..."
dpkg-deb --build "${DEB_ROOT}"

mv "${DEB_ROOT}.deb" "${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"

echo "=== Pacote criado: ${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb ==="

rm -rf "${BUILD_DIR}"

echo "Para instalar: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_all.deb"
echo "Para resolver dependencias: sudo apt-get install -f"
