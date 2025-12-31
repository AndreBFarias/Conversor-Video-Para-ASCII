#!/bin/bash
# Verifica documentacao de novos scripts
# Pula arquivos em pacotes modularizados (herdam cobertura do wrapper)

ERRORS=0
WARNINGS=0

# Pacotes modularizados que herdam testes do wrapper
MODULARIZED_PACKAGES=(
    "src/soul/boca"
    "src/soul/consciencia"
    "src/soul/visao"
    "src/soul/threading_manager"
    "src/soul/audio_threads"
    "src/soul/user_profiler"
    "src/soul/live_session"
    "src/soul/onboarding"
    "src/core/animation"
    "src/core/profiler"
    "src/core/ollama_client"
    "src/core/metricas"
    "src/core/desktop_integration"
    "src/data_memory/smart_memory"
    "src/ui/dashboard"
    "src/ui/theme_manager"
    "src/ui/banner"
    "src/ui/screens"
)

is_modularized_submodule() {
    local file="$1"
    local dir=$(dirname "$file")
    for pkg in "${MODULARIZED_PACKAGES[@]}"; do
        if [[ "$dir" == "$pkg" || "$dir" == "$pkg"/* ]]; then
            return 0
        fi
    done
    return 1
}

echo "Verificando documentacao de novos scripts..."

NEW_FILES=$(git diff --cached --name-only --diff-filter=A | grep -E '^src/.*\.py$' | grep -v '__init__.py' | grep -v '/tests/')

if [[ -z "$NEW_FILES" ]]; then
    echo "OK: Nenhum novo script detectado"
    exit 0
fi

STAGED_CONTENT=$(git diff --cached)

for file in $NEW_FILES; do
    # Pular submodulos de pacotes modularizados
    if is_modularized_submodule "$file"; then
        continue
    fi

    filename=$(basename "$file" .py)

    if echo "$STAGED_CONTENT" | grep -qiE "(closes|fixes|ref|issue).*#[0-9]+"; then
        echo "OK: Issue referenciada no commit para $file"
    else
        echo "AVISO: $file criado sem referencia a issue (#XX)"
        echo "  -> Crie uma issue ou adicione 'Closes #XX' ao commit"
        WARNINGS=$((WARNINGS + 1))
    fi

    changelog_files=$(git diff --cached --name-only | grep -iE 'changelog|session.*summary')
    if [[ -n "$changelog_files" ]]; then
        echo "OK: Changelog atualizado para $file"
    else
        echo "AVISO: $file criado sem atualizacao no CHANGELOG"
        echo "  -> Documente a mudanca em dev-journey/03-changelog/"
        WARNINGS=$((WARNINGS + 1))
    fi

    test_file="src/tests/test_${filename}.py"
    if git diff --cached --name-only | grep -q "$test_file"; then
        echo "OK: Teste criado para $file"
    elif [[ -f "$test_file" ]]; then
        echo "OK: Teste ja existe para $file"
    else
        echo "ERRO: $file criado sem teste correspondente"
        echo "  -> Crie $test_file com testes unitarios"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "FALHA: $ERRORS erro(s) encontrado(s)"
    echo "Novos scripts precisam de testes correspondentes."
    exit 1
fi

if [[ $WARNINGS -gt 0 ]]; then
    echo "AVISO: $WARNINGS aviso(s) - considere adicionar issues e changelog"
fi

echo "OK: Novos scripts documentados adequadamente"
exit 0
