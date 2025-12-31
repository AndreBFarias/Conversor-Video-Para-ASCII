#!/bin/bash
# Hook pre-commit para detectar except: bare (silenciosos)

set -e

# Busca except: bare (sem tratamento)
VIOLATIONS=$(grep -rn 'except:\s*$' src/ --include="*.py" 2>/dev/null | grep -v test | grep -v __pycache__ || true)

if [ -n "$VIOLATIONS" ]; then
    echo "ERRO: except: bare encontrado (use 'except Exception as e:' com logging)"
    echo ""
    echo "$VIOLATIONS"
    echo ""
    echo "Corrija usando:"
    echo "  except Exception as e:"
    echo '      logger.debug(f"Erro em [contexto]: {e}")'
    exit 1
fi

exit 0
