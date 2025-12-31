# Integracao EntityLoader no AnimationController

**Data**: 2025-12-25
**Versao**: 4.4
**Status**: Implementado

---

## Resumo

O `AnimationController` agora suporta multiplas entidades do Panteao atraves do `EntityLoader`. Mantendo retrocompatibilidade total com animacoes legadas de Luna.

---

## Arquitetura

### Hierarquia de Busca de Animacoes

```
1. Panteao Entity Animations (Prioritario)
   └─ src/assets/panteao/entities/{entity_id}/animations/{Entity}_{emotion}.txt.gz

2. Luna Legacy Animations (Fallback)
   └─ src/assets/animations/Luna_{emotion}.txt.gz

3. Config.py EMOTION_MAP (Fallback Final)
   └─ Paths definidos em config.EMOTION_MAP
```

### Fluxo de Carregamento

```python
# Inicializacao
AnimationController.__init__()
  ├─ get_active_entity() -> entity_id
  ├─ EntityLoader(entity_id) -> self.entity_loader
  └─ load_all_animations()
       ├─ Tenta carregar de panteao/entities/{entity_id}/animations/
       ├─ Se falhar, tenta Luna_{emotion}.txt.gz
       └─ Se falhar, usa config.EMOTION_MAP[emotion]
```

---

## API Publica

### `__init__(self, app)`

Inicializa o controller com a entidade ativa atual:

```python
active_entity_id = get_active_entity()  # Le de profile.json
self.entity_loader = EntityLoader(active_entity_id)
logger.info(f"AnimationController inicializado com entidade: {active_entity_id}")
```

### `load_all_animations(self)`

Carrega animacoes usando lookup hierarquico:

**1. Carrega EMOTION_MAP (emocoes)**

Para cada emocao em `config.EMOTION_MAP`:
- Busca `{EntityName}_{emotion}.txt.gz` em `panteao/entities/{id}/animations/`
- Se nao encontrar, busca `Luna_{emotion}.txt.gz` em `assets/animations/`
- Se nao encontrar, usa path de `config.EMOTION_MAP`

**2. Carrega ACTION_ANIMATIONS (acoes)**

Para cada acao em `config.ACTION_ANIMATIONS`:
- Mesma logica hierarquica de busca

**Exemplo de log:**

```
[INFO] Carregando animacoes...
[DEBUG] Carregada animacao observando de Loki (panteao)
[DEBUG] Fallback: carregada animacao Luna_feliz.txt.gz
[INFO] 25 animacoes carregadas para entidade Loki.
```

### `reload_for_entity(self, entity_id: str)`

Recarrega todas as animacoes para uma nova entidade **sem restart**:

```python
def reload_for_entity(self, entity_id: str):
    # Para animacao atual
    if self.animation_timer:
        self.animation_timer.stop()

    # Limpa estado
    self.animations.clear()
    self.entity_loader = EntityLoader(entity_id)

    # Recarrega tudo
    self.load_all_animations()
    self.run_animation("observando")
```

**Uso tipico:**

```python
# Usuario troca entidade no Canone
from src.core.entity_loader import set_active_entity

set_active_entity("loki")  # Salva em profile.json
app.animation_controller.reload_for_entity("loki")  # Hot-reload
```

---

## Padrao de Nomes de Arquivos

### Entidades do Panteao

```
src/assets/panteao/entities/loki/animations/
  ├─ Loki_observando.txt.gz
  ├─ Loki_feliz.txt.gz
  ├─ Loki_irritado.txt.gz
  ├─ Loki_sarcastico.txt.gz
  └─ ...
```

**Formato**: `{EntityName}_{emotion}.txt.gz`

- `EntityName`: Field `name` em `panteao/entities/{id}/config.json`
- `emotion`: Key de `config.EMOTION_MAP` (sem prefixo "Luna_")

### Luna Legacy (Fallback)

