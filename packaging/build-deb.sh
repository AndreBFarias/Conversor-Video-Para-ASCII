#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="2.1.0"
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
cp "${SCRIPT_DIR}/deb/DEBIAN/control" "${DEB_ROOT}/DEBIAN/"
cp "${SCRIPT_DIR}/deb/DEBIAN/postinst" "${DEB_ROOT}/DEBIAN/"
cp "${SCRIPT_DIR}/deb/DEBIAN/postrm" "${DEB_ROOT}/DEBIAN/"
chmod 755 "${DEB_ROOT}/DEBIAN/postinst"
chmod 755 "${DEB_ROOT}/DEBIAN/postrm"

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

echo "[4/5] Criando arquivo .desktop..."
cat > "${DEB_ROOT}/usr/share/applications/${PACKAGE_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.1
Name=Extase em 4R73
Comment=Conversor de Videos e Imagens para Arte ASCII
Exec=/opt/${PACKAGE_NAME}/venv/bin/python3 /opt/${PACKAGE_NAME}/main.py
Icon=${PACKAGE_NAME}
Terminal=false
Type=Application
Categories=Video;AudioVideo;
StartupNotify=true
StartupWMClass=${PACKAGE_NAME}
Path=/opt/${PACKAGE_NAME}
EOF

echo "[5/5] Criando wrapper script..."
cat > "${DEB_ROOT}/usr/bin/${PACKAGE_NAME}" << EOF
#!/bin/bash
cd /opt/${PACKAGE_NAME}
exec ./venv/bin/python3 main.py "\$@"
EOF
chmod 755 "${DEB_ROOT}/usr/bin/${PACKAGE_NAME}"

echo "Construindo pacote .deb..."
dpkg-deb --build "${DEB_ROOT}"

mv "${DEB_ROOT}.deb" "${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"

echo "=== Pacote criado: ${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb ==="

rm -rf "${BUILD_DIR}"

echo "Para instalar: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_all.deb"
echo "Para resolver dependencias: sudo apt-get install -f"
