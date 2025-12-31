# Fluxo de Onboarding com Entity Selector

**Data**: 2025-12-25
**Versao**: v3.4.1

---

## Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                    INICIO DO ONBOARDING                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
              ┌───────────────────────────────┐
              │ should_show_entity_selector() │
              │                               │
              │ Verifica quantas entidades    │
              │ estao disponiveis no registry │
              └───────────────────────────────┘
                              │
                              v
                     ┌────────────────┐
                     │ len() > 1 ?    │
                     └────────────────┘
                       │             │
                 [SIM] │             │ [NAO]
                       v             v
         ┌──────────────────┐   ┌──────────────────┐
         │ MOSTRAR SELETOR  │   │  USAR LUNA       │
         │ EntitySelector   │   │  (default)       │
         │ Screen           │   │                  │
         └──────────────────┘   └──────────────────┘
                  │                      │
                  │ Usuario seleciona    │
                  │ com ← → Enter        │
                  v                      │
         ┌──────────────────┐            │
         │ selected_entity  │            │
         │ = user_choice    │            │
         └──────────────────┘            │
                  │                      │
                  v                      v
         ┌──────────────────────────────────┐
         │  set_active_entity(entity_id)    │
         │  Persiste escolha no profile     │
         └──────────────────────────────────┘
                              │
                              v
         ┌──────────────────────────────────┐
         │   entity_loader = EntityLoader   │
         │   (selected_entity)              │
         └──────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                   STATIC OVERLAY (3s)                        │
│              TV Static em toda a interface                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                      ATO I - PERGUNTA NOME                   │
│                                                              │
│  if selected_entity != "luna":                               │
│    ├─ "Bem-vindo ao terminal de {entity_name}..."           │
│  else:                                                       │
│    ├─ Frase poetica do CSV (linha 1, variacao aleatoria)    │
│                                                              │
│  Revela: #main_input                                         │
│  Aguarda: input de texto (timeout 90s)                       │
│  Processa: extrai nome, analisa genero                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                   ATO I - APRESENTACAO                       │
│                                                              │
│  Revela: Banner da entidade (TV static → glitch)            │
│                                                              │
│  if selected_entity != "luna":                               │
│    ├─ "{user_name}, um prazer. Eu sou {entity_name}."       │
│  else:                                                       │
│    ├─ Frase poetica do CSV (linha 3, variacao aleatoria)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                 ATO I - BOTAO VOZ (OPCIONAL)                 │
│                                                              │
│  Revela: #toggle_voice_call                                  │
│  Frase: CSV linha 4 (sempre generica)                       │
│  Aguarda: click ou timeout 12s                              │
│                                                              │
│  if clicked:                                                 │
│    ├─ Resume listening                                       │
│    ├─ Aguarda input de voz (timeout 20s)                    │
│    ├─ Pausa listening                                        │
│    └─ Salva: preferencias.permite_voz = True                │
│  else:                                                       │
│    └─ Salva: preferencias.permite_voz = False               │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│              ATO I - BOTAO ANEXAR (SEMPRE)                   │
│                                                              │
│  Revela: #attach_file                                        │
│  Frase: CSV linha 5 (sempre generica)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    ATO II - MENU REVELATION                  │
│                                                              │
│  Revela menu lateral                                         │
│  Frase: CSV linha 6 (monologo da entidade)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│              ATO II - BOTAO VER (OPCIONAL)                   │
│                                                              │
│  Revela: #olhar                                              │
│  Frase: CSV linha 7                                          │
│  Aguarda: click ou timeout 12s                              │
│                                                              │
│  if clicked:                                                 │
│    ├─ Captura frame da camera                               │
│    ├─ Registra rosto com nome do usuario                    │
│    ├─ Salva foto em data_memory/events/                     │
│    └─ Salva: preferencias.permite_camera = True             │
│  else:                                                       │
│    └─ Salva: preferencias.permite_camera = False            │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                ATO II - REVELACAO DE BOTOES                  │
│                                                              │
│  Revela sequencialmente com pausas de 0.5s:                 │
│    1. #nova_conversa (Confissao) - CSV linha 8              │
│    2. #ver_historico (Relicario) - CSV linha 9              │
│    3. #editar_alma (Custodia) - CSV linha 10                │
│    4. #canone + #quit (Canone/Requiem) - CSV linha 11       │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    ENCERRAMENTO RITUAL                       │
│                                                              │
│  Frase final: CSV linha 12                                   │
│  Salva no profile.json:                                      │
│    ├─ onboarding_completo = True                            │
│    ├─ completed_at = timestamp                              │
│    └─ active_entity = selected_entity ← NOVO                │
│                                                              │
│  Revela todos os elementos                                   │
│  Resume listening                                            │
│  Chama: app.action_nova_conversa()                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
                     ┌────────────────┐
                     │  FIM ONBOARD   │
                     └────────────────┘
