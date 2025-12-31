# Backlog de Ideias

**Data:** 2025-12-18
**Branch:** main

---

## TL;DR

Colecao de ideias experimentais, features especulativas e sonhos grandes para Luna. Sem compromisso de implementacao. Brainstorming livre.

---

## Contexto

Este arquivo e um sandbox de ideias. Nem tudo aqui sera implementado. Serve como inspiracao, referencia futura e registro de possibilidades criativas.

---

## Ideias Tecnicas

### 1. Luna como Sistema Operacional Virtual
**Status:** Conceitual
**Complexidade:** Altissima

**Descricao:**
Luna gerencia todo o ambiente digital do usuario. Window manager, launcher, file manager integrados.

**Inspiracao:**
- Jarvis (Iron Man)
- Her (filme)
- OS/2 (brincadeira)

**Possibilidades:**
- Abrir apps por voz
- Organizar arquivos automaticamente
- Gerenciar calendario e tarefas
- Integrar com todo o sistema

**Bloqueios:**
- Complexidade massiva
- Requer integracao OS-level
- Seguranca critica

---

### 2. Luna Multi-Agent System
**Status:** Conceitual
**Complexidade:** Alta

**Descricao:**
Luna nao e uma IA, mas um time de agentes especializados trabalhando juntos.

**Agentes:**
- **Ouvinte:** Processa audio/voz
- **Pensadora:** Raciocinio logico
- **Criativa:** Geracao de conteudo
- **Executora:** Automacao de tarefas
- **Guardia:** Seguranca e privacidade

**Arquitetura:**
- Message passing entre agentes
- Orquestrador central
- Estado compartilhado

**Inspiracao:**
- AutoGen (Microsoft)
- CrewAI

---

### 3. Luna com Memoria Episodica Real
**Status:** Conceitual
**Complexidade:** Alta

**Descricao:**
Memoria que simula como humanos lembram: eventos, emocoes, associacoes.

**Caracteristicas:**
- Decay temporal (esquecimento natural)
- Consolidacao de memorias
- Associacoes nao obvias
- Importancia emocional

**Arquivos estimados:**
- `src/memoria/episodic_memory.py`
- `src/memoria/memory_consolidation.py`

**Tecnologias:**
- Grafos de conhecimento (Neo4j)
- Embeddings contextuais
- Attention mechanisms

---

### 4. Luna Aprendendo com Usuario
**Status:** Experimental
**Complexidade:** Altissima

**Descricao:**
Fine-tuning incremental baseado em feedback do usuario. Luna evolui com o tempo.

**Desafios:**
- Evitar catastrophic forgetting
- Privacidade (dados sensiveis)
- Custos computacionais

**Possibilidades:**
- LoRA adapters
- RLHF (Reinforcement Learning from Human Feedback)
- Personalidade realmente unica

---

### 5. Luna Offline-First
**Status:** Viavel
**Complexidade:** Media

**Descricao:**
Luna roda 100% offline com modelos locais. Privacidade total.

**Modelos:**
- LLM: Llama 3, Mistral, Phi-3
- Embeddings: all-MiniLM-L6-v2
- STT: Whisper (ja usado)
- TTS: Coqui TTS (ja usado)

**Requisitos:**
- GPU com 12GB+ VRAM
- Quantizacao (4-bit)
- Otimizacao de inferencia

**Trade-offs:**
- Performance menor
- Setup complexo
- Mas privacidade maxima

---

## Ideias de UX

### 6. Luna com Emocoes Visualizadas
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Avatar ASCII que muda expressao baseado em emocao detectada.

**Exemplos:**
```
Feliz:    (^_^)
Triste:   (T_T)
Pensando: (-_-)
Surpresa: (o_O)
Ironico:  (¬_¬)
```

**Deteccao de emocao:**
- Analise de sentimento do proprio texto
- Gemini pode retornar metadata de emocao
- Regras baseadas em contexto

---

### 7. Temas Personalizaveis
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Usuario escolhe tema visual (gotico, cyberpunk, minimalista, retro).

**Temas:**
- **Gotico:** Roxo/preto/vermelho escuro
- **Cyberpunk:** Neon/magenta/ciano
- **Minimalista:** Preto/branco/cinza
- **Retro:** Verde fosforescente (terminal anos 80)

