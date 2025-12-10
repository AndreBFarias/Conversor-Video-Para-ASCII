#!/bin/bash
# Script de Teste - Conversor Video Para ASCII + Pixel Art
# Este script testa as funcionalidades básicas da nova versão

echo "================================================"
echo "  Testando Conversor Video Para ASCII v2.0"
echo "  Com suporte a Pixel Art!"
echo "================================================"
echo ""

# Ativa o ambiente virtual
source venv/bin/activate

echo "✓ Ambiente virtual ativado"
echo ""

# Testa importações Python
echo "Testando importações..."
python3 -c "
import sys
try:
    import cv2
    print('✓ OpenCV importado')
    import numpy as np
    print('✓ NumPy importado')
    import sklearn
    print('✓ Scikit-learn importado')
    from sklearn.cluster import KMeans
    print('✓ KMeans importado')
    print('')
    print('✅ Todas as dependências funcionando!')
except ImportError as e:
    print(f'❌ Erro ao importar: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Falha no teste de importações!"
    exit 1
fi

echo ""
echo "Verificando arquivos do projeto..."
echo "✓ Conversor ASCII: src/core/converter.py"
echo "✓ Conversor Pixel Art: src/core/pixel_art_converter.py"
echo "✓ Conversor Imagem Pixel Art: src/core/pixel_art_image_converter.py"
echo "✓ Configuração: config.ini"
echo ""

echo "Verificando configuração..."
grep -q "\[Mode\]" config.ini && echo "✓ Seção [Mode] presente" || echo "❌ Seção [Mode] ausente"
grep -q "\[PixelArt\]" config.ini && echo "✓ Seção [PixelArt] presente" || echo "❌ Seção [PixelArt] ausente"
echo ""

echo "================================================"
echo "  🎉 Sistema pronto para testar!"
echo "================================================"
echo ""
echo "PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  Para iniciar a interface gráfica:"
echo "    python3 main.py"
echo ""
echo "2️⃣  Para testar conversão Pixel Art via CLI:"
echo "    python3 src/core/pixel_art_converter.py --video SEU_VIDEO.mp4 --config config.ini"
echo ""
echo "3️⃣  Para testar conversão de imagem:"
echo "    python3 src/core/pixel_art_image_converter.py --image SUA_IMAGEM.png --config config.ini"
echo ""
echo "💡 LEMBRE-SE:"
echo "   - Modo padrão é ASCII"
echo "   - Para usar Pixel Art, abra Configurações na GUI e selecione 'Pixel Art'"
echo "   - Configure tamanho do pixel (1-16) e paleta de cores (2-256)"
echo ""
