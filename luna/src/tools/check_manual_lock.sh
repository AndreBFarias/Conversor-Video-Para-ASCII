#!/bin/bash
set -e

VIOLATIONS=$(grep -rn '\.acquire()' src/ --include="*.py" 2>/dev/null | grep -v test | grep -v __pycache__ || true)

if [ -n "$VIOLATIONS" ]; then
    echo "ERRO: Uso manual de .acquire() encontrado"
    echo "Use 'with lock:' em vez de lock.acquire()/release()"
    echo ""
    echo "Violacoes:"
    echo "$VIOLATIONS"
    exit 1
fi

exit 0
