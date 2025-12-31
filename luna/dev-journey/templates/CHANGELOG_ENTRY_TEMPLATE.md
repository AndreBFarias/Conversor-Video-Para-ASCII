# Changelog Entry Template

**Data:** YYYY-MM-DD
**Versao:** [vX.Y.Z ou "Unreleased"]
**Tipo:** [Added / Fixed / Changed / Removed / Deprecated / Security]

## TL;DR

[Resumo de 1 linha da mudanca]

## Formato de Entrada

Use este formato ao adicionar entrada no CHANGELOG.md principal:

```markdown
## [vX.Y.Z] - YYYY-MM-DD

### Added
- [Descricao concisa da nova feature] ([#PR](link))

### Fixed
- [Descricao concisa do bug corrigido] ([#PR](link))

### Changed
- [Descricao concisa da mudanca] ([#PR](link))

### Removed
- [Descricao concisa do que foi removido] ([#PR](link))

### Deprecated
- [Descricao concisa do que foi marcado como obsoleto] ([#PR](link))

### Security
- [Descricao concisa da correcao de seguranca] ([#PR](link))
```

## Tipos de Mudanca

### Added
Para novas features ou funcionalidades.

**Exemplos:**
- Adicionado suporte a multi-threading no processador de conversacoes
- Adicionada opcao de configuracao para timeout de API
- Adicionado comando `/export` para exportar historico de conversas

### Fixed
Para correcoes de bugs.

**Exemplos:**
- Corrigido vazamento de memoria no gerenciador de cache
- Corrigido erro de parsing em mensagens com caracteres especiais
- Corrigido crash ao receber resposta vazia da API

### Changed
Para mudancas em funcionalidades existentes.

**Exemplos:**
- Alterado modelo padrao de LLM local para API Gemini
- Atualizado sistema de logging para rotacao automatica a cada 10MB
- Refatorado processador de mensagens para melhor performance

### Removed
Para features ou funcionalidades removidas.

**Exemplos:**
- Removido suporte a Python 3.8 (minimo agora e 3.10)
- Removida dependencia obsoleta `old-package`
- Removido endpoint deprecado `/legacy-api`

### Deprecated
Para features marcadas como obsoletas mas ainda funcionais.

**Exemplos:**
- Marcado `/old-command` como obsoleto, use `/new-command`
- Marcada funcao `process_legacy()` como deprecada, sera removida em v2.0

### Security
Para correcoes de vulnerabilidades.

**Exemplos:**
- Corrigida vulnerabilidade de injecao em input de usuario
- Atualizada biblioteca `requests` para versao segura 2.31.0
- Adicionada validacao de API key para prevenir vazamento

## Guidelines de Escrita

### 1. Seja Conciso

**Ruim:**
- Foi implementada uma nova funcionalidade muito interessante que permite aos usuarios exportarem todo o historico de conversas para um arquivo JSON, o que e muito util para backup e analise posterior.

**Bom:**
- Adicionado comando `/export` para exportar historico em JSON

### 2. Use Voz Ativa

**Ruim:**
- O bug de memoria foi corrigido

**Bom:**
- Corrigido vazamento de memoria no cache

### 3. Seja Especifico

**Ruim:**
- Melhorias de performance

**Bom:**
- Reduzido tempo de inicializacao de 3s para 0.5s

### 4. Inclua Referencias

**Ruim:**
- Corrigido bug de crash

**Bom:**
- Corrigido crash ao processar mensagens vazias ([#123](link))

## Versionamento Semantico

Luna segue [Semantic Versioning 2.0.0](https://semver.org/):

### MAJOR (X.0.0)
Mudancas incompativeis com versoes anteriores.

**Quando incrementar:**
- Remocao de features publicas
- Mudanca de API publica
- Mudanca de formato de configuracao

**Exemplo:**
```markdown
## [v2.0.0] - 2025-12-18

### Changed
- Refatorada API interna - BREAKING: `process()` agora retorna `Result` ao inves de `dict`

### Removed
- Removido suporte a Python 3.8 e 3.9
```

### MINOR (0.X.0)
Novas features ou funcionalidades (retrocompativeis).

**Quando incrementar:**
- Adicao de nova feature
- Melhoria significativa em feature existente
- Adicao de nova API publica

**Exemplo:**
```markdown
## [v1.3.0] - 2025-12-18

### Added
- Adicionado suporte a streaming de respostas
- Adicionado comando `/save` para salvar conversas
```

### PATCH (0.0.X)
Correcoes de bugs e pequenas mudancas (retrocompativeis).

**Quando incrementar:**
- Bug fixes
- Atualizacoes de dependencias
- Correcoes de documentacao

**Exemplo:**
```markdown
## [v1.2.3] - 2025-12-18

### Fixed
- Corrigido erro ao processar caracteres Unicode
- Corrigido crash em sistemas sem GPU
```

## Exemplo Completo

```markdown
## [v1.4.0] - 2025-12-18

### Added
- Adicionado suporte a multi-threading para processamento paralelo ([#145](link))
- Adicionado comando `/debug` para ativar modo verbose ([#147](link))
- Adicionada opcao `max_retries` em config.ini ([#149](link))

### Fixed
- Corrigido vazamento de memoria no ConversationMemory ([#142](link))
- Corrigido crash ao receber resposta vazia da API ([#144](link))
- Corrigido parsing incorreto de mensagens com markdown ([#146](link))

### Changed
- Atualizado modelo padrao do provider LLM ([#148](link))
- Refatorado sistema de cache para usar Redis ([#150](link))
- Melhorado tempo de inicializacao de 3s para 0.5s ([#151](link))

### Deprecated
- Marcado comando `/old-export` como obsoleto, use `/export` ([#152](link))

### Security
- Atualizada biblioteca LLM para versao mais recente (correcao de vulnerabilidade) ([#153](link))
```

## Checklist Pre-Commit

Antes de adicionar entrada ao CHANGELOG:

- [ ] Versao correta conforme SemVer
- [ ] Data no formato YYYY-MM-DD
- [ ] Tipo de mudanca correto (Added/Fixed/etc)
- [ ] Descricao concisa e especifica
- [ ] Link para PR incluido
- [ ] Ordenado cronologicamente (mais recente primeiro)
- [ ] Sem erros de portugues
- [ ] Sem emojis

## Template Rapido

Copie e cole este template ao criar nova entrada:

```markdown
## [Unreleased]

### Added

### Fixed

### Changed

### Removed

### Deprecated

### Security
```

Preencha apenas as secoes relevantes. Remova secoes vazias antes de commitar.

## Links Relacionados

- [CONTRIBUTING.md](../06-guides/CONTRIBUTING.md)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Template Version:** 1.0
**Licenca:** GPLv3
