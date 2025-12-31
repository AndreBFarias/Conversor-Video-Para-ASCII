# Guia de Contribuicao - Luna

**Data:** 2025-12-18

## TL;DR

Regras obrigatorias para contribuir com Luna: fork > branch > codigo limpo > testes > PR com documentacao. Zero emojis, zero comentarios no codigo, PT-BR tecnico.

## Contexto

Luna e um assistente IA com interface TUI construido em Python/Textual. Este projeto segue o Protocolo Luna: codigo puro, documentacao separada, arquitetura rigida. Contribuir significa entender e respeitar essas regras.

## Como Contribuir

### 1. Setup Inicial

```bash
git clone https://github.com/AndreBFarias/Luna.git
cd Luna
./install.sh
source venv/bin/activate
```

### 2. Criar Branch

```bash
git checkout -b feature/nome-da-feature
```

ou

```bash
git checkout -b fix/nome-do-bug
```

### 3. Desenvolver

1. Estude a arquitetura existente em `src/`
2. Mantenha a separacao: logica em `src/`, docs em `dev-journey/`
3. Use type hints obrigatorios
4. Zero comentarios explicativos no codigo
5. Implemente logging rotacionado (nunca apenas `print()`)

### 4. Testar

```bash
pytest src/core/ -v
pytest src/utils/ -v
python main.py
```

Ordem obrigatoria: testa modulos filhos primeiro, orquestrador depois.

### 5. Documentar

Toda feature ou bug fix DEVE incluir:

- Atualizacao em `dev-journey/01-changelog/CHANGELOG.md`
- Atualizacao em `dev-journey/03-session-logs/YYYY-MM-DD_Session_Summary.md`
- Documentacao tecnica em `dev-journey/04-docs/` se necessario

### 6. Criar Pull Request

1. Push da branch:
```bash
git push origin feature/nome-da-feature
```

2. Abra PR no GitHub com:
   - Titulo imperativo em PT-BR
   - Descricao clara do problema/solucao
   - Referencias a issues relacionadas
   - Checklist de validacao

## Regras de Pull Request

### Obrigatorio

- [ ] Codigo passa em todos os testes
- [ ] Type hints em todas as funcoes
- [ ] Zero comentarios no codigo
- [ ] Documentacao atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Logging implementado (nada de `print()`)
- [ ] Segue estrutura de diretorios obrigatoria

### Proibido

- Emojis em commits, codigo ou documentacao
- Comentarios explicativos no codigo
- `print()` para debug
- Modificar `main.py` sem justificativa (ele e orquestrador)
- Dependencias sem adicionar ao `requirements.txt`

## Padrao de Codigo

### Commits

Mensagens imperativas em PT-BR:

```
feat: adiciona suporte a multi-threading no processador
fix: corrige vazamento de memoria no cache
refactor: separa logica de API em modulo dedicado
docs: atualiza guia de instalacao
```

### Branches

- `main`: producao estavel, somente leitura
- `dev`: desenvolvimento ativo, aceita PRs
- `feature/*`: novas funcionalidades
- `fix/*`: correcoes de bugs
- `refactor/*`: refatoracoes

### Code Review

Todo PR passa por:

1. Validacao automatica de testes
2. Revisao de arquitetura
3. Validacao de documentacao
4. Aprovacao de mantenedor

## Regras de Documentacao

### Regras Obrigatorias

Todo PR **DEVE** seguir estas regras:

| Regra | Descricao | Onde Atualizar |
|-------|-----------|----------------|
| **1. PR atualiza doc** | Todo PR deve atualizar a documentacao relevante | `dev-journey/` |
| **2. Novos .py no FOLDER_STRUCTURE** | Novos arquivos Python precisam de entrada | `dev-journey/01-getting-started/FOLDER_STRUCTURE.md` |
| **3. Feature no CHANGELOG** | Toda feature nova precisa de entrada | `dev-journey/03-changelog/CHANGELOG.md` |
| **4. Codigo sem comentarios = doc pareada** | Se o codigo nao tem comentarios, crie doc | `dev-journey/04-implementation/` |
| **5. Funcoes publicas com docstring** | Funcoes publicas precisam de docstring minima | No proprio arquivo |

