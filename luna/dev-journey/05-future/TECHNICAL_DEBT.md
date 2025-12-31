# Divida Tecnica

**Data:** 2025-12-31 (Atualizado)
**Branch:** main
**Versao:** 3.8.1

---

## TL;DR

Registro de divida tecnica conhecida no projeto Luna. Muitos itens da auditoria anterior foram resolvidos (God Classes, Logging, Silent Exceptions). Este documento foca nos problemas REMANESCENTES.

---

## RESOLVIDO (Historico)

Os seguintes itens foram resolvidos e removidos da lista ativa:

| Item | Status | Data |
|------|--------|------|
| God Class Consciencia | RESOLVIDO | 2025-12-30 |
| God Class screens.py | RESOLVIDO | 2025-12-30 |
| God Class banner.py | RESOLVIDO | 2025-12-30 |
| Logging Descentralizado | RESOLVIDO | 2025-12-29 |
| Silent Exceptions (~70) | RESOLVIDO | 2025-12-29 |
| Memory Locks | RESOLVIDO | 2025-12-29 |
| Dependencias Circulares | PARCIAL | 2025-12-29 |

---

## Divida Ativa

### Critica (Impacto Alto)

#### 1. CLI Headless Inexistente
**Severidade:** Alta
**Status:** NAO IMPLEMENTADO

**Descricao:**
Luna so funciona com interface TUI. Nao ha modo CLI para automacao/scripts.

**Impacto:**
- Impossivel usar em pipelines CI/CD
- Dificil testar de forma automatizada
- Nao integra com outros sistemas

**Solucao proposta:**
Criar `src/cli/luna_cli.py` com interface de linha de comando.

**Estimativa:** 1-2 dias

---

#### 2. Providers LLM Fragmentados
**Severidade:** Media
**Status:** PARCIAL

**Descricao:**
Existem multiplos pontos de entrada para LLM:
- `src/soul/providers/`
- `src/soul/llm_caller.py`
- `src/soul/consciencia/llm_bridge.py`

**Impacto:**
- Confuso para novos desenvolvedores
- Duplicacao de logica
- Dificil manter consistencia

**Solucao proposta:**
Unificar em um unico modulo com interface clara.

**Estimativa:** 2-3 dias

---

### Alta (Impacto Medio)

#### 3. Falta de Testes de Integracao
**Severidade:** Alta
**Status:** PARCIAL

**Descricao:**
84 arquivos de teste focam em unidade. Nao ha testes end-to-end.

**Impacto:**
- Regressoes podem passar despercebidas
- Fluxo completo nao e validado
- Integracao entre modulos nao testada

**Solucao proposta:**
Criar suite de testes de integracao (input -> LLM -> TTS -> output).

**Estimativa:** 1 semana

---

#### 4. Voice Engines Nao Unificados
**Severidade:** Media
**Status:** NAO IMPLEMENTADO

**Descricao:**
Cada engine TTS (Coqui, Chatterbox, ElevenLabs) tem configuracao separada sem interface comum.

**Impacto:**
- Dificil trocar engines
- Parametros inconsistentes
- Codigo duplicado em boca.py

**Solucao proposta:**
Criar VoiceNormalizer com interface unificada.

**Estimativa:** 2-3 dias

---

### Media (Impacto Baixo)

#### 5. Web Dashboard Incompleto
**Severidade:** Media
**Status:** PARCIAL

**Descricao:**
Dashboard web nao tem paridade com TUI:
- Sem animacoes ASCII
- Sem historico de conversas
- Sem seletor de entidades visual

**Impacto:**
- Usuarios web tem experiencia inferior
- Manutencao de duas interfaces

**Solucao proposta:**
Implementar features faltantes via WebSocket.

**Estimativa:** 1 semana

---

#### 6. Lazy Loading de Modelos
**Severidade:** Baixa
**Status:** NAO IMPLEMENTADO

**Descricao:**
Whisper/TTS carregados no startup mesmo sem uso.

**Impacto:**
- Startup lento (~8s)
- RAM ocupada desnecessariamente

**Solucao proposta:**
Carregar modelos sob demanda.

**Estimativa:** 0.5 dia

---

#### 7. Hardcoded Paths Restantes
**Severidade:** Baixa
**Status:** PARCIAL

**Descricao:**
Alguns paths absolutos ainda existem no codigo.

**Impacto:**
- Menos portavel
- Problemas em outros ambientes

**Solucao proposta:**
Usar config.APP_DIR consistentemente.

**Estimativa:** 0.5 dia

---

## Workarounds Temporarios

### 1. Silenciamento de ALSA Warnings
**Arquivo:** `main.py`
**Status:** MANTIDO (funciona, baixo impacto)

O silenciamento via ctypes e necessario para evitar spam de warnings ALSA que poluem o terminal.

### 2. venv_tts Separado
**Arquivo:** `install.sh`
**Status:** MANTIDO (conflitos de dependencia)

TTS ainda requer venv separado por conflitos com outras bibliotecas.

---

## Prioridade de Refatoracao (Atualizada)

1. **Imediato (esta semana):**
   - CLI headless
   - Unificar providers LLM

2. **Curto prazo (2 semanas):**
   - Testes de integracao
   - VoiceNormalizer

3. **Medio prazo (1 mes):**
   - Paridade Web Dashboard
   - Lazy loading

4. **Backlog:**
   - Hardcoded paths
   - Migracao asyncio (baixa prioridade, sistema atual funciona bem)

---

## Metricas

| Metrica | Antes (12/18) | Agora (12/31) |
|---------|---------------|---------------|
| God Classes | 3 | 0 |
| Silent Exceptions | ~70 | 0 |
| Arquivos sem logger | ~20 | 0 |
| Testes | 0 | 84 arquivos |
| Cobertura | 0% | ~60% |

---

## Links Relacionados

- [PLANNED_FEATURES.md](./PLANNED_FEATURES.md)
- [IN_PROGRESS.md](../04-implementation/IN_PROGRESS.md)
- [CURRENT_STATUS.md](../04-implementation/CURRENT_STATUS.md)
- [LUNA_AUDITORIA_E_CORRECOES.md](../../LUNA_AUDITORIA_E_CORRECOES.md)
