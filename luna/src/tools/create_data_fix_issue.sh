#!/bin/bash
# src/tools/create_data_fix_issue.sh
# Cria issue para corrigir dados pessoais hardcoded

set -e

gh issue create \
    --title "[TEST] Corrigir dados pessoais hardcoded e assert fraco" \
    --body "## Problema
A validação detectou dados pessoais hardcoded e 1 assert fraco.

## Violações encontradas

### 1. Nomes próprios em test_visao.py (11 ocorrências)
Linhas: 212, 219, 232, 235, 467, 483, 495, 507, 524, 547, 558

\`\`\`python
# ERRADO (atual)
pessoas = [{\"nome\": \"Andre\"}]
result = visao.registrar_rosto_imediato(\"Andre\")

# CORRETO
from conftest import TEST_USER
pessoas = [{\"nome\": TEST_USER}]
result = visao.registrar_rosto_imediato(TEST_USER)
\`\`\`

### 2. Nomes em test_emotional_state.py (linha 264)
\`\`\`python
# Substituir nome hardcoded por TEST_USER ou fixture
\`\`\`

### 3. Nomes em test_context_builder.py (linha 34)
\`\`\`python
# Substituir nome hardcoded por TEST_USER ou fixture
\`\`\`

### 4. Assert fraco em test_visao.py:602
\`\`\`python
# ERRADO
def test_handles_none():
    ...
    assert True  # Não valida nada

# CORRETO
def test_handles_none():
    result = visao.method(None)
    assert result is None, 'Deve retornar None para input None'
\`\`\`

### 5. Lint em conftest.py
\`\`\`bash
ruff check src/tests/conftest.py --fix
\`\`\`

## Constantes disponíveis em conftest.py
\`\`\`python
TEST_USER = \"test_user\"
TEST_USER_ID = \"user_001\"
TEST_EMAIL = \"test@example.com\"
TEST_ENTITY = \"luna\"
\`\`\`

## Fixtures disponíveis
\`\`\`python
@pytest.fixture
def test_user():
    return \"test_user\"

@pytest.fixture
def user_profile():
    return {\"name\": \"test_user\", ...}
\`\`\`

## Critérios de aceite
- [ ] 0 ocorrências de \"Andre\" em testes
- [ ] 0 asserts fracos (assert True)
- [ ] \`./src/tools/check_test_data.sh\` passa
- [ ] \`./src/tools/check_test_quality.sh\` passa
- [ ] \`ruff check src/\` retorna 0 erros

## Validação
\`\`\`bash
./src/tools/validate_all.sh
\`\`\`

## Arquivos a modificar
- src/tests/test_visao.py
- src/tests/test_emotional_state.py
- src/tests/test_context_builder.py
- src/tests/conftest.py (lint)" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "✓ Issue criada"
echo ""
echo "Ver: gh issue list --label ai-task --state open"