```

---

## Casos de Uso

### Caso 1: Registry com Apenas Luna

```json
{
  "entities": {
    "luna": {
      "available": true
    }
  }
}
```

**Fluxo**:
1. `should_show_entity_selector()` retorna `False`
2. Seletor NAO aparece
3. `selected_entity = "luna"` (hardcoded)
4. Frases do CSV sao usadas (poeticas)
5. Banner Luna e exibido
6. Onboarding identico ao tradicional

---

### Caso 2: Registry com Luna + Juno

```json
{
  "entities": {
    "luna": {
      "available": true
    },
    "juno": {
      "available": true
    }
  }
}
```

**Fluxo**:
1. `should_show_entity_selector()` retorna `True`
2. **EntitySelectorScreen aparece ANTES do static**
3. Usuario navega com `←` `→` e seleciona com `Enter`
4. Se escolher Juno:
   - `selected_entity = "juno"`
   - `set_active_entity("juno")` persiste no profile
   - EntityLoader("juno") carrega config/alma/animations
   - Saudacao: "Bem-vindo ao terminal de Juno..."
   - Apresentacao: "Andre, um prazer. Eu sou Juno."
   - Banner Juno e exibido
   - Resto do onboarding usa frases genericas do CSV

---

## Frases Adaptativas

| Linha CSV | Luna (poetica) | Outras Entidades (generica) |
|-----------|----------------|------------------------------|
| Linha 1 | "Olá explorador de mistérios..." (10 variações) | "Bem-vindo ao terminal de {entity_name}. Como devo te chamar, mortal?" |
| Linha 3 | "É um prazer $N..." (10 variações) | "{user_name}, um prazer. Eu sou {entity_name}." |
| Linhas 4-12 | Frases do CSV (sempre) | Frases do CSV (sempre) |

---

## Estrutura do profile.json Apos Onboarding

```json
{
  "nome": "Andre",
  "nome_completo_input": "Andre Farias",
  "nome_analise": {
    "genero_provavel": "masculino",
    "confianca_genero": 0.95,
    "possiveis_origens": ["grego", "portugues"],
    "diminutivos_comuns": ["Dre"],
    "tratamento_sugerido": "senhor"
  },
  "preferencias": {
    "permite_voz": true,
    "permite_camera": true
  },
  "onboarding_completo": true,
  "completed_at": "2025-12-25T21:30:00",
  "active_entity": "juno"  ← NOVO CAMPO
}
```

---

## Proximas Features

### 1. CSVs Customizados por Entidade

Estrutura sugerida:
```
src/assets/panteao/entities/juno/onboarding.csv
src/assets/panteao/entities/eris/onboarding.csv
```

Modificacao necessaria em `OnboardingDialogues`:
```python
def __init__(self, entity_id: str = "luna"):
    self.entity_id = entity_id
    self.csv_path = self._get_csv_path()
    self._load_csv()

def _get_csv_path(self) -> Path:
    entity_csv = ENTITIES_DIR / self.entity_id / "onboarding.csv"
    if entity_csv.exists():
        return entity_csv
    return CSV_PATH  # Fallback para o CSV default
```

### 2. Parametros de TTS por Entidade

Usar `entity_loader.get_voice_config()`:
```python
voice_config = self.entity_loader.get_voice_config()
stability = voice_config.get("elevenlabs", {}).get("stability", 0.3)
style = voice_config.get("elevenlabs", {}).get("style", 0.65)
await self._falar_onboarding(frase, stability=stability, style=style)
```

### 3. Cores Tematicas por Entidade

Carregar `entity_loader.get_color_theme()` e aplicar CSS dinamico durante onboarding.

---

**Citacao**: "A interface e o espelho da alma digital." - Alan Kay
