#!/bin/bash
# src/tools/check_test_data.sh
# Detecta dados pessoais/hardcoded em testes
# Bloqueia: nomes reais, emails, paths pessoais

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== VERIFICANDO DADOS DE TESTE ==="

VIOLATIONS=0

# 1. Nomes próprios comuns hardcoded (deveria ser "test_user", "user_1", etc)
echo ""
echo "[1/4] Verificando nomes próprios hardcoded..."

NAMES_PATTERN='("Andre"|"André"|"Maria"|"João"|"Pedro"|"Lucas"|"Ana"|"Carlos"|"Paulo"|"Julia"|"user_name.*Andre")'
FOUND=$(grep -rniE "$NAMES_PATTERN" src/tests/ --include="*.py" 2>/dev/null | grep -v "# OK:" | grep -v "test_user_profiler.py" || true)

if [ -n "$FOUND" ]; then
    echo -e "${RED}Nomes próprios encontrados:${NC}"
    echo "$FOUND" | head -15
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# 2. Paths pessoais (/home/usuario, /Users/nome)
echo ""
echo "[2/4] Verificando paths pessoais..."

PATHS_PATTERN='(/home/[a-z]+/|/Users/[A-Za-z]+/|C:\\Users\\[A-Za-z]+)'
FOUND=$(grep -rniE "$PATHS_PATTERN" src/tests/ --include="*.py" 2>/dev/null | grep -v "# OK:" || true)

if [ -n "$FOUND" ]; then
    echo -e "${RED}Paths pessoais encontrados:${NC}"
    echo "$FOUND" | head -10
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# 3. Emails pessoais (deveria ser test@example.com)
echo ""
echo "[3/4] Verificando emails pessoais..."

# Emails que NÃO são de teste
FOUND=$(grep -rniE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' src/tests/ --include="*.py" 2>/dev/null | grep -viE "(example\.com|exemplo\.com|test\.com|teste\.com|localhost|mock|fake)" || true)

if [ -n "$FOUND" ]; then
    echo -e "${RED}Emails possivelmente pessoais:${NC}"
    echo "$FOUND" | head -10
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# 4. Dados que deveriam ser variáveis
echo ""
echo "[4/4] Verificando dados hardcoded que deveriam ser variáveis..."

python3 << 'PYEOF'
import re
import sys
from pathlib import Path

VIOLATIONS = []

# Padrões problemáticos
PATTERNS = [
    # Nomes próprios brasileiros comuns
    (r'["\']Andr[eé]["\']', "Nome próprio 'Andre' - use 'test_user' ou variável"),
    (r'["\']Maria["\']', "Nome próprio 'Maria' - use 'test_user' ou variável"),
    (r'["\']Jo[aã]o["\']', "Nome próprio 'João' - use 'test_user' ou variável"),
    (r'["\']Pedro["\']', "Nome próprio 'Pedro' - use 'test_user' ou variável"),
    (r'["\']Carlos["\']', "Nome próprio 'Carlos' - use 'test_user' ou variável"),
    (r'["\']Lucas["\']', "Nome próprio 'Lucas' - use 'test_user' ou variável"),

    # Dados que deveriam vir de config/fixture
    (r'registrar_rosto\s*\([^)]*["\'][A-Z][a-z]+["\']', "Nome em registrar_rosto - use variável ou fixture"),
    (r'(user_name|username|nome)\s*=\s*["\'][A-Z][a-z]{2,}["\']', "Nome de usuário hardcoded - use TEST_USER ou fixture"),
]

# Padrões permitidos (whitelist)
ALLOWED = [
    "test_user",
    "TestUser",
    "test_name",
    "mock_user",
    "fake_user",
    "user_1",
    "User1",
    "example",
    "Example",
    "sample",
    "Sample",
    "dummy",
    "Dummy",
]

EXCLUDED_FILES = [
    "test_user_profiler.py",
]

for pyfile in Path("src/tests").rglob("*.py"):
    if pyfile.name in EXCLUDED_FILES:
        continue

    try:
        content = pyfile.read_text()
        lines = content.split('\n')
    except:
        continue

    for i, line in enumerate(lines, 1):
        # Pular comentários
        if line.strip().startswith('#'):
            continue

        # Pular se tem marcador de OK
        if '# OK:' in line or '# ALLOWED' in line:
            continue

        # Pular se usa padrões permitidos
        if any(allowed in line for allowed in ALLOWED):
            continue

        for pattern, msg in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                VIOLATIONS.append(f"{pyfile.name}:{i}: {msg}")
                break

if VIOLATIONS:
    print(f"\n{len(VIOLATIONS)} dados hardcoded encontrados:")
    for v in VIOLATIONS[:20]:
        print(f"  ! {v}")
    if len(VIOLATIONS) > 20:
        print(f"  ... e mais {len(VIOLATIONS) - 20}")
    sys.exit(1)
else:
    print("  ✓ Nenhum dado pessoal hardcoded")
    sys.exit(0)
PYEOF

PYTHON_RESULT=$?
if [ $PYTHON_RESULT -ne 0 ]; then
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Resultado
echo ""
if [ $VIOLATIONS -gt 0 ]; then
    echo -e "${RED}========================================"
    echo "  DADOS PESSOAIS/HARDCODED DETECTADOS"
    echo -e "========================================${NC}"
    echo ""
    echo "Use ao invés:"
    echo '  - "test_user" ou "user_1" para nomes'
    echo '  - "test@example.com" para emails'
    echo '  - tempfile.mkdtemp() para paths'
    echo '  - Fixtures do pytest para dados reutilizáveis'
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Nenhum dado pessoal/hardcoded encontrado${NC}"
fi
