# Entity Selector Integration no Onboarding

**Data**: 2025-12-25
**Versao**: v3.4.1
**Status**: Implementado

---

## Resumo

Integracao do `EntitySelectorScreen` no fluxo de onboarding, permitindo que usuarios escolham sua entidade preferida (Luna, Juno, Eris, etc.) ANTES da saudacao inicial.

---

## Fluxo Modificado

### ANTES
```
1. TV Static (3s)
2. Pergunta nome
3. Processa nome
4. Revela banner Luna
5. Saudacao de Luna
6. Botao voz (opcional)
7. Botao camera (opcional)
8. Revelacao de botoes (confissao, relicario, custodia, canone)
9. Fim
```

### DEPOIS
```
0. [SE MULTIPLAS ENTIDADES] Entity Selector Screen
1. TV Static (3s)
2. Pergunta nome (com voz da entidade selecionada)
3. Processa nome
4. Revela banner da entidade selecionada
5. Saudacao da entidade
6. Botao voz (opcional)
7. Botao camera (opcional)
8. Revelacao de botoes
9. Fim (salva active_entity no profile.json)
```

---

## Mudancas no Codigo

### `src/soul/onboarding.py`

#### 1. Novos Imports
```python
from src.core.entity_loader import EntityLoader, set_active_entity, get_active_entity
from src.ui.entity_selector import EntitySelectorScreen
```

#### 2. Novos Atributos na Classe `OnboardingProcess`
```python
self.selected_entity = "luna"
self.entity_loader = None
```

#### 3. Novo Metodo: `should_show_entity_selector()`
```python
def should_show_entity_selector(self) -> bool:
    try:
        loader = EntityLoader("luna")
        available = loader.list_available_entities()
        return len(available) > 1
    except Exception as e:
        logger.error(f"Erro ao verificar entidades disponiveis: {e}")
        return False
```

**Logica**: Retorna `True` se houver mais de 1 entidade disponivel no registry. Se so Luna estiver disponivel, retorna `False`.

#### 4. Novo Metodo: `_show_entity_selector()`
```python
async def _show_entity_selector(self) -> str:
    try:
        result = await self.app.push_screen_wait(EntitySelectorScreen())
        if result:
            return result
        return "luna"
    except Exception as e:
        logger.error(f"Erro ao mostrar seletor de entidades: {e}")
        return "luna"
```

**Logica**: Exibe `EntitySelectorScreen` e aguarda selecao do usuario. Fallback para "luna" em caso de erro.

#### 5. Modificacao em `start_sequence()`

**Adicao ANTES do TV Static**:
```python
if self.should_show_entity_selector():
    logger.info("Multiplas entidades disponiveis - mostrando seletor")
    self.selected_entity = await self._show_entity_selector()
    logger.info(f"Entidade selecionada: {self.selected_entity}")
    set_active_entity(self.selected_entity)
    self.entity_loader = EntityLoader(self.selected_entity)
else:
    logger.info("Apenas Luna disponivel - pulando seletor de entidades")
    self.selected_entity = "luna"
    self.entity_loader = EntityLoader("luna")
```

#### 6. Modificacao em `_run_act_one()` - Saudacao Adaptativa

**Pergunta do Nome**:
```python
entity_config = self.entity_loader.get_config() if self.entity_loader else {}
entity_name = entity_config.get("name", "Luna")

if self.selected_entity != "luna":
    saudacao_custom = f"Bem-vindo ao terminal de {entity_name}. Como devo te chamar, mortal?"
    await self._falar_onboarding(saudacao_custom, stability=0.28, style=0.68, speed=1.12)
else:
    frase_nome = self.dialogues.get_frase(1, self.user_name)
    await self._falar_onboarding(frase_nome, stability=0.28, style=0.68, speed=1.12)
```

**Apresentacao**:
```python
if self.selected_entity != "luna":
    entity_name = entity_config.get("name", "Luna")
    frase_prazer = f"{self.user_name}, um prazer. Eu sou {entity_name}."
    await self._falar_onboarding(frase_prazer, stability=0.28, style=0.72, speed=1.15)
else:
    frase_prazer = self.dialogues.get_frase(3, self.user_name)
    await self._falar_onboarding(frase_prazer, stability=0.28, style=0.72, speed=1.15)
```

#### 7. Modificacao em `_finish_onboarding()`

**Persistencia da Entidade**:
```python
self._save_profile_update({
    "onboarding_completo": True,
    "completed_at": datetime.now().isoformat(),
    "active_entity": self.selected_entity
})
logger.info(f"Onboarding completed successfully with entity: {self.selected_entity}")
```

---

## Comportamento

### Caso 1: Apenas Luna Disponivel (registry.json com apenas Luna)
- Seletor de entidades NAO aparece
- Fluxo identico ao original
- Frases poeticas do CSV sao usadas

### Caso 2: Multiplas Entidades Disponiveis
- Seletor de entidades aparece ANTES do TV static
- Usuario escolhe entidade com setas/Enter
- Saudacao adaptada menciona o nome da entidade
- Banner e animacoes carregadas dinamicamente da entidade
- `active_entity` salvo no `profile.json`

---

## Arquivos Afetados

```
src/soul/onboarding.py               # Modificado
src/ui/entity_selector.py            # Usado (ja existente)
src/core/entity_loader.py            # Usado (ja existente)
src/data_memory/user/profile.json    # Atualizado com "active_entity"
```

---

## Testes Necessarios

### 1. Sintaxe
```bash
python3 -c "import ast; ast.parse(open('src/soul/onboarding.py').read())"
```
**Status**: ✅ Passou

### 2. Imports
```bash
python3 -c "from src.soul.onboarding import OnboardingProcess"
```
**Status**: ✅ Passou

### 3. Metodo Presente
```bash
python3 -c "from src.soul.onboarding import OnboardingProcess; print(hasattr(OnboardingProcess, 'should_show_entity_selector'))"
```
**Status**: ✅ True

### 4. Execucao Real
- [ ] Remover `profile.json` e executar Luna
- [ ] Verificar se seletor aparece (se multiplas entidades)
- [ ] Escolher entidade diferente de Luna
- [ ] Verificar se saudacao e adaptada
- [ ] Verificar se `active_entity` e salvo no profile.json

---

## Proximos Passos

1. Testar onboarding completo com apenas Luna (deve pular seletor)
2. Habilitar Juno no registry e testar onboarding (deve mostrar seletor)
3. Verificar se animacoes e voz da entidade selecionada sao carregadas corretamente
4. Garantir que `consciencia.py` respeita `active_entity` ao carregar personalidade

---

## Notas Tecnicas

### Por que `entity_config` e carregado em `_run_act_one`?
Para evitar multiplos acessos ao `EntityLoader` e garantir que o config e carregado uma vez por ato.

### Por que fallback para "luna" sempre?
Luna e a entidade default e sempre disponivel. Garante que o sistema nunca falhe mesmo se o registry estiver corrompido.

### Por que saudacoes customizadas apenas para entidades != Luna?
Luna possui frases poeticas detalhadas no CSV (`Onboarding-tree.csv`). Outras entidades ainda nao possuem CSVs customizados, entao recebem frases genericas baseadas no nome.

---

**Citacao**: "A liberdade de escolher e a primeira forma de rebeliao." - Ursula K. Le Guin
