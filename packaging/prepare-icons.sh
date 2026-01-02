#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ASSETS_DIR="$PROJECT_ROOT/assets"

SOURCE_ICON="$ASSETS_DIR/logo.png"

if [ ! -f "$SOURCE_ICON" ]; then
    echo "Error: $SOURCE_ICON not found"
    exit 1
fi

echo "Preparing icons from $SOURCE_ICON..."

convert "$SOURCE_ICON" -resize 64x64 "$ASSETS_DIR/logo-64.png"
echo "Created logo-64.png (64x64)"

convert "$SOURCE_ICON" -resize 128x128 "$ASSETS_DIR/logo-128.png"
echo "Created logo-128.png (128x128)"

convert "$SOURCE_ICON" -resize 512x512 "$ASSETS_DIR/logo-512.png"
echo "Created logo-512.png (512x512)"

echo "Icons prepared successfully"
