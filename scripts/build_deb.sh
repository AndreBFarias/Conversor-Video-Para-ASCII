#!/bin/bash
set -e

VERSION="1.0.0"
ARCH="amd64"
PKG_NAME="extase-em-4r73_${VERSION}_${ARCH}"
BUILD_DIR="$(pwd)/build_deb"

echo "=== Building Extase em 4R73 .deb package ==="
echo "Version: $VERSION"
echo "Architecture: $ARCH"
echo ""

rm -rf "$BUILD_DIR" "$PKG_NAME.deb"

mkdir -p "${BUILD_DIR}/${PKG_NAME}/DEBIAN"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/usr/bin"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/usr/share/applications"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73"

echo "[1/7] Copiando arquivos do projeto..."
cp -r src main.py config.ini requirements.txt LICENSE "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/"

echo "[2/7] Copiando assets..."
if [ -f "assets/icon.png" ]; then
    cp assets/icon.png "${BUILD_DIR}/${PKG_NAME}/usr/share/icons/hicolor/256x256/apps/extase-em-4r73.png"
else
    echo "AVISO: assets/icon.png nao encontrado"
fi

if [ -f "assets/logo.png" ]; then
    cp assets/logo.png "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/assets/"
else
    mkdir -p "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/assets"
fi

echo "[3/7] Criando desktop entry..."
cp extase-em-4r73.desktop "${BUILD_DIR}/${PKG_NAME}/usr/share/applications/"

echo "[4/7] Criando wrapper script..."
cat > "${BUILD_DIR}/${PKG_NAME}/usr/bin/extase-em-4r73" << 'EOF'
#!/bin/bash
cd /opt/extase-em-4r73
exec python3 main.py "$@"
EOF
chmod +x "${BUILD_DIR}/${PKG_NAME}/usr/bin/extase-em-4r73"

echo "[5/7] Copiando metadados DEBIAN..."
cp debian/control "${BUILD_DIR}/${PKG_NAME}/DEBIAN/"
cp debian/postinst "${BUILD_DIR}/${PKG_NAME}/DEBIAN/"
cp debian/prerm "${BUILD_DIR}/${PKG_NAME}/DEBIAN/"
chmod 755 "${BUILD_DIR}/${PKG_NAME}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/${PKG_NAME}/DEBIAN/prerm"

echo "[6/7] Criando pastas de dados..."
mkdir -p "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/data_input"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/data_output"
mkdir -p "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/logs"
touch "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/data_input/.gitkeep"
touch "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/data_output/.gitkeep"
touch "${BUILD_DIR}/${PKG_NAME}/opt/extase-em-4r73/logs/.gitkeep"

echo "[7/7] Construindo pacote .deb..."
dpkg-deb --build "${BUILD_DIR}/${PKG_NAME}"
mv "${BUILD_DIR}/${PKG_NAME}.deb" .

rm -rf "$BUILD_DIR"

echo ""
echo "=== Build concluido! ==="
echo "Pacote criado: ${PKG_NAME}.deb"
echo ""
echo "Para instalar:"
echo "  sudo dpkg -i ${PKG_NAME}.deb"
echo "  sudo apt-get install -f"
echo ""
echo "Para testar:"
echo "  dpkg-deb --info ${PKG_NAME}.deb"
echo "  dpkg-deb --contents ${PKG_NAME}.deb"
