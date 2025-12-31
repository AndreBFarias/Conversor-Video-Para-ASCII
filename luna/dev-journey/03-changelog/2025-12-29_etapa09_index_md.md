# 2025-12-29: ETAPA 09 - INDEX.md para IAs

## Objetivo
Criar arquivo de referencia rapida para IAs trabalhando no projeto.

## Arquivo Criado

### INDEX.md (raiz do projeto)
Documento de ~300 linhas com:

#### 1. Navegacao Rapida
- Tabela de arquivos essenciais (CLAUDE.md, config.py, main.py)
- Tabela de modulos principais (soul/, data_memory/, ui/, core/)
- Indicacao de linhas por arquivo

#### 2. Fluxo de Dados Principal
- Diagrama ASCII mostrando:
  - Usuario -> main.py -> voice_system/UI/entity_loader
  - consciencia.py (UniversalLLM + SmartMemory)
  - boca.py (TTS) -> Audio Output

#### 3. Comandos Uteis
- Desenvolvimento (pytest, ruff, mypy)
- Pre-commit (install, run)
- Git (status, branch, commit)

#### 4. Convencoes do Projeto
- Nomenclatura (PascalCase, snake_case, UPPER_SNAKE)
- Estrutura de diretorios
- Padroes de codigo (type hints, logging, config)
- Limites (300 linhas max)

#### 5. Estrutura de Entidades
- Localizacao (src/assets/panteao/)
- Formato do config.json
- Como trocar entidade via codigo

#### 6. Providers LLM
- Hierarquia de fallback
- Circuit breaker (3 falhas = disable)

#### 7. Sistema de Memoria
- Categorias (USER_INFO, PREFERENCE, etc)
- Fluxo de retrieval
- TTLs (L1, L2, compactacao)

#### 8. Testes
- Estrutura de diretorios
- Comandos para rodar testes especificos

#### 9. Pre-commit Hooks
- Lista dos 13 hooks com stage (commit/push)

#### 10. Links Uteis
- Referencias para outros documentos do projeto

## Beneficios

1. **Onboarding rapido**: Nova IA entende projeto em minutos
2. **Navegacao direta**: Tabelas linkam para arquivos importantes
3. **Comandos prontos**: Copy-paste para tarefas comuns
4. **Contexto visual**: Diagrama ASCII mostra fluxo de dados
5. **Convencoes claras**: Evita inconsistencias de estilo

## Validacao

- [x] INDEX.md criado na raiz
- [x] Diagrama ASCII de fluxo incluido
- [x] Comandos uteis documentados
- [x] Convencoes do projeto listadas
- [x] Estrutura de entidades explicada
