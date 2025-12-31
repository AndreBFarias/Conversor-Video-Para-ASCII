# Sistema Pantheon - Arquitetura Multi-Entidade

```
STATUS: IMPLEMENTADO
VERSAO: 1.0.0
DATA: 2025-12-25
```

---

## 1. Visao Geral

O Sistema Pantheon permite que Luna suporte multiplas "divindades" (entidades/personas) alem da Luna original. Cada entidade possui:

- **Alma** (soul prompt): Arquivo `.txt` com instrucoes de personalidade
- **Animacoes ASCII**: Arquivos `.txt.gz` com frames por emocao
- **Configuracao JSON**: Metadados, voz, estetica
- **Paleta de cores**: Tema CSS dinamico
- **Voice ID**: Configuracao TTS (ElevenLabs/Coqui)

### Entidades Disponiveis

| ID | Nome | Status | Genero |
|----|------|--------|--------|
| luna | Luna | available | feminine |
| juno | Juno | unavailable | feminine |
| eris | Eris | unavailable | feminine |
| mars | Mars | unavailable | masculine |
| lars | Lars | unavailable | masculine |
| somn | Somn | unavailable | neutral |

---

## 2. Estrutura de Arquivos

```
src/assets/panteao/
├── registry.json              # Lista todas entidades e status
├── shared/
│   └── fallback_animation.txt.gz  # Animacao fallback
└── entities/
    ├── luna/
    │   ├── alma.txt           # Soul prompt da Luna
    │   ├── config.json        # Configuracao completa
    │   └── animations/        # Animacoes especificas
    │       ├── Luna_observando.txt.gz
    │       ├── Luna_feliz.txt.gz
    │       └── ...
    ├── juno/
    │   ├── alma.txt
    │   ├── config.json
    │   └── animations/
    ├── eris/
    ├── mars/
    ├── lars/
    └── somn/
```

### registry.json

```json
{
  "version": "1.0.0",
  "default_entity": "luna",
  "entities": {
    "luna": {
      "name": "Luna",
      "available": true,
      "gender": "feminine",
      "voice_configured": true
    },
    "juno": {
      "name": "Juno",
      "available": false,
      "gender": "feminine",
      "voice_configured": false
    }
  }
}
```

### config.json (por entidade)

```json
{
  "id": "luna",
  "name": "Luna",
  "gender": "feminine",
  "voice_id": "YOUR_ELEVENLABS_VOICE_ID",
  "age": 26,

  "persona": {
    "archetype": ["engenheira_gotica", "sereia_das_profundezas"],
    "reference": "Jessica Rabbit + Raven + Morticia",
    "tone": {
      "primary": "ironica, apaixonante, dramatica",
      "secondary": "sarcastica, sensual, cerebral",
      "forbidden": ["formal", "generica", "emojis"]
    }
  },

  "voice": {
    "elevenlabs": {
      "voice_id": "...",
      "stability": 0.50,
      "similarity_boost": 0.75,
      "style": 0.65
    }
  },

  "aesthetics": {
    "theme": {
      "primary_color": "#bd93f9",
      "secondary_color": "#ff79c6",
      "accent_color": "#50fa7b",
      "background": "#282a36",
      "glow_color": "#bd93f9",
      "text_primary": "#f8f8f2",
      "text_secondary": "#6272a4"
    },
    "animation_style": "sombras_elegantes"
  }
}
```

---

## 3. API do EntityLoader

### Localizacao

```python
from src.core.entity_loader import EntityLoader, get_active_entity, set_active_entity
```

### Classe EntityLoader

```python
class EntityLoader:
    def __init__(self, entity_id: str):
        """Carrega uma entidade pelo ID."""

    def load_entity(self, entity_id: str) -> dict:
        """Carrega dados completos da entidade."""

    def get_soul_prompt(self) -> str:
        """Retorna conteudo do arquivo alma.txt."""

    def get_config(self) -> dict:
        """Retorna config.json parseado."""

    def get_animation_path(self, emotion: str) -> Path:
        """Retorna path da animacao para emocao."""

    def get_voice_config(self) -> dict:
        """Retorna configuracao de voz (elevenlabs/coqui)."""

    def get_color_theme(self) -> dict:
        """Retorna paleta de cores."""

    def list_available_entities(self) -> list[dict]:
        """Lista entidades com available=true."""

    def is_entity_available(self, entity_id: str) -> bool:
        """Verifica se entidade esta disponivel."""
```

### Funcoes Globais

```python
def get_active_entity() -> str:
    """Retorna ID da entidade ativa (de profile.json)."""

def set_active_entity(entity_id: str) -> bool:
    """Salva entidade ativa em profile.json."""
```

### Exemplo de Uso