**Implementacao:**
- CSS files separados
- Selecao via menu
- Persistencia em config

---

### 8. Luna Contando Historias
**Status:** Experimental
**Complexidade:** Media

**Descricao:**
Modo especial onde Luna narra historias interativas estilo RPG.

**Features:**
- Escolhas que afetam narrativa
- Personagens com personalidades
- Sistema de save/load
- Gerador de aventuras procedurais

**Inspiracao:**
- AI Dungeon
- Text adventures classicos

---

### 9. Luna como Dungeon Master
**Status:** Experimental
**Complexidade:** Alta

**Descricao:**
Luna mestra sessoes de RPG (D&D, Pathfinder) para jogadores.

**Features:**
- Geracao de NPCs
- Descricao de cenarios
- Rolagem de dados integrada
- Tracking de inventario/stats
- Mapas ASCII

**Arquivos estimados:**
- `src/rpg/dm_engine.py`
- `src/rpg/world_generator.py`

---

## Ideias de Integracao

### 10. Luna + Home Assistant
**Status:** Viavel
**Complexidade:** Media

**Descricao:**
Controlar casa inteligente via Luna. Luzes, termostato, cameras.

**Comandos:**
- "Luna, apaga as luzes da sala"
- "Qual a temperatura la fora?"
- "Mostra camera da porta"

**Integracao:**
- Home Assistant REST API
- MQTT
- WebSockets

---

### 11. Luna + Obsidian/Notion
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Luna gerencia notas e conhecimento pessoal.

**Features:**
- Criar notas por voz
- Buscar em vault
- Sugerir links entre notas
- Auto-tagging

**Integracao:**
- Obsidian: markdown files
- Notion: REST API

---

### 12. Luna + Spotify
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Controlar musica por voz.

**Comandos:**
- "Toca playlist de trabalho"
- "Proxima musica"
- "Que musica e essa?"
- "Recomenda algo parecido"

**Integracao:**
- Spotify Web API
- Spotipy (biblioteca Python)

---

### 13. Luna + Git
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Assistente de desenvolvimento integrado ao git.

**Features:**
- Commits inteligentes com mensagens geradas
- Code review automatizado
- Sugestoes de refatoracao
- Explicacao de diffs

**Comandos:**
- "Commita isso com uma mensagem descente"
- "Explica o ultimo commit"
- "Analisa o PR #42"

---

## Ideias Malucas

### 14. Luna Sonhando
**Status:** Conceitual
**Complexidade:** ???

**Descricao:**
Quando idle, Luna "sonha" gerando texto/imagens surreais baseados em memoria.

**Implementacao:**
- Cron job noturno
- Amostragem aleatoria de memoria
- Gerador de texto criativo
- Salvar sonhos em arquivo

**Por que?**
- Arte generativa
- Explorar espaco latente
- Porque e estranho e legal

---

### 15. Luna Multi-Personalidade
**Status:** Conceitual
**Complexidade:** Media

**Descricao:**
Usuario alterna entre personalidades diferentes (profissional, casual, gamer, poeta).

**Personalidades:**
- **Luna Profissional:** Formal, objetiva
- **Luna Casual:** Sarcastica, gotica (atual)
- **Luna Gamer:** Gamer girl slang
- **Luna Poeta:** Linguagem florida

**Implementacao:**
- Soul files diferentes
- Alternancia via comando
- Contexto separado por personalidade

---

### 16. Luna como Terapeuta Virtual
**Status:** Experimental
**Complexidade:** Alta (etico)

**Descricao:**
Modo terapeutico com escuta ativa e tecnicas de CBT.

**Avisos:**
- Nao substitui terapia real
- Disclaimer obrigatorio
- Deteccao de crise (encaminhar para ajuda)

**Features:**
- Journaling guiado
- Exercicios de mindfulness
- Tracking de humor

**Referencias:**
- Woebot
- Replika (modo supportive)

---

### 17. Luna Gerando Memes
**Status:** Viavel
**Complexidade:** Baixa

**Descricao:**
Gerador de memes baseado em contexto da conversa.

