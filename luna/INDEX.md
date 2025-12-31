# Luna - Indice Rapido para IAs

> Referencia rapida para IAs trabalhando neste projeto.
> Ultima atualizacao: 2025-12-30 | Versao: 3.8.1 | Score: 8.8/10

---

## Navegacao Rapida

### Arquivos Essenciais
| Objetivo | Arquivo | Descricao |
|----------|---------|-----------|
| Regras do Projeto | `CLAUDE.md` | Protocolo obrigatorio para IAs |
| Arquitetura | `dev-journey/01-getting-started/ARCHITECTURE.md` | Visao geral do sistema |
| Changelog | `dev-journey/03-changelog/CHANGELOG.md` | Historico de mudancas |
| Config | `config.py` | Todas as configuracoes do app |
| Entry Point | `main.py` | Ponto de entrada (orquestrador) |
| Auditoria | `AUDITORIA_EXTERNA_2025-12-30.md` | Estado atual do projeto |
| Scorecard | `SCORECARD.md` | Metricas e scores |

---

## Pacotes Modularizados

### Soul (Logica de IA)

| Pacote | Responsabilidade |
|--------|------------------|
| `src/soul/boca/` | TTS - sintese de voz |
| `src/soul/consciencia/` | Cerebro - LLM e processamento |
| `src/soul/visao/` | Vision - analise de imagens |
| `src/soul/threading_manager/` | Gerenciamento de threads |

### Core (Infraestrutura)

| Pacote | Responsabilidade |
|--------|------------------|
| `src/core/animation/` | Animacoes ASCII |
| `src/core/profiler/` | Profiling de performance |
| `src/core/ollama_client/` | Cliente Ollama |
| `src/core/logging_config.py` | Logging centralizado |
| `src/core/entity_loader.py` | Carrega entidades |
| `src/core/session.py` | Sessoes de usuario |

### Data Memory (Persistencia)

| Pacote | Responsabilidade |
|--------|------------------|
| `src/data_memory/smart_memory/` | Memoria semantica vetorial |
| `src/data_memory/entity_memory.py` | Memoria por entidade |
| `src/data_memory/vector_store_optimized.py` | Armazenamento de vetores |

### UI (Interface)

| Pacote | Responsabilidade |
|--------|------------------|
| `src/ui/dashboard/` | Debug dashboard |
| `src/ui/theme_manager/` | Sistema de temas |
| `src/ui/user_profiler/` | Profiling de usuario |
| `src/ui/screens.py` | Telas (History, Canone) |
| `src/ui/banner.py` | Widget de animacao |
| `src/ui/widgets.py` | Componentes reutilizaveis |

---

## Fluxo de Dados Principal

```
                    +------------------+
                    |     Usuario      |
                    +--------+---------+
                             |
              +==============v===============+
              |        main.py               |
              |    (TemploDaAlma App)        |
              +==============+===============+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v--------+ +--------v--------+ +--------v--------+
|   voice_system  | |   UI Widgets    | |   entity_loader |
| (audio_threads) | |  (banner.py)    | | (panteao/*.json)|
+--------+--------+ +--------+--------+ +--------+--------+
         |                   |                   |
         +-------------------+-------------------+
                             |
              +==============v===============+
              |      consciencia/            |
              |   (Processamento Central)    |
              |                              |
              |  +------------------------+  |
              |  | UniversalLLM           |  |
              |  | (Gemini/Ollama)        |  |
              |  +------------------------+  |
              |                              |
              |  +------------------------+  |
              |  | SmartMemory            |  |
              |  | (Vetorial + Emocional) |  |
              |  +------------------------+  |
              +==============+===============+
                             |
              +==============v===============+
              |         boca/                |
              |   (TTS: Coqui/Chatterbox)    |
              +==============+===============+
                             |
                    +--------v---------+
                    |  Audio Output    |
                    +------------------+
```

---

## Comandos Uteis

### Desenvolvimento
```bash
# Ativar ambiente
source venv/bin/activate

# Rodar aplicacao
python main.py

# Rodar testes
pytest src/tests/ -v

# Testes rapidos (sem GPU)
CUDA_VISIBLE_DEVICES="" pytest src/tests/ -v --tb=short

# Lint
./venv/bin/ruff check src/

# Format
./venv/bin/ruff format src/
```

### Pre-commit
```bash
# Instalar hooks
./venv/bin/pre-commit install

# Rodar todos os hooks
./venv/bin/pre-commit run --all-files
```

### Git
```bash
# Status
git status

# Criar branch de feature
git checkout -b feat/nome-da-feature

# Commit padrao
git commit -m "tipo(escopo): descricao curta"
```

---

## Convencoes do Projeto