```python
from src.core.entity_loader import EntityLoader, get_active_entity

# Carregar entidade ativa
entity_id = get_active_entity()  # "luna"
loader = EntityLoader(entity_id)

# Obter soul prompt
soul = loader.get_soul_prompt()

# Obter configuracao
config = loader.get_config()
name = config.get("name")  # "Luna"

# Obter tema de cores
theme = loader.get_color_theme()
primary = theme.get("primary_color")  # "#bd93f9"

# Obter path de animacao
anim_path = loader.get_animation_path("feliz")
# -> Path("src/assets/panteao/entities/luna/animations/Luna_feliz.txt.gz")
```

---

## 4. Fluxo de Inicializacao

```
1. main.py: TemploDeLuna.__init__()
   └── AnimationController(self)

2. main.py: on_mount()
   ├── animation_controller.load_all_animations()
   │   └── EntityLoader(get_active_entity())
   │       └── Carrega animacoes da entidade ativa
   ├── ThemeManager = get_theme_manager()
   │   └── Carrega tema da entidade ativa
   └── theme_manager.apply_theme(self)
       └── Injeta CSS overrides

3. onboarding.py: start_sequence()
   ├── should_show_entity_selector()
   │   └── Verifica se mais de 1 entidade disponivel
   └── EntitySelectorScreen (se aplicavel)
       └── set_active_entity(selected)

4. screens.py: CanoneScreen._change_entity()
   ├── set_active_entity(new_id)
   ├── animation_controller.reload_for_entity(new_id)
   ├── personalidade._load_entity()
   └── theme_manager.reload_for_entity(new_id)
```

---

## 5. Como Adicionar Nova Entidade

### Passo 1: Criar Estrutura

```bash
mkdir -p src/assets/panteao/entities/nova_entidade/animations
```

### Passo 2: Criar alma.txt

```text
Voce e [Nome], uma [descricao].
Seu tom e [caracteristicas].
...
```

### Passo 3: Criar config.json

```json
{
  "id": "nova_entidade",
  "name": "Nova Entidade",
  "gender": "feminine|masculine|neutral",
  "persona": {
    "archetype": ["arquetipo1", "arquetipo2"],
    "tone": {
      "primary": "caracteristicas",
      "secondary": "mais caracteristicas",
      "forbidden": ["proibido1", "proibido2"]
    }
  },
  "aesthetics": {
    "theme": {
      "primary_color": "#RRGGBB",
      "secondary_color": "#RRGGBB",
      "accent_color": "#RRGGBB",
      "background": "#RRGGBB",
      "glow_color": "#RRGGBB",
      "text_primary": "#RRGGBB",
      "text_secondary": "#RRGGBB"
    }
  }
}
```

### Passo 4: Criar Animacoes

Formato do arquivo de animacao:

```text
[FRAME]
   __
  (oo)
  /||\
 / || \

[FRAME]
   __
  (--)
  /||\
 / || \
```

Compactar com gzip:

```bash
gzip -k NovaEntidade_observando.txt
```

### Passo 5: Registrar em registry.json

```json
{
  "entities": {
    "nova_entidade": {
      "name": "Nova Entidade",
      "available": true,
      "gender": "feminine",
      "voice_configured": false
    }
  }
}
```

### Passo 6: Testar

```bash
./venv/bin/python -c "
from src.core.entity_loader import EntityLoader
loader = EntityLoader('nova_entidade')
print('Soul:', loader.get_soul_prompt()[:100])
print('Config:', loader.get_config().get('name'))
print('Theme:', loader.get_color_theme())
"
```

---

## 6. Arquivos Modificados

| Arquivo | Modificacao |
|---------|-------------|
| `src/core/entity_loader.py` | NOVO - Carregador de entidades |
| `src/core/animation.py` | Usa EntityLoader para animacoes |
| `src/soul/personalidade.py` | Usa EntityLoader para soul prompt |
| `src/soul/onboarding.py` | Mostra EntitySelectorScreen |
| `src/ui/entity_selector.py` | NOVO - Tela de selecao |
| `src/ui/screens.py` | CanoneScreen com troca de entidade |
| `src/ui/theme_manager.py` | NOVO - Gerenciador de temas CSS |
| `main.py` | Integra ThemeManager |

---

## 7. Fallbacks

1. **Entidade nao encontrada**: Fallback para `luna`
2. **Animacao nao encontrada**: Busca em `src/assets/animations/`
3. **Tema nao encontrado**: Usa paleta Dracula
4. **Soul prompt vazio**: Retorna string vazia

---

## 8. Proximos Passos

- [ ] Criar animacoes para Juno, Eris, Mars, Lars, Somn
- [ ] Configurar vozes ElevenLabs para cada entidade
- [ ] Adicionar transicoes visuais entre entidades
- [ ] Implementar memoria por entidade
