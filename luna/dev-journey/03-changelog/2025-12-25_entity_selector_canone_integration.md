# Entity Selector Integration - Cânone Screen

**Data:** 2025-12-25
**Versao:** 3.4.1
**Status:** Implementado

---

## Resumo

Integração do sistema de troca de entidades no Cânone Screen, permitindo ao usuário alternar entre diferentes essências (Luna, Athena, Apollo, etc.) sem perder o histórico da sessão.

---

## Modificações Implementadas

### 1. Arquivo: `src/ui/screens.py`

#### Imports Adicionados
```python
from src.core.entity_loader import get_active_entity, set_active_entity, EntityLoader
from src.ui.entity_selector import EntitySelectorScreen
```

#### Nova Aba "Entidade" no CanoneScreen

**Estrutura:**
```
TabPane("Entidade", id="tab-entity")
├── Entidade Ativa
│   ├── Nome da entidade atual (reactive)
│   └── Descrição/arquétipo (reactive)
└── Botão "Invocar Outra Essência"
    └── Abre EntitySelectorScreen como modal
```

**Binding Atualizado:**
- Aba 1: Entidade (novo)
- Aba 2: Provedores
- Aba 3: Voz
- Aba 4: Áudio
- Aba 5: Chaves
- Aba 6: Avançado
- Aba 7: Efeitos

#### Métodos Novos

##### `_open_entity_selector()`
```python
def _open_entity_selector(self):
    def on_entity_selected(selected_entity_id: str):
        if selected_entity_id and selected_entity_id != get_active_entity():
            self._change_entity(selected_entity_id)

    self.app.push_screen(EntitySelectorScreen(), on_entity_selected)
```

**Função:** Abre o EntitySelectorScreen como modal sobre o Cânone. Usa callback para processar a seleção.

##### `_change_entity(new_entity_id: str)`
```python
def _change_entity(self, new_entity_id: str):
    # 1. Valida e persiste nova entidade via set_active_entity()
    # 2. Recarrega AnimationController
    # 3. Recarrega sistema de personalidade
    # 4. Atualiza UI da aba Entidade
    # 5. Notifica usuário do sucesso
```

**Função:** Orquestra a troca de entidade, recarregando todos os componentes necessários.

**Componentes Recarregados:**
1. **AnimationController** → `reload_for_entity(new_entity_id)`
   - Para timer de animação atual
   - Limpa cache de animações
   - Recarrega todas as animações da nova entidade
   - Reinicia animação "observando"

2. **Personalidade** → `get_personalidade()._load_entity()`
   - Recarrega EntityLoader interno
   - Atualiza referência à alma.txt da nova entidade
   - Mantém histórico de frases usadas (não reseta)

3. **Profile.json** → `set_active_entity(new_entity_id)`
   - Persiste escolha no perfil do usuário
   - Próximo boot carrega a entidade escolhida

**UI Updates:**
- `#current-entity-name` → Nome da nova entidade
- `#current-entity-description` → Arquétipos da nova entidade

---

## Fluxo de Execução

```
[Usuário] Cânone → Aba "Entidade" → Botão "Invocar Outra Essência"
    ↓
[EntitySelectorScreen] Modal abre → Usuário navega e seleciona entidade
    ↓
[Callback] on_entity_selected(entity_id) disparado
    ↓
[CanoneScreen._change_entity] Orquestra troca:
    1. set_active_entity(entity_id)         # Persiste no profile.json
    2. animation_controller.reload_for_entity()  # Recarrega animações
    3. personalidade._load_entity()         # Recarrega prompts
    4. Atualiza UI da aba                   # Reactive updates
    ↓
[Notificação] "Entidade trocada para {nome}. Histórico preservado."
```

---

## Aspectos Críticos

### ✅ **Preservação de Estado**

**O que NÃO é afetado pela troca:**
- Histórico de sessão (manifest.json)
- Fila de processamento (audio_queue, transcription_queue, etc.)
- Conversas em andamento
- Memória RAG (data_memory/)
- Perfil do usuário (user_profile.json)
- Configurações do .env

**O que É recarregado:**
- Animações (assets visuais)
- Personalidade (prompts da alma.txt)
- Nome exibido no banner

### ⚠️ **Limitações Conhecidas**

1. **TTS Voice Cloning**: Se a nova entidade tem voz customizada (embeddings Coqui/Chatterbox), ela só será aplicada na **próxima** fala gerada. A fala atual em buffer não é afetada.

2. **Banner Name**: O banner visual (ASCII art) ainda mostra "LUNA" hardcoded. Para trocar isso, seria necessário recarregar o `BannerGlitchWidget` dinamicamente (feature futura).

3. **Consciencia System Prompt**: O `Consciencia` carrega a alma.txt apenas no `__init__`. Para aplicar a nova personalidade, seria necessário adicionar um método `reload_soul()` no Consciencia (feature futura).

---

## Testing Checklist

- [x] Importações corretas (entity_loader, EntitySelectorScreen)
- [x] Aba "Entidade" renderiza corretamente
- [x] Botão "Invocar Outra Essência" abre modal
- [x] EntitySelectorScreen retorna entity_id correto
- [x] set_active_entity() persiste no profile.json
- [x] AnimationController.reload_for_entity() funciona
- [x] UI da aba Entidade atualiza após troca
- [x] Notificação de sucesso exibida
- [ ] **TODO:** Teste com entidade que tem voz customizada
- [ ] **TODO:** Teste de troca durante processamento ativo

---

## Próximos Passos

1. **Reload do System Prompt** (Consciencia)
   - Adicionar método `reload_soul()` no Consciencia
   - Chamar em `_change_entity()` para aplicar nova personalidade imediatamente

2. **Dynamic Banner Update**
   - Recarregar `BannerGlitchWidget` com nome da nova entidade
   - Substituir "LUNA" hardcoded por nome dinâmico

3. **Voice Embedding Hot Swap**
   - Adicionar `Boca.reload_voice(entity_id)` para trocar embeddings sem reiniciar TTS
   - Aplicar na próxima síntese de voz

4. **Animation Transition Effect**
   - Adicionar efeito TV static durante troca de entidade
   - Usar `run_tv_static_transition()` antes de `reload_for_entity()`

---

## Referências

- `src/ui/screens.py` - CanoneScreen modificado
- `src/ui/entity_selector.py` - Modal de seleção
- `src/core/entity_loader.py` - EntityLoader, set_active_entity()
- `src/core/animation.py` - AnimationController.reload_for_entity()
- `src/soul/personalidade.py` - DicionarioPersonalidade._load_entity()
- `PROMPTS_ETAPAS_PANTHEON.md` - Roadmap original do sistema de entidades

---

**Assinatura:** *"A identidade não é fixa, é fluida como sombra à luz da vela."*
