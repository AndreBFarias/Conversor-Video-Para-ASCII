# Arquitetura de Troca de Entidade - Hot Swap System

**Data:** 2025-12-25
**Versão:** 3.4.1
**Componente:** Entity Management System

---

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                       CanoneScreen                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ TabPane: "Entidade"                                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ [Entidade Ativa]                                   │  │  │
│  │  │  Nome: Luna (reactive)                             │  │  │
│  │  │  Desc: engenheira_gotica, dark_feminine (reactive) │  │  │
│  │  │                                                     │  │  │
│  │  │ [Botão] "Invocar Outra Essência"                   │  │  │
│  │  │    onClick → _open_entity_selector()               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    push_screen(EntitySelectorScreen)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EntitySelectorScreen (Modal)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│  │  │  Luna   │  │ Athena  │  │ Apollo  │  │  ...    │     │  │
│  │  │ (atual) │  │   [N/A] │  │   [N/A] │  │         │     │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│  │                                                           │  │
│  │  ← → Navegar  •  Enter Selecionar  •  Esc Default Luna  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    dismiss(selected_entity_id)
                              ↓
                    on_entity_selected(entity_id)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               _change_entity(new_entity_id)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. set_active_entity(new_entity_id)                      │  │
│  │    └─> profile.json: {"active_entity": "athena"}         │  │
│  │                                                           │  │
│  │ 2. animation_controller.reload_for_entity(new_entity_id) │  │
│  │    ├─> Para timer atual                                  │  │
│  │    ├─> Limpa cache de animações                          │  │
│  │    ├─> Carrega animations/ da nova entidade              │  │
│  │    └─> Inicia "observando"                               │  │
│  │                                                           │  │
│  │ 3. get_personalidade()._load_entity()                    │  │
│  │    ├─> Recarrega EntityLoader interno                    │  │
│  │    └─> Atualiza referência ao alma.txt                   │  │
│  │                                                           │  │
│  │ 4. Atualiza UI (reactive)                                │  │
│  │    ├─> #current-entity-name → "Athena"                   │  │
│  │    └─> #current-entity-description → "warrior, wisdom"   │  │
│  │                                                           │  │
│  │ 5. Notifica usuário                                      │  │
│  │    └─> "Entidade trocada para Athena. Histórico..."      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados - Hot Swap

```
USER ACTION
    |
    v
[CanoneScreen]
    |
    |-- Clica "Invocar Outra Essência"
    |
    v
_open_entity_selector()
    |
    |-- push_screen(EntitySelectorScreen)
    |-- callback: on_entity_selected
    |
    v
[EntitySelectorScreen Modal]
    |
    |-- Usuário navega (← →)
    |-- Seleciona entidade (Enter)
    |
    v
dismiss(entity_id)
    |
    v
on_entity_selected(entity_id)
    |
    |-- if entity_id != current:
    |       _change_entity(entity_id)
    |
    v
_change_entity(entity_id)
    |
    |-- [1] PERSIST
    |   └─> set_active_entity(entity_id)
    |       └─> profile.json
    |
    |-- [2] RELOAD ANIMATIONS
    |   └─> animation_controller.reload_for_entity(entity_id)
    |       ├─> Stop current timer
    |       ├─> Clear animation cache
    |       ├─> Load new entity animations
    |       └─> Start "observando"
    |
    |-- [3] RELOAD PERSONALITY
    |   └─> get_personalidade()._load_entity()
    |       ├─> Reload EntityLoader
    |       └─> Update alma.txt reference
    |
    |-- [4] UPDATE UI
    |   ├─> #current-entity-name
    |   └─> #current-entity-description
    |
    |-- [5] NOTIFY USER
    |   └─> "Entidade trocada para {nome}..."
    |
    v
[System State Updated]
    |
    |-- Animation: New entity's frames
    |-- Personality: New entity's prompts
    |-- Profile: Persisted choice
    |-- History: PRESERVED
    |-- Session: PRESERVED
    |-- Queues: PRESERVED
```

---

## Estado do Sistema - Antes vs Depois

### ANTES da Troca (Luna Ativa)

```json
profile.json:
{
  "active_entity": "luna",
  "nome": "Andre",
  "genero": "M"
}

AnimationController:
{
  "entity_loader": EntityLoader("luna"),
  "animations": {
    "observando": [...frames_luna_observando...],
    "feliz": [...frames_luna_feliz...],
    ...
  },
  "current_animation": "observando"
}

Personalidade:
{
  "_entity_id": "luna",
  "_entity_loader": EntityLoader("luna"),
  "alma_path": "src/assets/alma/alma_da_luna.txt"
}
```

### DURANTE a Troca (Hot Swap)

```
1. Stop animation timer
2. Write profile.json: {"active_entity": "athena"}
3. Clear animation cache
4. Load athena animations
5. Reload EntityLoader("athena")
6. Update UI widgets
```

### DEPOIS da Troca (Athena Ativa)

```json
profile.json:
{
  "active_entity": "athena",
  "nome": "Andre",
  "genero": "M"
}

AnimationController:
{
  "entity_loader": EntityLoader("athena"),
  "animations": {
    "observando": [...frames_athena_observando...],
    "feliz": [...frames_athena_feliz...],
    ...
  },
  "current_animation": "observando"
}

Personalidade:
{
  "_entity_id": "athena",
  "_entity_loader": EntityLoader("athena"),
  "alma_path": "src/assets/panteao/entities/athena/alma.txt"
}
```