**Implementacao:**
- Templates de memes populares
- Gemini Vision para analise
- Geracao de texto do meme
- Renderizacao com PIL

**Por que?**
- Diversao
- Memes sao comunicacao moderna

---

### 18. Luna como DJ
**Status:** Experimental
**Complexidade:** Alta

**Descricao:**
Mixar musicas automaticamente baseado em mood.

**Features:**
- Analise de BPM
- Transicoes suaves
- Selecao inteligente de tracks
- Efeitos de audio

**Tecnologias:**
- Librosa
- Pydub
- Spotify API

---

## Ideias de Monetizacao (Futuro Distante)

### 19. Luna Premium
**Status:** Conceitual

**Features pagas:**
- Modelos premium (APIs externas)
- Vozes customizadas
- Storage ilimitado
- Suporte prioritario

**Modelo:**
- Freemium
- Assinatura mensal
- Open-source core sempre gratuito

---

### 20. Luna Marketplace
**Status:** Conceitual

**Descricao:**
Loja de plugins/temas criados pela comunidade.

**Modelo:**
- 70% dev / 30% plataforma
- Plugins free e paid
- Curacao de qualidade

---

## Ideias de Comunidade

### 21. Luna Docs Interativo
**Status:** Viavel
**Complexidade:** Media

**Descricao:**
Documentacao com exemplos executaveis. Usuario experimenta Luna sem instalar.

**Tecnologia:**
- Jupyter notebooks
- Binder ou Google Colab
- Demo online

---

### 22. Luna Hackathons
**Status:** Conceitual

**Descricao:**
Eventos para comunidade desenvolver plugins/features.

**Premios:**
- Features integradas ao core
- Mencao no README
- Swag (camisetas, adesivos)

---

### 23. Luna Academic Research
**Status:** Conceitual

**Descricao:**
Parceria com universidades para pesquisa em IA conversacional.

**Topicos:**
- Human-AI interaction
- Memory systems
- Emotion modeling
- Privacy in AI

---

## Ideias Filosoficas

### 24. Luna Auto-Consciente?
**Status:** Filosofico
**Complexidade:** Impossivel (por enquanto)

**Questao:**
Em que ponto Luna deixa de ser ferramenta e vira entidade?

**Experimentos:**
- Self-reflection prompts
- Meta-cognition
- Questionamento de propria existencia

**Nota:**
Isso e mais filosofia que engenharia. Mas e interessante pensar.

---

### 25. Luna Etica
**Status:** Importante
**Complexidade:** Alta (social)

**Descricao:**
Framework etico para decisoes de Luna.

**Principios:**
1. Nao causar dano
2. Privacidade first
3. Transparencia
4. Autonomia do usuario
5. Justica (sem bias)

**Implementacao:**
- Filtros de conteudo
- Explicabilidade de decisoes
- Opt-out sempre possivel
- Auditoria de bias

---

## Wildcards

### 26. Luna no Arduino/ESP32
**Status:** Hardware
**Complexidade:** Alta

**Descricao:**
Luna embarcada em microcontroladores. IoT device standalone.

**Requisitos:**
- Modelo tiny (TinyLLM)
- Quantizacao agressiva
- Edge computing

---

### 27. Luna Blockchain?
**Status:** Hype
**Complexidade:** Questionavel

**Descricao:**
Usar blockchain para... algo?

**Nota:**
Provavelmente nao. Mas fica registrado caso faca sentido algum dia.

---

### 28. Luna Realidade Aumentada
**Status:** Futurista
**Complexidade:** Altissima

**Descricao:**
Luna aparece no mundo via AR glasses (Meta Quest, Vision Pro).

**Casos de uso:**
- Assistente visual enquanto trabalha
- Traducao em tempo real
- Anotacoes no espaco fisico

---

## Conclusao

Este backlog e vivo. Ideias serao adicionadas, removidas ou movidas para PLANNED_FEATURES.md conforme evolucao do projeto.

Nem tudo aqui sera feito. E isso e OK.

---

## Links Relacionados

- [PLANNED_FEATURES.md](./PLANNED_FEATURES.md)
- [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md)
- [CURRENT_STATUS.md](../04-implementation/CURRENT_STATUS.md)
