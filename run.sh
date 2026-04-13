#!/bin/bash
# Extase em 4R73 - Lancador com limpeza de cache
# "A clareza exige que se remova o que obscurece." - Epiteto

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Limpar caches Python
find "${SCRIPT_DIR}" -type d -name "__pycache__" -not -path "*/venv/*" -exec rm -rf {} + 2>/dev/null
find "${SCRIPT_DIR}" -type f -name "*.pyc" -not -path "*/venv/*" -delete 2>/dev/null
find "${SCRIPT_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find "${SCRIPT_DIR}" -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null

# Limpar cache da aplicacao
rm -rf "${HOME}/.cache/extase-em-4r73" 2>/dev/null
rm -rf "${SCRIPT_DIR}/.cache" 2>/dev/null

# Ativar venv e executar
if [ -f "${SCRIPT_DIR}/venv/bin/activate" ]; then
    source "${SCRIPT_DIR}/venv/bin/activate"
    exec python3 "${SCRIPT_DIR}/main.py" "$@"
else
    echo "Erro: venv nao encontrado. Execute install.sh primeiro."
    exit 1
fi
