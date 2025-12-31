# GUIA DE IMPLEMENTACAO DE NOVAS FEATURES

**Data:** 2025-12-30
**Pre-requisito:** Executar GUIA_CORRECAO.md primeiro
**Publico:** Desenvolvedores (humanos ou IAs)

---

## FILOSOFIA DO PROJETO

### Principios de Design

1. **Modularidade** - Cada feature em seu proprio modulo
2. **Testabilidade** - Todo codigo novo vem com testes
3. **Documentacao** - Docstrings + entrada no CHANGELOG
4. **Retrocompatibilidade** - Nao quebrar features existentes

### Arquitetura de Referencia

```
src/
├── soul/           # "Cerebro" - LLM, personalidade, memoria ativa
├── core/           # Infraestrutura - logging, threading, entidades
├── data_memory/    # Persistencia - vetores, cache, memorias
├── ui/             # Interface - widgets Textual
├── web/            # Dashboard web - FastAPI
├── app/            # Bootstrap e mixins do app principal
└── tests/          # Testes unitarios e integracao
```

---

## FLUXO PADRAO PARA NOVA FEATURE

### ETAPA 1: PLANEJAMENTO (~15 min)

```bash
# 1. Criar branch
git checkout main && git pull
git checkout -b feat/nome-da-feature

# 2. Criar issue (opcional mas recomendado)
gh issue create \
  --title "[FEAT] Descricao curta da feature" \
  --body "## Objetivo\n...\n## Arquivos\n...\n## Checklist\n- [ ] Implementar\n- [ ] Testes\n- [ ] Documentar" \
  --label "enhancement"
```

### ETAPA 2: SCAFFOLDING (~10 min)

Criar estrutura de arquivos:

```bash
# Se for modulo novo em soul/
touch src/soul/nova_feature.py
touch src/tests/test_nova_feature.py

# Se for novo subsistema
mkdir -p src/novo_subsistema/
touch src/novo_subsistema/__init__.py
touch src/novo_subsistema/core.py
touch src/tests/test_novo_subsistema.py
```

### ETAPA 3: IMPLEMENTACAO

#### Template de Modulo

```python
"""
NovaFeature - Descricao curta.

Este modulo e responsavel por:
- Ponto 1
- Ponto 2

Uso:
    from src.soul.nova_feature import get_nova_feature

    feature = get_nova_feature()
    result = feature.do_something()
"""

from dataclasses import dataclass
from typing import Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class NovaFeatureConfig:
    """Configuracao da feature."""
    param1: str = "default"
    param2: int = 10


class NovaFeature:
    """
    Classe principal da feature.

    Attributes:
        config: Configuracao da feature
    """

    def __init__(self, config: Optional[NovaFeatureConfig] = None):
        self.config = config or NovaFeatureConfig()
        logger.info(f"NovaFeature inicializada: {self.config}")

    def do_something(self, input_data: str) -> str:
        """
        Faz algo com os dados.

        Args:
            input_data: Dados de entrada

        Returns:
            Resultado processado

        Raises:
            ValueError: Se input_data for vazio
        """
        if not input_data:
            raise ValueError("input_data nao pode ser vazio")

        logger.debug(f"Processando: {input_data[:50]}...")
        result = f"Processed: {input_data}"
        return result


# Singleton pattern (opcional)
_instance: Optional[NovaFeature] = None


def get_nova_feature() -> NovaFeature:
    """Factory function para NovaFeature."""
    global _instance
    if _instance is None:
        _instance = NovaFeature()
    return _instance


__all__ = ["NovaFeature", "NovaFeatureConfig", "get_nova_feature"]
```

#### Template de Teste

```python
"""Testes para NovaFeature."""

import pytest
from unittest.mock import MagicMock, patch


class TestNovaFeatureConfig:
    def test_default_values(self):
        from src.soul.nova_feature import NovaFeatureConfig

        config = NovaFeatureConfig()
        assert config.param1 == "default"
        assert config.param2 == 10

    def test_custom_values(self):
        from src.soul.nova_feature import NovaFeatureConfig

        config = NovaFeatureConfig(param1="custom", param2=20)
        assert config.param1 == "custom"
        assert config.param2 == 20


class TestNovaFeature:
    def test_initialization(self):
        from src.soul.nova_feature import NovaFeature

        feature = NovaFeature()
        assert feature.config is not None

    def test_do_something_success(self):
        from src.soul.nova_feature import NovaFeature

        feature = NovaFeature()
        result = feature.do_something("test input")
        assert "Processed" in result
        assert "test input" in result

    def test_do_something_empty_raises(self):
        from src.soul.nova_feature import NovaFeature

        feature = NovaFeature()
        with pytest.raises(ValueError, match="nao pode ser vazio"):
            feature.do_something("")


class TestGetNovaFeature:
    def test_returns_singleton(self):
        from src.soul.nova_feature import get_nova_feature

        f1 = get_nova_feature()
        f2 = get_nova_feature()
        assert f1 is f2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### ETAPA 4: INTEGRACAO

#### Se integrar em consciencia.py

```python
# No topo do arquivo
from src.soul.nova_feature import get_nova_feature

