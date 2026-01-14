#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_ID="com.github.andrebfarias.extase-em-4r73"

echo "=== Construindo Flatpak para ${APP_ID} ==="

if ! command -v flatpak-builder &> /dev/null; then
    echo "ERRO: flatpak-builder nao encontrado."
    echo "Instale com: sudo apt install flatpak-builder"
    exit 1
fi

echo "[1/3] Adicionando repositorio Flathub..."
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

echo "[2/3] Instalando SDK..."
flatpak install -y flathub org.gnome.Platform//45 org.gnome.Sdk//45 || true

echo "[3/3] Construindo flatpak..."
cd "${SCRIPT_DIR}"
flatpak-builder --force-clean --user --install-deps-from=flathub --repo=repo build-dir "${APP_ID}.yml"

echo "=== Build concluido ==="
echo ""
echo "Para instalar localmente:"
echo "  flatpak-builder --user --install --force-clean build-dir ${APP_ID}.yml"
echo ""
echo "Para criar bundle (.flatpak):"
echo "  flatpak build-bundle repo ${APP_ID}.flatpak ${APP_ID}"
