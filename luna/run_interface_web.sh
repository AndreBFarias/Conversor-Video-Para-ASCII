#!/bin/bash
# run_interface_web.sh - Inicia o dashboard web do Luna
# Acesse: http://localhost:8080/api/dashboard

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Erro: venv nao encontrado. Execute install.sh primeiro."
    exit 1
fi

echo "Iniciando Luna Web Dashboard..."
echo "Acesse: http://localhost:8080/api/dashboard"
echo ""

./venv/bin/python -m src.web.server