# No __init__
def __init__(self, entity_id: str = "luna"):
    # ... existente ...
    self._nova_feature = get_nova_feature()

# No metodo relevante
def process_interaction(self, user_text: str, ...):
    # Usar a nova feature
    enhanced_result = self._nova_feature.do_something(user_text)
    # ...
```

#### Se integrar em main.py

```python
# Se for nova acao de botao
async def action_nova_feature(self):
    from src.soul.nova_feature import get_nova_feature

    feature = get_nova_feature()
    result = feature.do_something(self.current_input)
    self.notify(result)
```

### ETAPA 5: DOCUMENTACAO

#### Atualizar CHANGELOG.md

```markdown
## [Unreleased]

### Adicionado
- **NovaFeature**: Descricao da feature (#ISSUE_NUMBER)
  - `src/soul/nova_feature.py` - Implementacao principal
  - Integrada em consciencia.py
```

#### Criar changelog especifico (opcional)

```bash
cat > dev-journey/03-changelog/$(date +%Y-%m-%d)_nova_feature.md << 'EOF'
# NovaFeature

**Data:** $(date +%Y-%m-%d)
**Tipo:** Feature
**Issue:** #XX

## Resumo
Descricao da feature.

## Arquivos Criados
- `src/soul/nova_feature.py`
- `src/tests/test_nova_feature.py`

## Arquivos Modificados
- `src/soul/consciencia.py` - Integracao
- `dev-journey/03-changelog/CHANGELOG.md`

## Uso
\`\`\`python
from src.soul.nova_feature import get_nova_feature
# ...
\`\`\`

## Testes
\`\`\`bash
pytest src/tests/test_nova_feature.py -v
\`\`\`
EOF
```

### ETAPA 6: VALIDACAO

```bash
# 1. Rodar testes da feature
./venv/bin/python -m pytest src/tests/test_nova_feature.py -v

# 2. Rodar todos os testes (garantir que nao quebrou nada)
./venv/bin/python -m pytest src/tests/ -q --tb=no

# 3. Rodar pre-commit
./venv/bin/pre-commit run --all-files

# 4. Testar manualmente (se aplicavel)
./venv/bin/python main.py
```

### ETAPA 7: COMMIT E PR

```bash
# Commit
git add -A
git commit -m "feat: implementar NovaFeature (#ISSUE)

- Criado src/soul/nova_feature.py
- Integrado em consciencia.py
- 5 testes passando
- Documentado em CHANGELOG"

# Push
git push origin feat/nome-da-feature

# Criar PR
gh pr create \
  --title "feat: NovaFeature" \
  --body "## Summary
- Implementa X
- Integra com Y

## Test plan
- [ ] pytest test_nova_feature.py passa
- [ ] Teste manual OK

Closes #ISSUE"
```

---

## TIPOS DE FEATURES COMUNS

### Tipo 1: Nova Funcionalidade de LLM

**Onde:** `src/soul/`

**Exemplo:** Novo modo de conversa, nova forma de processar resposta

**Padrao:**
1. Criar classe em `src/soul/nova_funcionalidade.py`
2. Integrar em `consciencia.py`
3. Se precisar de UI, adicionar botao em `main.py`

### Tipo 2: Novo Widget de UI

**Onde:** `src/ui/`

**Exemplo:** Novo tipo de visualizacao, novo painel

**Padrao:**
1. Criar widget em `src/ui/novo_widget.py`
2. Adicionar CSS em `src/assets/panteao/entities/*/templo_de_*.css`
3. Integrar em `main.py` no metodo `compose()`

### Tipo 3: Novo Sistema de Memoria

**Onde:** `src/data_memory/`

**Exemplo:** Novo tipo de cache, nova forma de persistencia

**Padrao:**
1. Criar em `src/data_memory/novo_sistema.py`
2. Implementar interface `MemoryInterface` se aplicavel
3. Registrar em `src/data_memory/__init__.py`

### Tipo 4: Novo Provider LLM

**Onde:** `src/soul/providers/`

**Exemplo:** Integrar Claude, OpenAI, etc.

**Padrao:**
1. Criar `src/soul/providers/novo_provider.py`
2. Herdar de `BaseLLMProvider`
3. Registrar em `universal_llm.py`

### Tipo 5: Nova Rota Web

**Onde:** `src/web/`

**Exemplo:** Novo endpoint REST, nova pagina

**Padrao:**
1. Adicionar rota em `src/web/routes.py`
2. Se tiver frontend, atualizar `templates/dashboard.html`
3. Adicionar teste em `test_web.py`

---

## CHECKLIST PRE-MERGE

Antes de fazer merge de qualquer feature:

- [ ] Todos os testes passam (`pytest src/tests/ -q`)
- [ ] Pre-commit passa (`pre-commit run --all-files`)
- [ ] Docstring no topo do arquivo
- [ ] `__all__` definido
- [ ] Type hints em funcoes publicas
- [ ] CHANGELOG atualizado
- [ ] Nenhum `except: pass`
- [ ] Nenhum magic number (usar constants.py)
- [ ] Logging adequado (sem print)
- [ ] Arquivo < 300 linhas (ou justificativa)

---

## FEATURES SUGERIDAS PARA IMPLEMENTAR

### Backlog Priorizado

| Prioridade | Feature | Complexidade | Impacto |
|------------|---------|--------------|---------|
| P1 | Sistema de Plugins | Alta | Extensibilidade |
| P1 | CLI Interativo | Media | UX dev |
| P2 | Busca em Historico | Media | UX usuario |
| P2 | Export de Conversas | Baixa | UX usuario |
| P2 | Temas Customizaveis | Media | Personalizacao |
| P3 | Integracao Telegram | Alta | Alcance |
| P3 | Voice Cloning | Alta | Imersao |
| P3 | Multi-usuario | Alta | Escalabilidade |

### Feature: Sistema de Plugins

**Objetivo:** Permitir que usuarios adicionem funcionalidades sem modificar core.

**Arquivos sugeridos:**
```
src/plugins/
├── __init__.py
├── plugin_interface.py   # ABC para plugins
├── plugin_loader.py      # Descobre e carrega plugins
└── builtin/              # Plugins que vem com Luna
    └── example_plugin.py
```

### Feature: CLI Interativo

**Objetivo:** Comandos tipo `/help`, `/clear`, `/entity`, `/export`.

**Arquivos sugeridos:**
```
src/core/cli_commands.py
src/tests/test_cli_commands.py
```

### Feature: Busca em Historico

**Objetivo:** Pesquisar em conversas antigas.

**Arquivos sugeridos:**
```
src/data_memory/history_search.py
src/ui/search_modal.py
src/tests/test_history_search.py
```

---

## TROUBLESHOOTING COMUM

### "Import circular"

**Causa:** Modulo A importa B, B importa A.

**Solucao:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.soul.outro_modulo import OutraClasse
```

### "Test collection error"

**Causa:** Erro de sintaxe ou import quebrado no teste.

**Solucao:**
```bash
# Isolar o erro
./venv/bin/python -c "import src.tests.test_arquivo"
```

### "God class detected (> 300 lines)"

**Causa:** Pre-commit bloqueia arquivos grandes.

**Solucao:**
1. Extrair classes auxiliares para novo modulo
2. Ou adicionar `# noqa: god-class` (nao recomendado)

### "mypy error"

**Causa:** Type hint incorreto ou faltando.

**Solucao:**
```bash
./venv/bin/mypy src/soul/arquivo.py --show-error-codes
```

---

## RECURSOS UTEIS

### Documentacao Interna

- `INDEX.md` - Navegacao rapida
- `dev-journey/04-implementation/ARCHITECTURE_DNA.md` - Arquitetura
- `dev-journey/04-implementation/DEPENDENCY_MAP.md` - Dependencias
- `dev-journey/06-guides/CODE_STYLE.md` - Estilo de codigo

### Comandos Frequentes

```bash
# Validacao rapida
./src/tools/quick_check.sh

# Testes com cobertura
pytest src/tests/ --cov=src --cov-report=html

# Verificar tamanho de arquivos
wc -l src/soul/*.py | sort -rn | head -10

# Buscar padrao no codigo
grep -rn "padrao" src/ --include="*.py" | grep -v test

# Ver dependencias de um arquivo
grep "^from\|^import" src/soul/consciencia.py | sort
```

---

**Assinatura:** Claude Code (Opus 4.5)
**Data:** 2025-12-30

> "Qualquer idiota consegue escrever codigo que um computador entende.
> Bons programadores escrevem codigo que humanos entendem." - Martin Fowler
