# Feature: [NOME]

**Data:** YYYY-MM-DD
**Status:** [Planejado | Em Progresso | Concluido | Abandonado]

---

## TL;DR

[Resumo de 1 linha: O que essa feature faz e qual problema resolve]

---

## Descricao

[O que essa feature faz? Explicacao clara e direta.]

---

## Motivacao

[Por que precisamos disso? Qual problema estamos resolvendo?]

---

## Implementacao

### Abordagem

[Como foi/sera implementado? Decisoes tecnicas principais.]

### Fluxo

```
[Input] -> [Processamento] -> [Output]
```

### Codigo Exemplo

```python
def exemplo_da_feature(param: str) -> Result:
    # Logica principal
    pass
```

---

## Arquivos Afetados

| Arquivo | Mudanca |
|---------|---------|
| `src/soul/[modulo].py` | [O que mudou] |
| `src/ui/[widget].py` | [O que mudou] |
| `config.py` | [Nova configuracao] |

---

## Dependencias

### Internas

- [Feature X] - Precisa estar implementada antes
- [Modulo Y] - Usa funcoes de Y

### Externas

- `pacote==1.2.3` - [Justificativa]

---

## Configuracao

```ini
[nova_secao]
parametro = valor_padrao
```

Ou em `.env`:

```bash
NOVA_VAR=valor
```

---

## Testes

### Casos de Teste

1. **Sucesso:** Input valido retorna resultado esperado
2. **Erro:** Input invalido levanta excecao apropriada
3. **Edge case:** [Caso limite especifico]

### Comandos

```bash
pytest tests/test_[feature].py -v
```

---

## TODO

### Planejamento

- [ ] Definir escopo final
- [ ] Validar abordagem

### Implementacao

- [ ] Criar estrutura base
- [ ] Implementar logica core
- [ ] Adicionar tratamento de erros
- [ ] Escrever testes

### Finalizacao

- [ ] Code review
- [ ] Atualizar CHANGELOG.md
- [ ] Documentar uso

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| [Risco 1] | Media | Alto | [Estrategia] |

---

## Notas

[Qualquer informacao adicional, links, referencias]

---

## Links Relacionados

- [Issue relacionada](#)
- [Documentacao externa](#)

---
*Template Version: 2.0 | Licenca: GPLv3*