### Docstring Minima

```python
def funcao_publica(param1: str, param2: int) -> Result:
    """Breve descricao do que a funcao faz.

    Args:
        param1: Descricao do parametro
        param2: Descricao do parametro

    Returns:
        Descricao do retorno
    """
```

### Checklist de Documentacao

Antes de abrir PR, verifique:

- [ ] CHANGELOG.md atualizado com a mudanca
- [ ] FOLDER_STRUCTURE.md atualizado (se criou arquivos)
- [ ] Session log criado em `Dev_log/YYYY-MM-DD_Session_Summary.md`
- [ ] Funcoes publicas tem docstring
- [ ] README.md atualizado (se feature e user-facing)
- [ ] PLACEHOLDERS.md atualizado (se adicionou TODOs)

---

## Templates de Documentacao

### Para Features

Use o template `dev-journey/templates/FEATURE_TEMPLATE.md`:

1. Status atual
2. Descricao tecnica
3. Motivacao
4. Implementacao detalhada
5. Arquivos modificados
6. TODO list

### Para Bugs

Use o template `dev-journey/templates/BUG_REPORT_TEMPLATE.md`:

1. Comportamento esperado vs observado
2. Steps para reproduzir
3. Logs relevantes
4. Ambiente

### Para Changelog

Use o template `dev-journey/templates/CHANGELOG_ENTRY_TEMPLATE.md`:

1. Versao
2. Data
3. Tipo de mudanca (Added/Fixed/Changed/Removed)
4. Descricao concisa

## Protocolo de Qualidade

### Antes de Commitar

```bash
black src/
mypy src/
pytest src/ -v
```

### Antes de PR

1. Rebase com `dev`:
```bash
git fetch origin
git rebase origin/dev
```

2. Resolve conflitos se houver
3. Força push se necessario:
```bash
git push -f origin feature/nome-da-feature
```

## Uso de IA no Desenvolvimento

Luna e um projeto de IA open source. O uso de ferramentas de IA para desenvolvimento e **bem-vindo e encorajado**, desde que as regras do projeto sejam seguidas.

### Permitido

- Usar LLMs para gerar codigo, documentacao, testes
- Usar assistentes de codigo (Copilot, Codeium, etc)
- Usar ferramentas de automacao para tarefas repetitivas
- Contribuicoes geradas parcial ou totalmente por IA

### Obrigatorio (mesmas regras para humanos e IAs)

- Seguir todas as regras de codigo deste guia
- Revisar o output antes de commitar
- Garantir que testes passam
- Manter qualidade e consistencia
- Documentar mudancas adequadamente

### Proibido

- Mencionar ferramentas de IA especificas no codigo ou commits
- Incluir assinaturas de IA ou creditos a servicos especificos
- Expor prompts, IDs ou configuracoes de servicos externos
- Copiar codigo protegido por copyright

### Anonimato

O projeto segue politica de **anonimato total**. Nenhum contribuidor (humano ou IA) deve ser identificado individualmente no codigo. Commits sao impessoais e focados na mudanca, nao no autor.

---

## Hierarquia de Prioridades

1. Correcoes criticas de seguranca
2. Bugs que quebram funcionalidade core
3. Performance e otimizacoes
4. Novas features
5. Refatoracoes esteticas

## Contato

- Issues: https://github.com/AndreBFarias/Luna/issues
- Discussoes: https://github.com/AndreBFarias/Luna/discussions

## Links Relacionados

- [CODE_STYLE.md](CODE_STYLE.md)
- [TESTING.md](TESTING.md)
- [DEBUGGING.md](DEBUGGING.md)
- [FEATURE_TEMPLATE.md](../templates/FEATURE_TEMPLATE.md)
- [BUG_REPORT_TEMPLATE.md](../templates/BUG_REPORT_TEMPLATE.md)

---

**Licenca:** GPLv3
