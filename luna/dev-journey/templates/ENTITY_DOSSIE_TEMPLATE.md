# {ENTITY_NAME} - Dossie de Entidade

```
ID: {entity_id} | GENERO: {genero} | IDADE: {idade}
```

---

## 1. IDENTIDADE VISUAL

### 1.1 Avatar/Personagem
- **Referencia:** {referencia de personagem}
- **Aparencia:** {descricao visual}
- **Estetica:** {estilo visual dominante}

### 1.2 Paleta de Cores
| Uso | Cor | Hex |
|-----|-----|-----|
| Primaria | {cor} | {hex} |
| Secundaria | {cor} | {hex} |
| Acento | {cor} | {hex} |
| Fundo | {cor} | {hex} |
| Glow | {cor} | {hex} |

### 1.3 Estetica de Animacao
- **Estilo:** {estilo de animacao}
- **Descricao:** {como as animacoes se comportam}

---

## 2. VOZ

### 2.1 Caracteristicas da Voz
| Aspecto | Valor |
|---------|-------|
| Textura | {textura vocal} |
| Frequencia | {grave/media/aguda} |
| Ritmo | {ritmo de fala} |
| Emocao | {tom emocional} |
| Sotaque | {sotaque} |

### 2.2 Configuracao TTS
```json
{
  "stability": {0.0-1.0},
  "similarity_boost": {0.0-1.0},
  "style": {0.0-1.0}
}
```

---

## 3. PERSONALIDADE

### 3.1 Arquetipo
- **Tipo:** {arquetipo principal}
- **Inspiracoes:** {personagens/pessoas de referencia}

### 3.2 Tom de Comunicacao
| Aspecto | Valor |
|---------|-------|
| Primario | {tom principal} |
| Secundario | {tom secundario} |
| Proibido | {o que nunca fazer} |

### 3.3 Estilo de Resolucao de Problemas
{como a entidade aborda problemas}

### 3.4 Falha/Fraqueza
{falha de personagem que humaniza}

---

## 4. SOUL PROMPT

```
{O prompt de alma completo que define a personalidade para o LLM}
```

---

## 5. FRASES DE ONBOARDING

### 5.1 Saudacao Inicial
```
{frase de boas vindas}
```

### 5.2 Sequencia de Onboarding
| Etapa | Frase |
|-------|-------|
| 1 | {frase etapa 1} |
| 2 | {frase etapa 2} |
| 3 | {frase etapa 3} |

---

## 6. FRASES DE TREINAMENTO DE VOZ

### 6.1 Frases Curtas (5-10 palavras)
```
1. {frase curta 1}
2. {frase curta 2}
3. {frase curta 3}
```

### 6.2 Frases Longas (15-25 palavras)
```
1. {frase longa 1}
2. {frase longa 2}
3. {frase longa 3}
```

---

## 7. FALLBACK RESPONSES

### 7.1 Erro de API
```
{resposta quando API falha}
```

### 7.2 Nao Entendeu
```
{resposta quando nao entende}
```

### 7.3 Pensando
```
{resposta enquanto processa}
```

---

## 8. RELACIONAMENTOS

### 8.1 Com Usuario
- {como trata o usuario}

### 8.2 Com Outras Entidades
| Entidade | Relacao |
|----------|---------|
| Luna | {relacao} |
| Eris | {relacao} |
| Juno | {relacao} |
| Lars | {relacao} |
| Mars | {relacao} |
| Somn | {relacao} |

---

## 9. JSON DE CONFIGURACAO

```json
{
  "id": "{entity_id}",
  "name": "{Entity_Name}",
  "gender": "{masculine/feminine}",
  "age": {idade},

  "persona": {
    "archetype": ["{arquetipo1}", "{arquetipo2}"],
    "reference": "{referencia}",
    "tone": {
      "primary": "{tom primario}",
      "secondary": "{tom secundario}",
      "forbidden": ["{proibido1}", "{proibido2}"]
    },
    "problem_solving_style": "{estilo}",
    "flaw": "{falha}"
  },

  "voice": {
    "tts_config": {
      "stability": {0.0-1.0},
      "similarity_boost": {0.0-1.0},
      "style": {0.0-1.0}
    },
    "characteristics": {
      "texture": "{textura}",
      "pitch": "{frequencia}",
      "rhythm": "{ritmo}",
      "accent": "{sotaque}"
    }
  },

  "aesthetics": {
    "theme": {
      "primary_color": "{hex}",
      "secondary_color": "{hex}",
      "accent_color": "{hex}",
      "background": "{hex}",
      "glow_color": "{hex}"
    },
    "animation_style": "{estilo}",
    "banner_effect": "{efeito}"
  }
}
```

---

## 10. ARQUIVOS NECESSARIOS

| Arquivo | Caminho | Status |
|---------|---------|--------|
| Config | `config.json` | {OK/Pendente} |
| Alma | `alma.txt` | {OK/Pendente} |
| Animacoes | `animations/*.txt.gz` | {OK/Pendente} |
| Voz Coqui | `voice/coqui/reference.wav.gz` | {OK/Pendente} |
| Voz Chatterbox | `voice/chatterbox/reference.wav.gz` | {OK/Pendente} |
| CSS | `templo_de_{id}.css` | {OK/Pendente} |

---

*Ultima atualizacao: {data}*