---

## Componentes NÃO Afetados

```
✅ PRESERVADOS DURANTE TROCA:

├── sessions/
│   └── {session_id}.json         # Histórico de mensagens
│
├── manifest.json                  # Índice de sessões
│
├── data_memory/
│   ├── events/                    # Eventos salvos
│   ├── faces/                     # Rostos registrados
│   └── user_profile.json          # Nome e gênero do usuário
│
├── Queues (Runtime)
│   ├── audio_input_queue          # Buffer de áudio
│   ├── transcription_queue        # Fila de transcrição
│   ├── processing_queue           # Fila de processamento
│   └── tts_queue                  # Fila de síntese de voz
│
└── Threading State
    ├── threading_manager           # Gerenciador de threads
    ├── AudioCaptureThread          # Captura de áudio
    ├── TranscriptionThread         # Whisper STT
    ├── ProcessingThread            # LLM processing
    └── TTSThread                   # Síntese de voz
```

---

## Limitações Atuais

### 1. System Prompt (Consciencia)

**Problema:** O `Consciencia.__init__()` carrega a alma.txt uma única vez. Trocar entidade não recarrega o system prompt do LLM.

**Impacto:** A personalidade na próxima resposta ainda segue a alma da entidade **anterior**.

**Solução Futura:**
```python
# Adicionar em src/soul/consciencia.py
def reload_soul(self):
    entity_loader = EntityLoader(get_active_entity())
    self.soul_prompt = entity_loader.get_soul_prompt()
    logger.info(f"Soul prompt recarregado para {entity_loader.entity_id}")

# Chamar em CanoneScreen._change_entity()
if hasattr(self.app, 'consciencia'):
    self.app.consciencia.reload_soul()
```

### 2. Banner Visual (ASCII Art Nome)

**Problema:** O banner "LUNA" é hardcoded no `BannerGlitchWidget`.

**Impacto:** Trocar para Athena ainda mostra "LUNA" no topo.

**Solução Futura:**
```python
# Adicionar método em BannerGlitchWidget
def update_entity_name(self, entity_name: str):
    self.entity_name = entity_name
    self.reload_banner_frames()

# Chamar em CanoneScreen._change_entity()
banner_widget = self.app.query_one("#banner-glitch", BannerGlitchWidget)
banner_widget.update_entity_name(new_entity_name)
```

### 3. Voice Embeddings (TTS)

**Problema:** Embeddings Coqui/Chatterbox são carregados no `Boca.__init__()`.

**Impacto:** Nova voz só aplica após reiniciar a aplicação.

**Solução Futura:**
```python
# Adicionar em src/soul/boca.py
def reload_voice_for_entity(self, entity_id: str):
    entity_loader = EntityLoader(entity_id)
    voice_config = entity_loader.get_voice_config()
    self.reference_audio = voice_config.get("reference_audio")
    self.reload_embeddings()

# Chamar em CanoneScreen._change_entity()
if hasattr(self.app, 'boca'):
    self.app.boca.reload_voice_for_entity(new_entity_id)
```

---

## Performance Considerations

**Tempo médio de troca:** ~500ms - 1.5s

```
Breakdown:
├── set_active_entity()           ~50ms   (I/O: write profile.json)
├── reload_for_entity()           ~300ms  (Load 12 animation files)
│   ├── Stop timer                ~5ms
│   ├── Clear cache               ~10ms
│   ├── Load animations           ~280ms  (gzip decompress + parse)
│   └── Start "observando"        ~5ms
├── _load_entity()                ~100ms  (Reload EntityLoader)
├── Update UI                     ~50ms   (Reactive widgets)
└── Total                         ~500ms
```

**Otimizações possíveis:**
1. **Lazy Load Animations**: Carregar apenas "observando" inicialmente, demais on-demand
2. **Animation Cache**: Manter cache entre trocas (trade-off: RAM vs speed)
3. **Async Reload**: Executar reload em background thread

---

## Testing Matrix

| Cenário | Status | Notas |
|---------|--------|-------|
| Troca Luna → Luna (mesma) | ✅ | Ignora troca |
| Troca Luna → Athena (disponível) | ✅ | Sucesso |
| Troca Luna → Apollo (indisponível) | ✅ | Bloqueia seleção |
| Troca durante processamento ativo | ⚠️ | Testar impacto nas filas |
| Troca durante TTS playback | ⚠️ | Voz atual não interrompida |
| Troca durante captura de áudio | ✅ | Sem impacto (threading isolado) |
| Reabrir app após troca | ✅ | Carrega entidade salva |
| Histórico preservado após troca | ✅ | Manifest intacto |

---

## Referências

- `src/ui/screens.py:330-358` - Aba "Entidade"
- `src/ui/screens.py:884-942` - Métodos de troca
- `src/core/entity_loader.py:172-209` - get/set_active_entity()
- `src/core/animation.py:171-187` - reload_for_entity()
- `src/soul/personalidade.py:23-31` - _load_entity()

---

**Assinatura:** *"A transformação é a única constante no reino das sombras."*