### Nomenclatura
- **Classes**: PascalCase (`SmartMemory`, `EntityLoader`)
- **Funcoes/Metodos**: snake_case (`process_interaction`, `get_status`)
- **Constantes**: UPPER_SNAKE (`MAX_CONTEXT_CHARS`, `TTS_ENGINE`)
- **Privados**: Prefixo `_` (`_ensure_loaded`, `_fallback_to_luna`)

### Estrutura de Arquivos
```
src/
├── soul/           # Logica de IA (consciencia, TTS, STT)
├── core/           # Infraestrutura (logging, session, entity)
├── data_memory/    # Sistema de memoria
├── ui/             # Interface Textual
├── app/            # Bootstrap e mixins do app
├── tools/          # Scripts auxiliares
├── logs/           # Logs de execucao
└── tests/          # Testes unitarios
```

### Padroes de Codigo
1. **Type hints** em funcoes publicas
2. **Logging** via `get_logger(__name__)`
3. **Configuracao** via `config.py` (nunca hardcode)
4. **Erros** sempre logados, nunca silenciosos
5. **Locks** via `file_lock.py` (nunca `threading.Lock` manual em arquivos)

### Limites
- Max **300 linhas** por arquivo novo (God Mode Prevention)
- Arquivos legados listados em `src/tools/legacy_files.txt`
- Pre-commit bloqueia arquivos muito grandes

---

## Estrutura de Entidades

### Localizacao
```
src/assets/panteao/
├── registry.json           # Lista de entidades disponiveis
└── entities/
    ├── luna/
    │   ├── config.json     # Configuracao da entidade
    │   ├── alma.txt        # System prompt
    │   ├── animations/     # Animacoes ASCII (.txt.gz)
    │   └── voice/          # Arquivos de voz de referencia
    ├── eris/
    ├── juno/
    ├── lars/
    ├── mars/
    └── somn/
```

### Trocar Entidade
```python
from src.core.entity_loader import set_active_entity, get_active_entity

current = get_active_entity()  # "luna"
set_active_entity("eris")      # Troca para Eris
```

---

## Providers LLM

### Hierarquia de Fallback
```
CHAT_PROVIDER=local:
  1. Ollama (local) -> priority=0
  2. Gemini (cloud) -> priority=1

CHAT_PROVIDER=gemini:
  1. Gemini (cloud) -> priority=0
  2. Ollama (local) -> priority=1
```

### Circuit Breaker
- 3 falhas consecutivas = provider desabilitado
- Reset automatico apos sucesso
- Callback `on_fallback` notifica troca

---

## Memoria

### Categorias
- `USER_INFO`: Nome, profissao, familia
- `PREFERENCE`: Gostos, preferencias
- `FACT`: Informacoes factuais
- `EVENT`: Acontecimentos
- `EMOTION`: Estados emocionais

### TTLs
- L1 Cache: 2 horas
- L2 Cache (SQLite): 24 horas
- Memorias antigas: compactadas apos 30 dias

---

## Testes

### Estrutura
```
src/tests/
├── conftest.py              # Fixtures globais
├── test_consciencia.py      # Testes do cerebro
├── test_smart_memory.py     # Testes de memoria
├── test_universal_llm.py    # Testes de providers
├── test_entity_loader.py    # Testes de entidades
└── ...
```

### Rodar Testes Especificos
```bash
# Um arquivo
pytest src/tests/test_consciencia.py -v

# Uma classe
pytest src/tests/test_consciencia.py::TestConsciencia -v

# Um metodo
pytest src/tests/test_consciencia.py::TestConsciencia::test_init -v
```

---

## Pre-commit Hooks (17)

| # | Hook | Descricao |
|---|------|-----------|
| 01 | Anonimato | Sem nomes de IAs no codigo |
| 02 | IDs Externos | Sem UUIDs/hashes pessoais |
| 03 | Dados de teste | Dados anonimos em testes |
| 04 | Testes existem | Novos modulos devem ter teste |
| 05 | Qualidade dos testes | Sem assert True ou pass |
| 06 | Except silenciosos | Sempre logar excecoes |
| 07 | Lock manual | Usar file_lock.py |
| 08 | God Mode | Max 300 linhas novos arquivos |
| 09 | Codigo orfao | Modulos devem ser importados |
| 10 | Logger obrigatorio | Usar get_logger, nao print |
| 11 | Ruff lint | Erros criticos bloqueados |
| 12 | Ruff format | Formatacao automatica |

---

## Links Uteis

- **Changelog**: `dev-journey/03-changelog/`
- **Guias**: `dev-journey/06-guides/`
- **Estrutura de entidades**: `dev-journey/04-implementation/ENTITY_STRUCTURE.md`
- **Scripts de validacao**: `scripts/validate_all.sh`
- **Arquivos legados**: `src/tools/legacy_files.txt`
