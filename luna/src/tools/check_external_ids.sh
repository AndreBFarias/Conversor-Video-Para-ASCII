#!/bin/bash
# check_external_ids.sh - Verifica identificadores de servicos externos
# Parte do sistema de compliance do projeto Luna

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

echo "Verificando identificadores externos..."

# Padroes de Voice IDs (ElevenLabs usa IDs de 20+ caracteres alfanumericos)
VOICE_ID_PATTERN='[a-zA-Z0-9]{20,}'

# Verificar Voice IDs hardcoded (exceto strings vazias e placeholders)
VOICE_IDS=$(grep -rniE "voice_id.*['\"]${VOICE_ID_PATTERN}['\"]" \
    --include="*.py" --include="*.json" --include="*.md" \
    src/ config.py 2>/dev/null | \
    grep -viE '""|\[\]|\[A_SER|\[VOZ_|voice_id.*:.*""' || true)

if [ -n "$VOICE_IDS" ]; then
    echo -e "${RED}ERRO: Voice IDs hardcoded encontrados:${NC}"
    echo "$VOICE_IDS"
    ERRORS=$((ERRORS + 1))
fi

# Verificar API keys hardcoded (padroes comuns)
API_KEYS=$(grep -rniE "(api_key|apikey|api-key)\s*[=:]\s*['\"][a-zA-Z0-9_-]{20,}['\"]" \
    --include="*.py" --include="*.json" \
    src/ 2>/dev/null | \
    grep -viE 'os\.getenv|environ|\.env|config\.' || true)

if [ -n "$API_KEYS" ]; then
    echo -e "${RED}ERRO: API keys hardcoded encontradas:${NC}"
    echo "$API_KEYS"
    ERRORS=$((ERRORS + 1))
fi

# Verificar tokens hardcoded
TOKENS=$(grep -rniE "(token|secret)\s*[=:]\s*['\"][a-zA-Z0-9_-]{30,}['\"]" \
    --include="*.py" --include="*.json" \
    src/ 2>/dev/null | \
    grep -viE 'os\.getenv|environ|\.env|config\.' || true)

if [ -n "$TOKENS" ]; then
    echo -e "${RED}ERRO: Tokens hardcoded encontrados:${NC}"
    echo "$TOKENS"
    ERRORS=$((ERRORS + 1))
fi

# Verificar design prompts de voz (descricoes de como criar vozes)
DESIGN_PROMPTS=$(grep -rniE "design_prompt.*['\"][A-Z]" \
    --include="*.py" --include="*.json" --include="*.md" \
    src/assets/panteao/ 2>/dev/null | \
    grep -viE '""' || true)

if [ -n "$DESIGN_PROMPTS" ]; then
    echo -e "${YELLOW}AVISO: Design prompts encontrados (podem ser problematicos):${NC}"
    echo "$DESIGN_PROMPTS"
fi

# Resultado final
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}OK: Nenhum identificador externo problematico encontrado${NC}"
    exit 0
else
    echo -e "${RED}FALHA: $ERRORS problema(s) encontrado(s)${NC}"
    exit 1
fi
