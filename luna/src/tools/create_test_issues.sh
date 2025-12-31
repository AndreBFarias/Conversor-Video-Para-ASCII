#!/bin/bash
# src/tools/create_test_issues.sh
# Cria issues no GitHub para correção de testes

set -e

echo "=== CRIANDO ISSUES PARA CORREÇÃO DE TESTES ==="
echo ""

# ============================================
# GRUPO 1: TESTES SEM ASSERT (FAKE)
# ============================================

echo "[1/4] Criando issues para testes sem assert..."

# test_ui_integrity.py
gh issue create \
    --title "[TEST] Corrigir testes sem assert em test_ui_integrity.py" \
    --body "## Problema
8 funções de teste não têm assert, apenas importam módulos.

## Funções afetadas
- \`test_glitch_button_import()\` linha 129
- \`test_personality_module_import()\` linha 184
- \`test_banner_module_import()\` linha 211
- \`test_widgets_module_import()\` linha 217
- \`test_screens_module_import()\` linha 223
- \`test_animation_controller_import()\` linha 229
- \`test_theme_manager_import()\` linha 234
- \`test_entity_selector_import()\` linha 240

## O que fazer
Cada teste deve validar ALGO real, não apenas importar. Exemplos:

\`\`\`python
# ERRADO (atual)
def test_banner_module_import():
    from src.ui.banner import Banner
    # Sem assert = não testa nada

# CORRETO
def test_banner_module_import():
    from src.ui.banner import Banner
    assert hasattr(Banner, 'render'), 'Banner deve ter método render'
    assert callable(getattr(Banner, '__init__', None)), 'Banner deve ser instanciável'
\`\`\`

## Critérios de aceite
- [ ] Todos os 8 testes têm pelo menos 1 assert real
- [ ] Asserts validam comportamento, não apenas existência
- [ ] Testes falham se o código quebrar

## Arquivo
\`src/tests/test_ui_integrity.py\`" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: test_ui_integrity.py"

# test_response_pipeline.py
gh issue create \
    --title "[TEST] Corrigir testes sem assert em test_response_pipeline.py" \
    --body "## Problema
3 funções de teste não têm assert.

## Funções afetadas
- \`test_run_hooks_calls_all()\` linha 154
- \`test_run_hooks_handles_error()\` linha 168
- \`test_process_calls_hooks()\` linha 232

## O que fazer
\`\`\`python
# ERRADO
def test_run_hooks_calls_all():
    pipeline = ResponsePipeline()
    pipeline.run_hooks(data)
    # Sem assert

# CORRETO
def test_run_hooks_calls_all():
    pipeline = ResponsePipeline()
    mock_hook = Mock()
    pipeline.register_hook(mock_hook)
    pipeline.run_hooks(data)
    mock_hook.assert_called_once_with(data)
\`\`\`

## Critérios de aceite
- [ ] 3 testes com asserts reais
- [ ] Usar mocks para verificar chamadas
- [ ] Testar caso de erro também

## Arquivo
\`src/tests/test_response_pipeline.py\`" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: test_response_pipeline.py"

# test_new_features.py
gh issue create \
    --title "[TEST] Corrigir testes sem assert em test_new_features.py" \
    --body "## Problema
4 funções de teste não têm assert.

## Funções afetadas
- \`test_optimized_vector_store()\` linha 29
- \`test_smart_memory()\` linha 95
- \`test_terminal_executor()\` linha 151
- \`test_session_history()\` linha 212

## O que fazer
\`\`\`python
# ERRADO
def test_smart_memory():
    memory = SmartMemory()
    memory.add('teste')
    # Sem assert

# CORRETO
def test_smart_memory():
    memory = SmartMemory()
    memory.add('teste', category='fact')
    results = memory.retrieve('teste')
    assert len(results) > 0, 'Deve retornar resultado'
    assert 'teste' in results[0], 'Deve conter o texto adicionado'
\`\`\`

## Critérios de aceite
- [ ] 4 testes com asserts reais
- [ ] Testar input → output
- [ ] Testar casos de borda (None, vazio)

## Arquivo
\`src/tests/test_new_features.py\`" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: test_new_features.py"

# Outros testes sem assert (agrupado)
gh issue create \
    --title "[TEST] Corrigir demais testes sem assert (34 funções)" \
    --body "## Problema
34 funções de teste adicionais não têm assert.

## Arquivos afetados
Rodar para listar:
\`\`\`bash
./src/tools/check_test_quality.sh
\`\`\`

## O que fazer
1. Identificar cada função sem assert
2. Entender o que deveria testar
3. Adicionar asserts que validam comportamento real

## Regras
- PROIBIDO: \`assert True\`, \`assert 1\`, \`pass\`
- OBRIGATÓRIO: Assert que falha se código quebrar

## Critérios de aceite
- [ ] 0 funções de teste sem assert
- [ ] \`./src/tools/check_test_quality.sh\` passa sem erros

## Estimativa
2-3 horas" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: demais testes"

# ============================================
# GRUPO 2: MÓDULOS SEM TESTE
# ============================================

echo ""
echo "[2/4] Criando issues para módulos sem teste..."

# Soul modules (críticos)
gh issue create \
    --title "[TEST] Criar testes para módulos soul/ críticos" \
    --body "## Problema
Módulos críticos do soul/ não têm testes.

## Módulos
- \`src/soul/boca.py\` - TTS (734 linhas)
- \`src/soul/visao.py\` - Computer Vision (656 linhas)
- \`src/soul/user_profiler.py\` - Perfil do usuário (621 linhas)
- \`src/soul/threading_manager.py\` - Gerenciamento de threads (538 linhas)

## O que testar
### boca.py
\`\`\`python
def test_boca_initialization():
    boca = Boca()
    assert boca.engine is not None

def test_boca_speak_returns_audio():
    boca = Boca()
    result = boca.speak('teste')
    assert result is not None or boca.is_speaking

def test_boca_handles_empty_text():
    boca = Boca()
    result = boca.speak('')
    assert result is None  # Não deve crashar
\`\`\`

### visao.py
\`\`\`python
def test_visao_capture_screenshot():
    visao = Visao()
    img = visao.capture()
    assert img is not None
    assert hasattr(img, 'shape')  # numpy array

def test_visao_analyze_returns_description():
    visao = Visao()
    result = visao.analyze(mock_image)
    assert isinstance(result, str)
\`\`\`

## Critérios de aceite
- [ ] test_boca.py com 5+ testes
- [ ] test_visao.py com 5+ testes
- [ ] test_user_profiler.py com 5+ testes
- [ ] test_threading_manager.py com 5+ testes
- [ ] Cobertura > 60% para cada módulo

## Arquivos a criar
- \`src/tests/test_boca.py\`
- \`src/tests/test_visao.py\`
- \`src/tests/test_user_profiler.py\`
- \`src/tests/test_threading_manager.py\`" \
    --label "type:test,P1-high,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: módulos soul/ críticos"

# Soul modules (secundários)
gh issue create \
    --title "[TEST] Criar testes para módulos soul/ secundários" \
    --body "## Módulos
- \`src/soul/conversation_state.py\`
- \`src/soul/streaming.py\`
- \`src/soul/comunicacao.py\`
- \`src/soul/model_manager.py\`
- \`src/soul/voice_system.py\`
- \`src/soul/wake_word.py\`
- \`src/soul/reminders.py\`
- \`src/soul/processing_threads.py\`
- \`src/soul/entity_hotswap.py\`
- \`src/soul/api_optimizer.py\`
- \`src/soul/voice_profile.py\`

## O que testar
Para cada módulo, criar pelo menos:
1. Teste de inicialização
2. Teste do método principal
3. Teste de caso de erro
4. Teste de caso de borda

## Template
\`\`\`python
import pytest
from src.soul.MODULE import MainClass

class TestMainClass:
    def test_initialization(self):
        obj = MainClass()
        assert obj is not None

    def test_main_method(self):
        obj = MainClass()
        result = obj.main_method(valid_input)
        assert result is not None

    def test_handles_none(self):
        obj = MainClass()
        result = obj.main_method(None)
        assert result is None or isinstance(result, ExpectedType)

    def test_handles_error(self):
        obj = MainClass()
        with pytest.raises(ExpectedException):
            obj.main_method(invalid_input)
\`\`\`

## Critérios de aceite
- [ ] 11 arquivos de teste criados
- [ ] Mínimo 3 testes por arquivo
- [ ] Todos os testes têm assert real" \
    --label "type:test,P2-medium,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: módulos soul/ secundários"

# ============================================
# GRUPO 3: LINT
# ============================================

echo ""
echo "[3/4] Criando issue para lint..."

gh issue create \
    --title "[LINT] Corrigir problemas de lint restantes" \
    --body "## Problema
1 problema de lint detectado.

## Como verificar
\`\`\`bash
ruff check src/ --output-format=full
\`\`\`

## Como corrigir
\`\`\`bash
ruff check src/ --fix
\`\`\`

## Critérios de aceite
- [ ] \`ruff check src/\` retorna 0 erros" \
    --label "type:refactor,P2-medium,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: lint"

# ============================================
# GRUPO 4: META ISSUE
# ============================================

echo ""
echo "[4/4] Criando meta issue..."

gh issue create \
    --title "[META] Qualidade de testes - Tracker" \
    --body "## Objetivo
Garantir qualidade REAL dos testes, não apenas métricas.

## Issues relacionadas
- [ ] Corrigir testes sem assert em test_ui_integrity.py
- [ ] Corrigir testes sem assert em test_response_pipeline.py
- [ ] Corrigir testes sem assert em test_new_features.py
- [ ] Corrigir demais testes sem assert (34 funções)
- [ ] Criar testes para módulos soul/ críticos
- [ ] Criar testes para módulos soul/ secundários
- [ ] Corrigir problemas de lint

## Metas
| Métrica | Atual | Meta |
|---------|-------|------|
| Testes sem assert | 49 | 0 |
| Módulos sem teste | 15 | 0 |
| Cobertura | ~10% | 60% |
| Lint errors | 1 | 0 |

## Validação
\`\`\`bash
./src/tools/validate_all.sh
\`\`\`

## Critérios de aceite
- [ ] \`./src/tools/check_test_quality.sh\` passa
- [ ] Todos os módulos têm arquivo de teste
- [ ] Cobertura >= 60%
- [ ] Lint limpo" \
    --label "type:test,P0-critical" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Meta issue criada"

# ============================================
# RESUMO
# ============================================

echo ""
echo "=========================================="
echo "  ISSUES CRIADAS COM SUCESSO"
echo "=========================================="
echo ""
echo "Ver todas: gh issue list --label type:test"
echo "Ver prontas: gh issue list --label status:ready"
echo ""
