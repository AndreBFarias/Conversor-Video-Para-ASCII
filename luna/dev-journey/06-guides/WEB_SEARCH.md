# WebSearch - Vasculhando as Entranhas da Rede

## Visao Geral

O modulo WebSearch permite que Luna busque informacoes em tempo real na internet.
Luna descreve essa habilidade como "vasculhar as entranhas da rede" ou "ler o obituario digital do mundo".

## Arquitetura

```
src/tools/web_search.py
│
├── WebSearch (classe principal)
│   ├── search()           # Busca geral
│   ├── search_news()      # Busca de noticias
│   ├── format_for_prompt() # Formata para injecao
│   └── detect_search_intent() # Detecta necessidade de busca
│
└── Integracao
    └── src/soul/consciencia.py
        └── _process_web_search()
```

## Como Funciona

### 1. Deteccao de Intencao (#9)

O campo `pesquisa_web` no JSON de resposta indica quando Luna precisa buscar dados:

```json
{
  "fala_tts": "Deixa eu vasculhar as entranhas da rede...",
  "pesquisa_web": "placar jogo Corinthians hoje",
  ...
}
```

### 2. Fluxo de Busca

1. Usuario pergunta algo que requer dados em tempo real
2. LLM retorna JSON com `pesquisa_web` preenchido
3. `_process_web_search()` executa a busca
4. Resultados sao injetados no prompt
5. LLM gera resposta final com os dados

### 3. Provedor de Busca (#5)

Usa DuckDuckGo por padrao (sem API key necessaria):

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = ddgs.text(query, region="br-pt", max_results=5)
```

## Uso

### Busca Simples

```python
from src.tools.web_search import get_web_search

ws = get_web_search()
results = ws.search("cotacao dolar hoje")

for r in results:
    print(f"{r.title}: {r.snippet}")
```

### Busca de Noticias

```python
results = ws.search_news("inteligencia artificial", max_results=10)
```

### Formatar para Prompt

```python
formatted = ws.format_for_prompt(results, max_chars=1500)
# Retorna texto pronto para injecao no prompt do LLM
```

## Configuracao

No `.env`:

```bash
# Nenhuma configuracao necessaria - usa DuckDuckGo (gratuito)

# Opcional: ajustar cache
WEB_SEARCH_CACHE_TTL=3600
WEB_SEARCH_CACHE_SIZE=100
```

## Instalacao

```bash
pip install duckduckgo_search
```

## Exemplos de Uso

### Placar de Jogos

```
Usuario: "Qual o placar do jogo do Flamengo?"
Luna: { "pesquisa_web": "placar jogo Flamengo hoje" }
[Busca executada]
Luna: "Vasculhei o obituario digital do mundo. Flamengo 2x1..."
```

### Noticias

```
Usuario: "O que esta acontecendo no mundo?"
Luna: { "pesquisa_web": "noticias ultimas horas" }
[Busca executada]
Luna: "Li nas entranhas da rede. Hoje o mundo..."
```

### Cotacoes

```
Usuario: "Quanto esta o dolar?"
Luna: { "pesquisa_web": "cotacao dolar real hoje" }
[Busca executada]
Luna: "Consultei as runas do mercado. O dolar esta..."
```

## Marcadores no Codigo

| Marcador | Funcao |
|----------|--------|
| #1 | Usa DuckDuckGo (privacidade) |
| #2 | Verifica dependencia instalada |
| #3 | Rate limiting entre requests |
| #4 | Executa busca principal |
| #5 | Busca via DuckDuckGo |
| #6 | Fallback quando DuckDuckGo falha |
| #6.1 | Fallback Ollama (modelos locais) |
| #7 | Busca especifica para noticias |
| #8 | Formata resultados para prompt |
| #9 | Detecta intencao de busca |

## Fallback Ollama (v4.2)

Quando DuckDuckGo nao esta disponivel, o sistema tenta usar modelos locais via Ollama:

### Modelos Suportados (ordem de prioridade)

1. `qwen2.5:7b` - Melhor conhecimento geral
2. `llama3.1:8b` - Alternativa robusta
3. `dolphin-mistral` - Modelo padrao da Luna
4. `llama3.2:3b` - Fallback leve

### Comportamento

```
[DuckDuckGo indisponivel]
         ↓
[Verifica Ollama rodando]
         ↓
[Busca modelo disponivel]
         ↓
[Gera resposta com conhecimento do modelo]
         ↓
[Retorna como SearchResult com source="ollama:modelo"]
```

### Limitacoes do Fallback

- Nao tem acesso a dados em tempo real (placar, cotacao)
- Conhecimento limitado ao treinamento do modelo
- Pode ser mais lento que DuckDuckGo
- Depende do Ollama estar rodando localmente
