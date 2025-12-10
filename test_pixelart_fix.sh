#!/bin/bash
# Script de teste rápido - Apenas para verificar se o app abre sem erros

echo "=== Teste Rápido - Conversão Pixel Art ==="
echo ""
echo "IMPORTANTE: Execute este script APÓS o install.sh terminar!"
echo ""

cd /home/vitoriamaria/Desenvolvimento/Conversor-Video-Para-ASCII

if [ ! -d "venv" ]; then
    echo "❌ ERRO: venv não existe! Execute ./install.sh primeiro."
    exit 1
fi

source venv/bin/activate

echo "✓ Ambiente virtual ativado"
echo ""
echo "Testando se o aplicativo abre sem erros..."
echo "NOTA: Feche o aplicativo (Ctrl+C) após verificar que ele abriu."
echo ""
echo "Se você NÃO ver os erros:"
echo "  - 'Window' object has no attribute 'get_content_area'"
echo "  - 'NoneType' object has no attribute 'set_active'"
echo ""
echo "Então o bug foi CORRIGIDO! ✅"
echo ""
echo "Pressione Enter para continuar..."
read

python3 main.py
