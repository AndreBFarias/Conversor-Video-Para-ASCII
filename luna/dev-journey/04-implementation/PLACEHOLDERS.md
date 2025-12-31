# Placeholders do Projeto

> **TL;DR:** Lista de todas as funcoes, classes e features que existem como placeholder aguardando implementacao completa.

## Contexto

Este documento mapeia codigo que precisa de atencao: funcoes ainda nao implementadas, TODOs deixados durante desenvolvimento, exception handlers silenciosos e pontos que precisam de refatoracao.

---

## O que e um Placeholder?

Placeholder e um trecho de codigo que:
- Existe na estrutura mas nao faz nada (`pass`, `return None`, `TODO`)
- Tem implementacao parcial/mock
- Esta comentado aguardando desenvolvimento
- Retorna dados fake/hardcoded
- Silencia excecoes sem tratamento (`except: pass`)

---

## Resumo Atual

| Categoria | Placeholders | Status Geral |
|-----------|--------------|--------------|
| Audio/Voz | 4 | Exception handlers |
| Visao | 1 | Exception handler |
| UI | 5 | Exception handlers + stub |
| Core | 1 | Exception handler |
| Orquestrador | 6 | Exception handlers + stub |
| Cache | 1 | **Funcao nao implementada** |
| **TOTAL** | **18** | - |

---

## Mapa de Placeholders

### [CATEGORIA: Audio/Voz]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `except: pass` | `src/soul/boca.py` | 217 | Silent | Remove arquivo temp apos TTS Coqui |
| `except: pass` | `src/soul/boca.py` | 273 | Silent | Remove arquivo temp apos TTS ElevenLabs |
| `except: pass` | `src/soul/boca.py` | 326 | Silent | Remove arquivo temp apos TTS Piper |
| `except: pass` | `src/soul/audio_threads.py` | 118 | Silent | Atualiza visualizador de audio |

**Analise:** Estes sao exception handlers para operacoes de cleanup. O padrao e aceitavel para remocao de arquivos temporarios - se falhar, nao e critico.

---

### [CATEGORIA: Visao]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `except: pass` | `src/soul/visao.py` | 229 | Silent | Comparacao de hash de imagem |

**Analise:** Exception handler durante deteccao de mudancas visuais. Continua execucao mesmo se comparacao falhar.

---

### [CATEGORIA: UI]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `except: pass` | `src/ui/emotion_manager.py` | 26 | Silent | Query de widget de emocao |
| `except: pass` | `src/ui/intro_animation.py` | 259 | Silent | Interrupcao de animacao intro |
| `except: pass` | `src/ui/intro_animation.py` | 281 | Silent | Interrupcao de animacao intro |
| `pass` | `src/ui/banner.py` | 342 | Stub | Condicional para set_text (nunca executa) |
| `except: pass` | `src/ui/banner.py` | 438 | Silent | Atualizacao de label de emocao |
| `except: pass` | `src/ui/banner.py` | 452 | Silent | Atualizacao de static |

**Analise:** A maioria sao handlers para falhas de UI nao-criticas. O `pass` na linha 342 e um stub dentro de condicional - codigo morto que pode ser removido.

---

### [CATEGORIA: Core]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `except: pass` | `src/core/animation.py` | 26 | Silent | Parse de numero de frames |
| `except: pass` | `src/soul/onboarding.py` | 48 | Silent | Leitura de perfil de usuario |

**Analise:** Handlers para parse de dados que podem falhar graciosamente.

---

### [CATEGORIA: Cache]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `set_l2()` | `src/soul/semantic_cache.py` | 95 | **TODO** | Cache L2 nao implementado |

**Analise:** **UNICO PLACEHOLDER REAL QUE PRECISA IMPLEMENTACAO.** O cache L2 (persistencia em disco/redis) esta declarado mas vazio.

---

### [CATEGORIA: Orquestrador (main.py)]

| Placeholder | Arquivo | Linha | Status | Descricao |
|-------------|---------|-------|--------|-----------|
| `py_error_handler()` | `main.py` | 18 | Stub | Handler de erros ALSA (intencional) |
| `except: pass` | `main.py` | 23 | Silent | Fallback se ALSA nao disponivel |
| `except: pass` | `main.py` | 189 | Silent | Log de stats de visao |
| `except: pass` | `main.py` | 197 | Silent | Log de stats de API |
| `except: pass` | `main.py` | 643 | Silent | Start chaos mode |
| `except: pass` | `main.py` | 886 | Silent | Stop do timer de olhar |

**Analise:** O `py_error_handler()` e um stub intencional para suprimir mensagens de erro ALSA no Linux. Os outros sao handlers de logging/UI nao-criticos.