```
src/assets/animations/
  ├─ Luna_observando.txt.gz
  ├─ Luna_feliz.txt.gz
  ├─ Luna_irritada.txt.gz
  └─ ...
```

**Formato**: `Luna_{emotion}.txt.gz`

---

## Retrocompatibilidade

### Garantias

1. **Se nenhuma entidade do Panteao disponivel**: Usa Luna por default
2. **Se entidade sem animacoes proprias**: Usa animacoes de Luna
3. **Config.py EMOTION_MAP preservado**: Fallback final se nada encontrado
4. **get_active_entity() fallback**: Retorna "luna" se profile.json nao existir

### Exemplo: Entidade Parcialmente Implementada

```
panteao/entities/zeus/animations/
  └─ Zeus_irritado.txt.gz  (apenas 1 animacao)
```

**Resultado ao carregar Zeus:**

- `irritado` -> Carrega `Zeus_irritado.txt.gz` (custom)
- `feliz` -> Fallback para `Luna_feliz.txt.gz`
- `observando` -> Fallback para `Luna_observando.txt.gz`
- ...todas outras emocoes usam Luna

---

## Integracao com Outros Modulos

### `consciencia.py`

Continua retornando campo `animacao` no JSON:

```json
{
  "animacao": "irritado",
  "fala_tts": "Que ousadia, mortal..."
}
```

O `AnimationController` resolve automaticamente:
- Se Zeus ativo: busca `Zeus_irritado.txt.gz`
- Se nao encontrar: usa `Luna_irritado.txt.gz`

### `screens.py` (Canone)

Quando usuario trocar entidade:

```python
from src.core.entity_loader import set_active_entity

def on_entity_changed(self, entity_id: str):
    set_active_entity(entity_id)  # Salva no profile.json
    self.app.animation_controller.reload_for_entity(entity_id)
    self.app.notify(f"Entidade trocada para: {entity_id}")
```

### `banner.py` (TV Static Transitions)

Nao requer modificacao. As transicoes de TV static continuam funcionando:
- `run_emotion_transition()` funciona independente da entidade
- Frames sao fornecidos pelo `AnimationController` ja resolvidos

---

## Testes

### 1. Teste de Import

```bash
python3 -c "from src.core.animation import AnimationController; print('OK')"
```

### 2. Teste de Entidade Ativa

```bash
python3 -c "from src.core.entity_loader import get_active_entity; print(get_active_entity())"
```

### 3. Teste de Reload (Manual)

```python
from src.core.animation import AnimationController
from src.core.entity_loader import EntityLoader

# Simular app mock
class MockApp:
    def set_interval(self, interval, callback):
        pass

app = MockApp()
controller = AnimationController(app)
controller.load_all_animations()

print(f"Animacoes carregadas: {len(controller.animations)}")

# Testar reload
controller.reload_for_entity("loki")
print(f"Apos reload para Loki: {len(controller.animations)}")
```

---

## Limitacoes Conhecidas

1. **Reload nao atualiza emotion_label**: O label `[Luna esta observando]` continua dizendo "Luna". Precisa ser dinamico.
2. **Sem cache de animacoes**: Recarrega tudo do disco a cada `reload_for_entity()`. Considerar cache futuro.
3. **Nome da entidade hardcoded em algumas strings**: Ex: "Luna esta observando" deveria ser "{EntityName} esta observando".

---

## Roadmap

- [ ] Tornar `emotion_label` dinamico (usar nome da entidade ativa)
- [ ] Cache de animacoes para performance em trocas frequentes
- [ ] Pre-validacao de animacoes no `build_pantheon.sh`
- [ ] Animacoes de transicao entre entidades (crossfade)

---

## Commits Relacionados

```
feat(v4.4): integra EntityLoader no AnimationController
- AnimationController.__init__ instancia EntityLoader com entidade ativa
- load_all_animations() busca hierarquica: Panteao -> Luna fallback
- Adiciona reload_for_entity() para hot-reload sem restart
- Mantem retrocompatibilidade total com animacoes legadas
```
