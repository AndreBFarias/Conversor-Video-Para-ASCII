# Bug Report: [Titulo Descritivo do Bug]

**Data:** YYYY-MM-DD
**Status:** [Aberto / Em Investigacao / Corrigido / Fechado]
**Severidade:** [Critica / Alta / Media / Baixa]
**Prioridade:** [P0 / P1 / P2 / P3]

## TL;DR

[Resumo de 1 linha: O que quebrou e qual o impacto]

## Descricao

### Comportamento Esperado

[Descricao clara do que deveria acontecer]

### Comportamento Observado

[Descricao clara do que realmente aconteceu]

### Diferenca

[Explicite a discrepancia entre esperado e observado]

## Ambiente

### Sistema

- **OS:** [Pop!_OS / Ubuntu / etc]
- **Versao do OS:** [22.04 LTS / etc]
- **Python:** [3.10.x / 3.11.x]
- **Shell:** [zsh / bash]

### Versao do Projeto

- **Branch:** [main / dev / feature/X]
- **Commit:** [hash do commit ou "latest"]
- **Versao:** [v1.2.3 se aplicavel]

### Dependencias Relevantes

```bash
textual==0.X.Y
google-genai==0.X.Y
# Liste apenas dependencias suspeitas
```

Verificar:
```bash
pip freeze | grep [pacote]
```

## Steps para Reproduzir

### Pre-Requisitos

[Configuracoes necessarias antes de reproduzir]

1. [Configuracao 1]
2. [Configuracao 2]

### Steps

1. [Passo exato para reproduzir]
2. [Segundo passo]
3. [Terceiro passo]
4. [Observe o erro]

### Reproducao Minima

```python
# Codigo minimo que reproduz o bug
from src.core.modulo import funcao_com_bug

resultado = funcao_com_bug(parametro_problematico)
# Erro acontece aqui
```

### Frequencia

- [ ] Acontece 100% das vezes
- [ ] Acontece intermitentemente (~X% das vezes)
- [ ] Acontece apenas em condicoes especificas

## Logs e Stack Trace

### Stack Trace Completo

```
Traceback (most recent call last):
  File "main.py", line X, in <module>
    funcao()
  File "src/core/modulo.py", line Y, in funcao
    operacao_problematica()
  File "src/utils/helper.py", line Z, in operacao_problematica
    raise Exception("Erro especifico")
Exception: Erro especifico
```

### Logs Relevantes

**luna.log:**
```
2025-12-18 14:32:10 - ERROR - [modulo.py:120] Falha ao processar mensagem
2025-12-18 14:32:10 - DEBUG - [modulo.py:121] Estado: {...}
```

**api.log:**
```
2025-12-18 14:32:09 - API Request: messages.create(...)
2025-12-18 14:32:10 - API Error: 429 Rate Limit Exceeded
```

### Comando para Extrair Logs

```bash
tail -100 src/logs/luna.log | grep ERROR
grep "YYYY-MM-DD 14:32" src/logs/api.log
```

## Diagnostico Inicial

### Modulo Afetado

- **Arquivo:** `src/core/[modulo].py`
- **Funcao:** `[nome_da_funcao]`
- **Linha:** [aproximadamente linha X]

### Causa Provavel

[Hipotese inicial sobre o que causa o bug]

### Evidencias

1. [Log X mostra Y]
2. [Comportamento Z sugere problema em W]

## Impacto

### Afeta

- [ ] Funcionalidade critica (sistema nao funciona)
- [ ] Funcionalidade secundaria (workaround existe)
- [ ] UX/UI apenas (funcional mas confuso)
- [ ] Performance (lento mas funciona)

### Usuarios Afetados

- [ ] Todos os usuarios
- [ ] Usuarios em configuracao especifica
- [ ] Apenas desenvolvedores
- [ ] Apenas em ambiente de teste

### Workaround

[Se existe solucao temporaria, descreva:]

```bash
# Exemplo de workaround
export VAR=valor_alternativo
python main.py
```

## Investigacao

### Testes Executados

1. **Teste de isolamento:**
   ```bash
   pytest tests/unit/test_[modulo].py -v
   ```
   Resultado: [Passou / Falhou]

2. **Teste manual:**
   [Descricao do teste manual executado]
   Resultado: [Comportamento observado]

### Hipoteses Testadas

- [ ] **Hipotese 1:** [Descricao]
  - Teste: [Como testou]
  - Resultado: [Confirmada / Rejeitada]

- [ ] **Hipotese 2:** [Descricao]
  - Teste: [Como testou]
  - Resultado: [Confirmada / Rejeitada]

### Debugging Executado

```bash
DEBUG=1 python main.py
# Output relevante
```

```python
# PDB breakpoint usado
import pdb; pdb.set_trace()
# Variaveis inspecionadas: x, y, z
```

## Solucao Proposta

### Correcao

[Descricao tecnica da correcao proposta]

**Mudancas Necessarias:**

1. `src/core/[modulo].py` - [Descricao da mudanca]
2. `tests/unit/test_[modulo].py` - [Adicionar teste de regressao]

**Diff Proposto:**

```python
# Antes
def funcao_com_bug(param: str) -> str:
    return param.upper()

# Depois
def funcao_corrigida(param: str) -> str:
    if not param:
        raise ValueError("Parametro nao pode ser vazio")
    return param.upper()
```

### Teste de Regressao

```python
def test_funcao_nao_aceita_string_vazia():
    with pytest.raises(ValueError):
        funcao_corrigida("")
```

### Validacao

- [ ] Teste unitario passa
- [ ] Teste de integracao passa
- [ ] Teste manual confirma correcao
- [ ] Nao introduz novos bugs

## Timeline

- **Reportado:** YYYY-MM-DD HH:MM
- **Confirmado:** YYYY-MM-DD HH:MM
- **Corrigido:** YYYY-MM-DD HH:MM (estimativa)
- **Testado:** YYYY-MM-DD HH:MM (estimativa)
- **Fechado:** YYYY-MM-DD HH:MM (estimativa)

## Metadados

### Labels

- `bug`
- `[severidade-critica/alta/media/baixa]`
- `[componente-core/utils/gui/api]`

### Relacionado a

- Issue: [#123](link)
- PR: [#456](link)
- Discussao: [#789](link)

### Checklist de Resolucao

- [ ] Bug reproduzido
- [ ] Causa raiz identificada
- [ ] Correcao implementada
- [ ] Teste de regressao adicionado
- [ ] Code review aprovado
- [ ] Documentacao atualizada
- [ ] CHANGELOG atualizado
- [ ] Merged em `dev`
- [ ] Validado em ambiente de teste
- [ ] Issue fechada

## Notas Adicionais

[Qualquer informacao adicional: dificuldades encontradas, descobertas interessantes, sugestoes de melhoria, etc.]

## Anexos

### Screenshots

[Se aplicavel, adicione screenshots do erro]

### Arquivos de Configuracao

**config.py:**
```python
CHAT_PROVIDER = "gemini"
CHAT_MODEL = "gemini-2.0-flash-exp"
```

### Dados de Entrada

[Se o bug depende de input especifico, inclua exemplo anonimizado]

```json
{
  "input": "exemplo de dados que causam o bug"
}
```

## Links Relacionados

- [Documentacao relevante](link)
- [Issue similar](link)
- [Referencia externa](link)

---

**Template Version:** 1.0
**Licenca:** GPLv3
