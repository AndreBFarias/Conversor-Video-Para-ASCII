# O Que Estamos Construindo

> **TL;DR:** Luna e uma assistente de IA gotica com personalidade marcante, interface TUI animada, capacidades multimodais (texto, voz, visao) e memoria persistente.

## Contexto

Assistentes de IA convencionais sao genericas, sem personalidade, com interfaces corporativas sem alma. Luna quebra esse padrao sendo tecnicamente competente e esteticamente distinta - uma engenheira de dados gotica que fala portugues brasileiro.

---

## O Que e Luna

### Identidade

Luna nao e uma assistente qualquer. Ela tem:

1. **Personalidade Gotica** - Sarcastica, tecnica, direta
2. **Estetica Dark Tech** - Interface TUI com tema Dracula, efeitos glitch
3. **Voz Propria** - Fala em portugues brasileiro, sem emojis ou formalidades vazias
4. **Memoria Afetiva** - Lembra de conversas e rostos

### Diferenciais

| Caracteristica | Luna | Assistentes Genericas |
|----------------|------|----------------------|
| Personalidade | Gotica, sarcastica, unica | Neutra, corporativa |
| Interface | TUI animada com ASCII art | Web/App padrao |
| Multimodalidade | Texto + Voz + Visao | Geralmente apenas texto |
| Memoria | Vetorial persistente | Contexto de sessao |
| Privacidade | Dados locais | Cloud obrigatorio |
| Customizacao | Open source, extensivel | Fechado |

---

## Capacidades Tecnicas

### 1. Chat por Texto

- Processamento via Google Gemini API
- Cache semantico para respostas similares
- Rate limiting inteligente
- Suporte a markdown e code blocks

### 2. Chamada de Voz

- **Speech-to-Text**: Faster-Whisper (local, GPU/CPU)
- **Text-to-Speech**: Coqui (local), ElevenLabs (cloud), Piper (local)
- **VAD**: WebRTC Voice Activity Detection
- Latencia otimizada (~1s de silencio para processar)

### 3. Visao Computacional

- Captura de webcam via OpenCV
- Reconhecimento facial com face_recognition
- Deteccao de mudancas com imagehash
- Descricao de cena via Gemini Vision

### 4. Memoria Persistente

- Embeddings semanticos (Sentence-Transformers)
- Historico de sessoes em JSON
- Rostos conhecidos em pickle
- Perfil de usuario

### 5. Interface TUI

- Framework Textual (Python)
- 12 animacoes ASCII por emocao
- Efeitos glitch e decrypt
- Visualizador de audio em tempo real
- Tema Dark Dracula

---

## Publico Alvo

### Usuarios Primarios

1. **Desenvolvedores** - Que querem uma IA local e customizavel
2. **Entusiastas de Linux** - Que preferem terminal a interfaces graficas
3. **Privacidade-Conscientes** - Que nao querem dados na cloud
4. **Makers** - Que querem hackear e estender funcionalidades

### Usuarios Secundarios

1. **Estudantes de IA** - Para aprender sobre multimodalidade
2. **Criadores de Conteudo** - Que querem uma IA com personalidade
3. **Gamers/Streamers** - Que apreciam estetica dark/gotica

---

## Casos de Uso

### 1. Assistente de Desenvolvimento

```
Usuario: "Luna, analisa esse codigo e sugere melhorias"
Luna: [Recebe codigo, analisa com Gemini, sugere refatoracao]
```

### 2. Companhia de Trabalho

```
Usuario: [Ativa modo voz]
Usuario: "Luna, o que voce acha desse design?"
Luna: [Captura tela, descreve, opina com sarcasmo caracteristico]
```

### 3. Organizacao Pessoal

```
Usuario: "Luna, o que conversamos sobre aquele projeto semana passada?"
Luna: [Busca no historico semantico, retorna contexto]
```

### 4. Reconhecimento de Presenca

```
[Pessoa entra no campo de visao da webcam]
Luna: "Ola Andre. Faz 3 dias que nao nos falamos."
```

---

## Stack Tecnica

### Core

| Componente | Tecnologia | Funcao |
|------------|------------|--------|
| LLM | Google Gemini | Processamento de linguagem |
| STT | Faster-Whisper | Transcricao de voz |
| TTS | Coqui/ElevenLabs/Piper | Sintese de voz |
| Vision | OpenCV + Gemini Vision | Processamento visual |
| UI | Textual (Rich) | Interface terminal |

### Infraestrutura

| Componente | Tecnologia | Funcao |
|------------|------------|--------|
| Embeddings | Sentence-Transformers | Memoria semantica |
| Cache | Semantic Cache | Otimizacao de API |
| Threading | Python Threading | Paralelismo |
| Config | python-dotenv | Configuracao |

---

## Arquitetura Simplificada

```
                    +------------------+
                    |     Usuario      |
                    +--------+---------+
                             |
           +-----------------+-----------------+
           |                 |                 |
     [Texto]           [Voz]             [Visao]
           |                 |                 |
           v                 v                 v
    +------+------+   +------+------+   +------+------+
    |   Input     |   |   Whisper   |   |   OpenCV    |
    |   Handler   |   |   STT       |   |   Vision    |
    +------+------+   +------+------+   +------+------+
           |                 |                 |
           +-----------------+-----------------+
                             |
                             v
                    +--------+--------+
                    |   Consciencia   |
                    |   (Gemini LLM)  |
                    +--------+--------+
                             |
                             v
                    +--------+--------+
                    |      Boca       |
                    |     (TTS)       |
                    +--------+--------+
                             |
                             v
                    +--------+--------+
                    |    Interface    |
                    |   (Textual UI)  |
                    +-----------------+
```

---

## Roadmap Resumido

| Versao | Foco | Status |
|--------|------|--------|
| v1.0 | Chat texto basico | Concluido |
| v2.0 | Multimodalidade (voz, visao) | Concluido |
| v3.0 | Memoria vetorial, cache | Atual |
| v4.0 | Plugins, automacao | Planejado |

---

## Links Relacionados

- [Para Onde Queremos Ir](./WHERE_WE_WANT_TO_GO.md) - Visao de longo prazo
- [Roadmap Detalhado](./ROADMAP.md) - Fases e marcos
- [Arquitetura](../01-getting-started/ARCHITECTURE.md) - Diagrama tecnico
- [Quick Start](../01-getting-started/QUICK_START.md) - Como comecar

---
*Ultima atualizacao: 2025-12-18*
