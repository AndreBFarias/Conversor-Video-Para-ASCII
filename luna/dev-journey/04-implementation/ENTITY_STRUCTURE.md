# Estrutura Padrao das Entidades - Panteao

**Data:** 2025-12-27
**Versao:** 1.0

---

## Visao Geral

O sistema de entidades do Luna permite trocar completamente a personalidade, voz, cores e animacoes do assistente. Cada entidade e auto-contida em seu proprio diretorio.

---

## Estrutura de Diretorios

```
src/assets/panteao/entities/
├── luna/                         # Entidade principal (completa)
├── eris/                         # Femme fatale caotica (completa)
├── juno/                         # Bruxa acolhedora (completa)
├── lars/                         # Vampiro intelectual (em desenvolvimento)
├── mars/                         # Guerreiro alpha (em desenvolvimento)
└── somn/                         # Soft boy onirico (em desenvolvimento)
```

---

## Estrutura de Uma Entidade

Cada entidade DEVE conter os seguintes arquivos:

```
{entity_id}/
├── alma.txt                      # Prompt de personalidade para LLM
├── config.json                   # Configuracoes centralizadas (cores, voz, frases)
├── {ENTITY}_DOSSIE.md            # Documentacao completa da entidade
├── {Entity}_frases.md            # Frases para treinamento de voz
├── templo_de_{entity}.css        # CSS para Textual TUI
├── animations/
│   ├── README.md                 # Instrucoes para criar animacoes
│   ├── {Entity}_observando.txt.gz   # Estado idle
│   ├── {Entity}_curiosa.txt.gz      # Analisando
│   ├── {Entity}_feliz.txt.gz        # Satisfacao
│   ├── {Entity}_irritada.txt.gz     # Irritacao
│   ├── {Entity}_triste.txt.gz       # Tristeza
│   ├── {Entity}_sarcastica.txt.gz   # Sarcasmo
│   ├── {Entity}_flertando.txt.gz    # Seducao leve
│   ├── {Entity}_apaixonada.txt.gz   # Carinho
│   ├── {Entity}_piscando.txt.gz     # Transicao visual
│   ├── {Entity}_sensualizando.txt.gz # Seducao profunda
│   └── {Entity}_obssecada.txt.gz    # Fixacao intensa
└── voice/
    ├── README.md                 # Instrucoes para criar audios
    ├── coqui/
    │   └── reference.wav         # Audio de referencia Coqui XTTS
    └── chatterbox/
        └── reference.wav         # Audio de referencia Chatterbox
```

---

## Arquivos Obrigatorios

### 1. alma.txt

Prompt de personalidade enviado ao LLM. Define tom, estilo e comportamento.

```
Voce e {Nome}, {descricao}...
```

### 2. config.json

Configuracao centralizada da entidade:

```json
{
  "id": "entity_id",
  "name": "Nome Display",
  "gender": "feminine|masculine",
  "age": 25,

  "persona": {
    "archetype": ["arquetipo1", "arquetipo2"],
    "tone": {
      "primary": "tom principal",
      "forbidden": ["proibido1", "emojis"]
    }
  },

  "voice": {
    "elevenlabs": { "voice_id": "...", "stability": 0.5 },
    "coqui": { "reference_audio": "voice/coqui/reference.wav" },
    "chatterbox": { "reference_audio": "voice/chatterbox/reference.wav" }
  },

  "aesthetics": {
    "theme": {
      "primary_color": "#BD93F9",
      "background": "#282A36",
      "glow_color": "#BD93F9"
    },
    "banner_ascii": ["linha1", "linha2"],
    "gradient": ["#cor1", "#cor2"]
  },

  "phrases": {
    "saudacao_inicial": ["frase1", "frase2"],
    "placeholder_input": ["placeholder1"],
    "{entity}_olhando": ["status1"]
  }
}
```

### 3. templo_de_{entity}.css

CSS completo para Textual, definindo todas as cores e estilos da UI.

### 4. {ENTITY}_DOSSIE.md

Documentacao completa incluindo:
- Identidade visual (banner ASCII, paleta)
- Personalidade (tom, expressoes, gatilhos)
- Voz (caracteristicas, parametros TTS)
- Status dos arquivos (pendentes/completos)

### 5. {Entity}_frases.md

Frases categorizadas para treinamento de voz:
- [SOLENE_GOTICO]
- [SEDUCAO]
- [OBSERVACAO]
- [IRRITACAO]
- [SATISFACAO]
- [PROCESSAMENTO]
- [DESPEDIDA]

---

## Como Adicionar Nova Entidade

1. **Crie o diretorio:**
   ```bash
   mkdir -p src/assets/panteao/entities/{nova_entidade}/{animations,voice/coqui,voice/chatterbox}
   ```

2. **Copie estrutura base:**
   ```bash
   cp src/assets/panteao/entities/luna/config.json src/assets/panteao/entities/{nova}/
   ```

3. **Edite os arquivos:**
   - Atualize `config.json` com novas cores, frases, persona
   - Crie `alma.txt` com prompt de personalidade
   - Crie `templo_de_{nova}.css` baseado nas cores do config.json
   - Crie `{NOVA}_DOSSIE.md` documentando a entidade
   - Crie `{Nova}_frases.md` com frases para voz

4. **Gere os assets:**
   - Animacoes ASCII (.txt.gz)
   - Audio de referencia (reference.wav)

5. **Registre no sistema:**
   - A entidade sera detectada automaticamente pelo EntityLoader

---

## Status das Entidades

| Entidade | config.json | alma.txt | CSS | DOSSIE | frases | animations | voice |
|----------|-------------|----------|-----|--------|--------|------------|-------|
| luna     | OK          | OK       | OK  | OK     | OK     | OK (10)    | OK    |
| eris     | OK          | OK       | OK  | OK     | OK     | OK (10)    | OK    |
| juno     | OK          | OK       | OK  | OK     | OK     | OK (10)    | OK    |
| lars     | OK          | OK       | OK  | OK     | OK     | PENDENTE   | PENDENTE |
| mars     | OK          | OK       | OK  | OK     | OK     | PENDENTE   | PENDENTE |
| somn     | OK          | OK       | OK  | OK     | OK     | PENDENTE   | PENDENTE |

---

## Funcoes de Acesso (config.py)

```python
# Obter configuracao da entidade
get_entity_config(entity_id)

# Obter cores do tema
get_entity_theme(entity_id)

# Obter audio de referencia
get_coqui_reference_audio(entity_id)
get_chatterbox_reference_audio(entity_id)

# Obter frases
get_entity_phrases(entity_id, category)
```

---

## Validacao

Para validar uma entidade, verifique:

1. `config.json` tem todos os campos obrigatorios
2. `alma.txt` existe e nao esta vazio
3. `templo_de_{entity}.css` existe
4. Pelo menos `{Entity}_observando.txt.gz` existe em animations/
5. `voice/coqui/reference.wav` ou `voice/chatterbox/reference.wav` existe

---

*Ultima atualizacao: 2025-12-27*