---

## Status Possiveis

| Status | Significado | Acao |
|--------|-------------|------|
| **TODO** | Nao iniciado, so tem assinatura | Implementar |
| **Parcial** | Funciona mas incompleto | Completar |
| **Mock** | Retorna dados fake para testes | Substituir |
| **Silent** | Silencia excecao | Avaliar se precisa log |
| **Stub** | Placeholder intencional | Manter ou remover |
| **Deprecated** | Vai ser removido | Remover |
| **Blocked** | Aguardando dependencia | Aguardar |

---

## Como Encontrar Placeholders

```bash
# Busca completa
grep -rn "TODO" src/
grep -rn "FIXME" src/
grep -rn "pass$" src/ --include="*.py"
grep -rn "NotImplementedError" src/

# Ou use o script automatico
python src/tools/find_placeholders.py
```

---

## Detalhamento dos Placeholders Criticos

### `set_l2()` - Cache L2 Nao Implementado

**Arquivo:** `src/soul/semantic_cache.py:95`

**Codigo Atual:**

```python
def set_l2(self, text: str, response: Any):
    pass
```

**Proposito:** Persistir cache semantico em disco ou Redis para sobreviver a restarts da aplicacao.

**Implementacao Sugerida:**

```python
def set_l2(self, text: str, response: Any):
    cache_file = self.cache_dir / f"{hash(text)}.json"
    with open(cache_file, 'w') as f:
        json.dump({
            'text': text,
            'response': response,
            'timestamp': time.time()
        }, f)
```

**Dependencias:**
- Decidir entre: JSON local, SQLite, ou Redis
- Definir TTL para entradas
- Implementar `get_l2()` correspondente

**Prioridade:** Media (cache L1 em memoria ja funciona)

---

### `py_error_handler()` - Handler ALSA

**Arquivo:** `main.py:18`

**Codigo Atual:**

```python
def py_error_handler(filename, line, function, err, fmt):
    pass
```

**Proposito:** Suprimir mensagens de erro verbosas da biblioteca ALSA no Linux. E intencional e nao deve ser alterado.

**Prioridade:** Nenhuma (funcionando como esperado)

---

## Priorizacao

### Alta Prioridade (Implementar)

| Placeholder | Arquivo | Justificativa |
|-------------|---------|---------------|
| `set_l2()` | semantic_cache.py | Unica funcao realmente incompleta |

### Baixa Prioridade (Avaliar)

| Placeholder | Arquivo | Justificativa |
|-------------|---------|---------------|
| `pass` em banner.py:342 | banner.py | Codigo morto, pode remover |
| Exception handlers | varios | Considerar adicionar logging |

### Manter Como Esta

| Placeholder | Arquivo | Justificativa |
|-------------|---------|---------------|
| `py_error_handler()` | main.py | Supressao intencional de ALSA |
| Cleanup handlers | boca.py | Remocao de temp files |

---

## Historico de Reducao

| Data | Total | Criticos | Silenciosos |
|------|-------|----------|-------------|
| 2025-12-10 | 25 | 5 | 20 |
| 2025-12-15 | 20 | 3 | 17 |
| 2025-12-18 | 18 | 1 | 17 |

**Tendencia:** Placeholders criticos reduzidos de 5 para 1.

---

## Regras de Placeholder

### Quando Usar

1. **TODO:** Funcionalidade planejada mas adiada
2. **FIXME:** Bug conhecido que nao e critico
3. **except: pass:** APENAS para erros realmente nao-criticos
4. **Stub:** Para APIs que precisam existir antes da implementacao

### Quando NAO Usar

1. Nunca `except: pass` em codigo de producao sem justificativa
2. Nunca deixar TODOs sem contexto (`# TODO: fix this`)
3. Nunca acumular mais de 5 placeholders criticos por modulo

### Formato Recomendado

```python
# TODO: Implementar cache L2 com Redis
#   Contexto: Cache L1 funciona mas perde dados no restart
#   Dependencia: Decidir entre Redis/SQLite
#   Prioridade: Media
def set_l2(self, text: str, response: Any):
    pass
```

---

## Links Relacionados

- [CURRENT_STATUS.md](./CURRENT_STATUS.md) - Status geral
- [TECHNICAL_DEBT.md](../05-future/TECHNICAL_DEBT.md) - Divida tecnica
- [find_placeholders.py](../../src/tools/find_placeholders.py) - Script de varredura
- [METRICS.md](../07-metrics/METRICS.md) - Metricas do projeto

---
*Ultima atualizacao: 2025-12-18*
