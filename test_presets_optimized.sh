#!/bin/bash
# Script de teste para verificar presets otimizados de Pixel Art

echo "=== Teste de Presets de Pixel Art Otimizados ==="
echo ""

CONFIG_FILE="config.ini"
BACKUP_FILE="config.ini.backup"

# Backup do config original
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✓ Backup criado: $BACKUP_FILE"

# Função para testar um preset
test_preset() {
    local preset_name=$1
    local expected_pixel_size=$2
    local expected_palette=$3
    
    echo ""
    echo "--- Testando preset: $preset_name ---"
    
    # Ativar modo Pixel Art
    sed -i 's/conversion_mode = .*/conversion_mode = pixelart/' "$CONFIG_FILE"
    
    # Aplicar preset via Python (simula seleção no combo)
    python3 -c "
import configparser
config = configparser.ConfigParser(interpolation=None)
config.read('$CONFIG_FILE')

pixelart_presets = {
    '8bit_low': {'width': 100, 'height': 25, 'pixel_size': 6, 'palette_size': 16},
    '8bit_high': {'width': 120, 'height': 30, 'pixel_size': 5, 'palette_size': 16},
    '16bit_low': {'width': 150, 'height': 38, 'pixel_size': 3, 'palette_size': 128},
    '16bit_high': {'width': 180, 'height': 45, 'pixel_size': 2, 'palette_size': 128},
    '32bit': {'width': 240, 'height': 60, 'pixel_size': 2, 'palette_size': 256},
    '64bit': {'width': 300, 'height': 75, 'pixel_size': 1, 'palette_size': 256},
}

preset = pixelart_presets['$preset_name']
config.set('Conversor', 'target_width', str(preset['width']))
config.set('Conversor', 'target_height', str(preset['height']))
config.set('PixelArt', 'pixel_size', str(preset['pixel_size']))
config.set('PixelArt', 'color_palette_size', str(preset['palette_size']))
config.set('Quality', 'preset', '$preset_name')

with open('$CONFIG_FILE', 'w') as f:
    config.write(f)

print(f'Preset {preset_name}: {preset[\"width\"]}x{preset[\"height\"]}, pixel_size={preset[\"pixel_size\"]}, {preset[\"palette_size\"]} cores')
"
    
    # Verificar se valores foram aplicados corretamente
    actual_pixel_size=$(grep "pixel_size" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    actual_palette=$(grep "color_palette_size" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    
    if [ "$actual_pixel_size" = "$expected_pixel_size" ] && [ "$actual_palette" = "$expected_palette" ]; then
        echo "  ✓ pixel_size: $actual_pixel_size (esperado: $expected_pixel_size)"
        echo "  ✓ color_palette_size: $actual_palette (esperado: $expected_palette)"
        echo "  ✓ PASSOU!"
    else
        echo "  ✗ FALHOU!"
        echo "    pixel_size: $actual_pixel_size (esperado: $expected_pixel_size)"
        echo "    color_palette_size: $actual_palette (esperado: $expected_palette)"
    fi
}

# Testar presets otimizados
test_preset "16bit_low" "3" "128"
test_preset "16bit_high" "2" "128"
test_preset "32bit" "2" "256"
test_preset "64bit" "1" "256"

echo ""
echo "=== Restaurando configuração original ==="
mv "$BACKUP_FILE" "$CONFIG_FILE"
echo "✓ Config restaurado"
echo ""
echo "=== Teste Concluído ==="
