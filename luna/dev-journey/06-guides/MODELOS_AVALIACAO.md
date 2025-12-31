# Avaliacao de Modelos LLM para Luna

**Data:** 2024-12-20
**Hardware:** NVIDIA RTX 3050 (4GB VRAM)
**Objetivo:** Modelos que suportem personalidade complexa, JSON estruturado, portugues BR

---

## Requisitos do Projeto Luna

| Requisito | Peso | Descricao |
|-----------|------|-----------|
| Personalidade complexa | ALTO | Gotica, sarcastica, mantendo personagem |
| JSON estruturado | ALTO | Respostas SEMPRE em formato JSON valido |
| Portugues BR | ALTO | Fluencia nativa, sem anglicismos |
| NSFW/Uncensored | MEDIO | Sem censura de conteudo |
| Contexto 4K+ | MEDIO | Para leitura de documentos |
| Velocidade <15s | MEDIO | Resposta rapida em 4GB VRAM |
| VRAM <=4GB | CRITICO | Limite de hardware |

---

## Modelos Instalados - Avaliacao

### INADEQUADOS (Remover do install.sh)

| Modelo | Tamanho | Problema | Acao |
|--------|---------|----------|------|
| tinyllama | 637MB | Muito pequeno, nao segue instrucoes complexas, JSON instavel | REMOVER |
| minicpm-v | 5.5GB | EXCEDE 4GB VRAM, causa swap e lentidao | SUBSTITUIR por moondream |
| gemma2:2b | 1.6GB | Censura forte, recusa roleplay, JSON fraco | NAO INSTALAR |
| phi3:mini | 2.2GB | Censura moderada, nao ideal para roleplay | NAO INSTALAR |

### ADEQUADOS (Manter/Adicionar)

| Modelo | Tamanho | Categoria | Notas |
|--------|---------|-----------|-------|
| dolphin-mistral | 4.1GB | Chat/Roleplay | PRINCIPAL - uncensored, bom roleplay |
| nous-hermes2 | 4.1GB | Chat/Roleplay | Alternativa - bom contexto |
| dolphin-llama3 | 4.7GB | Chat/Roleplay | Alternativa uncensored |
| llama3.2:3b | 2.0GB | Chat Leve | Rapido, bom portugues |
| qwen2.5-coder:7b | 4.7GB | Codigo | Manter para code analysis |
| deepseek-coder:6.7b | 3.8GB | Codigo | Alternativa mais leve |
| moondream | 1.6GB | Visao | SUBSTITUIR minicpm-v |
| llava-phi3 | 2.9GB | Visao | Alternativa visao |

---

## Novos Modelos Recomendados

### Para Chat/Roleplay (PRIORIDADE)

1. **dolphin-mistral** (JA INSTALADO)
   - Tamanho: 4.1GB
   - Uncensored: SIM
   - Portugues: BOM
   - JSON: BOM
   - Comando: `ollama pull dolphin-mistral`

2. **nous-hermes2:mistral** (ADICIONAR)
   - Tamanho: 4.1GB
   - Especializado em roleplay e narrativa
   - Bom seguimento de instrucoes
   - Comando: `ollama pull nous-hermes2:mistral`

3. **dolphin-llama3** (ADICIONAR)
   - Tamanho: 4.7GB (precisa quantizado)
   - Uncensored, baseado em Llama 3
   - Melhor qualidade geral
   - Comando: `ollama pull dolphin-llama3:8b-q4_0`

4. **llama3.2:3b** (ADICIONAR)
   - Tamanho: 2.0GB
   - Muito rapido, bom para fallback
   - Portugues excelente
   - Comando: `ollama pull llama3.2:3b`

### Para Visao

1. **moondream** (SUBSTITUIR minicpm-v)
   - Tamanho: 1.6GB
   - Perfeito para 4GB VRAM
   - Descricao de imagens eficiente
   - Comando: `ollama pull moondream`

2. **llava-phi3** (ALTERNATIVA)
   - Tamanho: 2.9GB
   - Melhor qualidade que moondream
   - Ainda cabe em 4GB
   - Comando: `ollama pull llava-phi3`

### Para Codigo

1. **qwen2.5-coder:7b** (JA INSTALADO)
   - Tamanho: 4.7GB
   - Melhor modelo de codigo para Ollama
   - Suporte multilingual

2. **deepseek-coder:6.7b** (ALTERNATIVA)
   - Tamanho: 3.8GB
   - Mais leve, ainda muito capaz
   - Comando: `ollama pull deepseek-coder:6.7b`

---

## Configuracao Recomendada Final

### Modelos Essenciais (Obrigatorios)

```bash
ollama pull dolphin-mistral    # Chat principal (4.1GB)
ollama pull moondream          # Visao leve (1.6GB)
ollama pull llama3.2:3b        # Chat rapido/fallback (2.0GB)
```

### Modelos Opcionais (Se espaco permitir)

```bash
ollama pull nous-hermes2:mistral   # Roleplay alternativo (4.1GB)
ollama pull qwen2.5-coder:7b       # Codigo (4.7GB)
ollama pull llava-phi3             # Visao melhor (2.9GB)
```

---

## Configuracao .env Recomendada

```ini
# Chat (Modelos Locais)
CHAT_LOCAL_MODEL=dolphin-mistral
CHAT_LOCAL_CONTEXT=8192

# Visao (Modelos Locais)
VISION_LOCAL_MODEL=moondream

# Codigo (Modelos Locais)
CODE_LOCAL_MODEL=qwen2.5-coder:7b

# Fallback rapido
CHAT_FALLBACK_MODEL=llama3.2:3b
```

---

## Fontes

- [Best Uncensored LLM on Ollama](https://www.arsturn.com/blog/finding-the-best-uncensored-llm-on-ollama-a-deep-dive-guide)
- [Ollama Structured Outputs](https://ollama.com/blog/structured-outputs)
- [Ollama VRAM Requirements 2025](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)
- [Vision Models Ollama](https://ollama.com/search?c=vision)
- [Best Ollama Models 2025](https://collabnix.com/best-ollama-models-in-2025-complete-performance-comparison/)
