# Changelog - Correcoes Multi-Entidade

**Data**: 2025-12-26
**Versao**: v4.4.0 (Pantheon Edition)

---

## Resumo

Correcao de bugs criticos no sistema multi-entidade e migracao completa para estrutura Pantheon.

---

## Bugs Corrigidos

### 1. Falta de Metodo `reload_for_entity()` em Personalidade

**Arquivo**: `src/soul/personalidade.py`
**Problema**: A classe `DicionarioPersonalidade` nao tinha metodo para recarregar quando a entidade era trocada.
**Correcao**: Adicionado metodo `reload_for_entity(entity_id)` que reinicializa o EntityLoader e limpa frases usadas.

### 2. Chamada Incorreta de Reload de Personalidade

**Arquivo**: `src/ui/screens.py`
**Problema**: O codigo chamava `personalidade._load_entity()` (metodo privado) que nao forcava reload.
**Correcao**: Alterado para chamar `personalidade.reload_for_entity(new_entity_id)`.

### 3. Emotion Label Hardcoded com "Luna"

**Arquivo**: `src/core/animation.py`
**Problema**: O texto `[Luna esta {emotion}]` era fixo independente da entidade.
**Correcao**: Agora usa dinamicamente o nome da entidade ativa: `[{entity_name} esta {emotion}]`.

### 4. CSS Hardcoded no EntitySelectorScreen

**Arquivo**: `src/ui/entity_selector.py`
**Problema**: Cores de background, border e texto eram fixas no CSS inline.
**Correcao**: Adicionado metodo `_apply_dynamic_theme()` que aplica cores da entidade ativa.

### 5. Symlinks de Animacoes Quebrados

**Pasta**: `src/assets/panteao/entities/luna/animations/`
**Problema**: Arquivos eram symlinks apontando para pasta deletada.
**Correcao**: Convertidos symlinks em arquivos reais.

### 6. Falta de Overrides CSS no ThemeManager

**Arquivo**: `src/ui/theme_manager.py`
**Problema**: Muitas regras de `:hover` e `:active` nao estavam sendo sobrescritas.
**Correcao**: Adicionados overrides para:
- `Button:hover`, `Button:focus`
- `GlitchButton:hover`
- `#canone-tabs Tab:hover`, `Tab.-active`
- `#history-list > ListItem:hover`, `:focus`, `.-selected`
- `Select`, `Input`, `Switch`
- `VerticalScroll` scrollbars

---

## Migracoes

### Estrutura de Pastas

| Antes | Depois |
|-------|--------|
| `src/assets/animations/` | `src/assets/panteao/entities/luna/animations/` |
| `src/assets/alma/alma_da_luna.txt` | `src/assets/panteao/entities/luna/alma.txt` |

### Atualizacoes de Path

Arquivos atualizados:
- `config.py`: `ASCII_ART_DIR`, `LEGACY_SOUL_FILE`
- `src/core/animation.py`: `fallback_dir`, `legacy_dir`
- `src/core/entity_loader.py`: `luna_anim_dir`, fallbacks
- `src/ui/entity_selector.py`: fallback de banner
- `src/soul/personalidade.py`: `FALLBACK_ALMA_PATH`
- `src/tools/verify_install.py`: paths de verificacao

---

## Arquivos Modificados

```
config.py
main.py
src/core/animation.py
src/core/entity_loader.py
src/soul/personalidade.py
src/ui/entity_selector.py
src/ui/screens.py
src/ui/theme_manager.py
src/tools/verify_install.py
```

## Arquivos/Pastas Removidos

```
src/assets/animations/        (movido para panteao)
src/assets/alma/              (movido para panteao)
```

---

## Testes Recomendados

1. Iniciar app com entidade Luna
2. Trocar para Eris via Canone
3. Verificar cores de background, hover, active
4. Verificar animacoes e emotion label
5. Verificar frases e personalidade
6. Trocar de volta para Luna
7. Verificar se tudo funciona

---

---

## Sessao 2 - Correcoes Adicionais

### 7. Selecao de Divindade no install.sh

**Arquivo**: `install.sh`
**Problema**: Usuario nao podia escolher a divindade inicial durante instalacao.
**Correcao**: Adicionada FASE 9 com menu interativo para escolher entre Luna, Juno ou Eris.

### 8. Backgrounds Hardcoded no CSS

**Arquivo**: `src/ui/theme_manager.py`
**Problema**: Varios elementos tinham background #282a36 fixo (status-label, emotion-label, chat-list, etc.)
**Correcao**: Adicionados CSS overrides dinamicos para:
- `#status-label`, `#emotion-label`
- `VerticalScroll#chat-list`
- `#history-container`, `#history-list`
- `#audio-visualizer`, `#status-area`
- `VoiceTrainerScreen`, `HistoryScreen`
- `#main_input`, `#main_input:focus`

### 9. Restart Automatico ao Trocar Entidade

**Arquivo**: `src/ui/screens.py`
**Problema**: Ao trocar de entidade, era necessario reiniciar manualmente o app.
**Correcao**:
- Adicionado metodo `_clear_theme_caches()` para limpar __pycache__
- Adicionado metodo `_restart_application()` com `os.execv()` para reinicio automatico
- Troca de entidade agora exibe notificacao e reinicia em 1.5s

### 10. Bug "Eris esta Eris sarcastica"

**Arquivo**: `src/core/animation.py`
**Problema**: O status exibia o nome da entidade duplicado (ex: "Eris esta Eris sarcastica").
**Correcao**: Modificada normalizacao para remover qualquer prefixo de entidade dinamicamente:
- Antes: `sentiment.replace("Luna_", "")`
- Depois: Verifica todos os prefixos possiveis (Luna_, Eris_, Juno_, Mars_, Lars_, Somn_)

### 11. Onboarding Lendo CSV por Entidade

**Arquivo**: `src/soul/onboarding.py`
**Problema**: O codigo lia coluna "Luna" que nao existe no CSV. Estrutura real tem colunas "Entidade" e "Conteudo".
**Correcao**:
- `OnboardingDialogues` agora aceita `entity_id` como parametro
- Metodo `_load_csv()` filtra por coluna "Entidade" (TODOS ou entidade especifica)
- Adicionado metodo `reload_for_entity()` para recarregar dialogos
- `start_sequence()` agora recarrega dialogos apos selecionar entidade

---

## Arquivos Modificados (Sessao 2)

```
install.sh                     (FASE 9 - selecao de divindade)
src/ui/theme_manager.py        (overrides CSS adicionais)
src/ui/screens.py              (restart automatico)
src/core/animation.py          (normalizacao de prefixos)
src/soul/onboarding.py         (leitura CSV por entidade)
```

---

## Proximos Passos

1. Adicionar animacoes especificas para Eris e Juno
2. Testar fluxo completo de instalacao e onboarding
3. Validar funcionamento em todos os modos
