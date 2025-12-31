#!/bin/bash
# src/tools/create_final_quality_issues.sh
# Cria issues finais para atingir 100% de qualidade

set -e

echo "=== CRIANDO ISSUES FINAIS ==="
echo ""

# Issue 1: Último teste sem assert
gh issue create \
    --title "[TEST] Corrigir último teste sem assert: test_ambient_presence.py" \
    --body "## Problema
1 função de teste não tem assert.

## Localização
\`src/tests/test_ambient_presence.py:267\`
\`\`\`python
def test_no_callback_when_none():
    # Precisa de assert
\`\`\`

## O que fazer
Adicionar assert que valida o comportamento esperado quando callback é None.

\`\`\`python
def test_no_callback_when_none():
    presence = AmbientPresence(callback=None)
    result = presence.trigger()
    assert result is None or result == False, 'Sem callback deve retornar None/False'
\`\`\`

## Critérios de aceite
- [ ] Função tem assert real
- [ ] \`./src/tools/check_test_quality.sh\` passa com 0 erros

## Validação
\`\`\`bash
./src/tools/check_test_quality.sh
\`\`\`" \
    --label "type:test,P0-critical,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: test_ambient_presence.py"

# Issue 2: Lint auto-fix
gh issue create \
    --title "[LINT] Corrigir 4 erros de lint em test_hardware_tiers.py" \
    --body "## Problema
4 erros de import não ordenado.

## Arquivos
\`src/tests/test_hardware_tiers.py\` linhas 102, 109, 118, 254

## Solução
\`\`\`bash
ruff check src/tests/test_hardware_tiers.py --fix
\`\`\`

## Critérios de aceite
- [ ] \`ruff check src/\` retorna 0 erros

## Validação
\`\`\`bash
ruff check src/ --output-format=concise
\`\`\`" \
    --label "type:refactor,P1-high,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: lint"

# Issue 3: Módulos soul/ críticos (boca, visao)
gh issue create \
    --title "[TEST] Criar testes para boca.py e visao.py" \
    --body "## Módulos críticos sem teste

### src/soul/boca.py (734 linhas) - TTS
Testar:
- Inicialização do engine
- speak() com texto válido
- speak() com texto vazio
- Interrupção de fala
- Fallback entre engines

### src/soul/visao.py (656 linhas) - Computer Vision
Testar:
- Captura de screenshot
- Análise de imagem
- Tratamento de erro quando sem display
- Mock de respostas da API

## Template
\`\`\`python
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile

class TestBoca:
    @patch('src.soul.boca.TTSEngine')
    def test_initialization(self, mock_engine):
        from src.soul.boca import Boca
        boca = Boca()
        assert boca is not None

    @patch('src.soul.boca.TTSEngine')
    def test_speak_valid_text(self, mock_engine):
        from src.soul.boca import Boca
        boca = Boca()
        boca.speak('Olá mundo')
        mock_engine.return_value.speak.assert_called()

    def test_speak_empty_text(self):
        from src.soul.boca import Boca
        boca = Boca()
        result = boca.speak('')
        # Não deve crashar
        assert True

class TestVisao:
    @patch('src.soul.visao.mss')
    def test_capture_returns_image(self, mock_mss):
        from src.soul.visao import Visao
        mock_mss.return_value.__enter__.return_value.grab.return_value = MagicMock()
        visao = Visao()
        img = visao.capture()
        assert img is not None
\`\`\`

## Critérios de aceite
- [ ] test_boca.py com 8+ testes
- [ ] test_visao.py com 8+ testes
- [ ] Todos os testes passam
- [ ] Usar mocks para dependências externas (TTS, display, API)

## Arquivos a criar
- \`src/tests/test_boca.py\`
- \`src/tests/test_visao.py\`" \
    --label "type:test,P1-high,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: boca.py e visao.py"

# Issue 4: Módulos soul/ restantes
gh issue create \
    --title "[TEST] Criar testes para 12 módulos soul/ restantes" \
    --body "## Módulos sem teste

| Módulo | Linhas | Prioridade |
|--------|--------|------------|
| user_profiler.py | 621 | Alta |
| threading_manager.py | 538 | Alta |
| conversation_state.py | ? | Média |
| streaming.py | ? | Média |
| comunicacao.py | ? | Média |
| model_manager.py | ? | Média |
| voice_system.py | ? | Baixa |
| wake_word.py | ? | Baixa |
| reminders.py | ? | Baixa |
| processing_threads.py | ? | Baixa |
| entity_hotswap.py | ? | Média |
| api_optimizer.py | ? | Média |

## Padrão obrigatório
Cada arquivo de teste deve ter no mínimo:

\`\`\`python
import pytest
from unittest.mock import Mock, patch

class TestNomeDoModulo:
    def test_initialization(self):
        '''Testa se o módulo inicializa sem erro'''
        # ...
        assert obj is not None

    def test_main_functionality(self):
        '''Testa a função principal do módulo'''
        # ...
        assert result == expected

    def test_handles_none_input(self):
        '''Testa tratamento de input None'''
        # ...
        assert result is None or isinstance(result, ExpectedType)

    def test_handles_error(self):
        '''Testa tratamento de erro'''
        with pytest.raises(ExpectedException):
            # ...
\`\`\`

## Critérios de aceite
- [ ] 12 arquivos test_*.py criados
- [ ] Mínimo 4 testes por arquivo
- [ ] Todos os testes têm assert real
- [ ] Usar mocks para dependências externas
- [ ] \`./src/tools/validate_all.sh\` passa

## Arquivos a criar
- test_user_profiler.py
- test_threading_manager.py
- test_conversation_state.py
- test_streaming.py
- test_comunicacao.py
- test_model_manager.py
- test_voice_system.py
- test_wake_word.py
- test_reminders.py
- test_processing_threads.py
- test_entity_hotswap.py
- test_api_optimizer.py" \
    --label "type:test,P1-high,status:ready,ai-task" \
    --milestone "Fase 2: Estabilidade"

echo "  ✓ Issue criada: módulos soul/ restantes"

# Resumo
echo ""
echo "=========================================="
echo "  4 ISSUES CRIADAS"
echo "=========================================="
echo ""
echo "Ordem de execução:"
echo "  1. [P0] Corrigir último teste sem assert"
echo "  2. [P1] Corrigir lint (ruff --fix)"
echo "  3. [P1] Criar testes boca.py e visao.py"
echo "  4. [P1] Criar testes 12 módulos restantes"
echo ""
echo "Ver issues: gh issue list --label type:test --state open"
echo ""
