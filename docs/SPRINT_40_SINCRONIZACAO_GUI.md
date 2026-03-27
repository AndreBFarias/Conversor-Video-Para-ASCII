# Sprint 40: Sincronizacao GUI Principal com Calibrador

**Prioridade:** MEDIA
**Resolve:** BUG-18
**Dependencia:** Sprint 35, Sprint 41

## Objetivo

Garantir que a GUI principal e o calibrador leem/escrevem o config.ini de forma coerente, especialmente a confusao entre `gpu_render_mode` e `render_mode`.

## Arquivo a Modificar

- `src/app/actions/options_actions.py`

## Tarefas

### 40.1 - Verificar/separar gpu_render_mode e render_mode

**Contexto:** Existem DUAS configuracoes com nomes similares:
- `gpu_render_mode` (fast/high_fidelity) - modo de matching GPU
- `render_mode` (user/background/both) - modo de chroma key

**Arquivo:** `src/app/actions/options_actions.py`

**Linha 377 (leitura):**
```python
render_mode = self.config.get('Conversor', 'gpu_render_mode', fallback='fast')
```
Verificar: este combo eh de "GPU Render Mode" (fast/high_fidelity)? Se sim, o codigo esta correto. Se o combo tiver opcoes user/background/both, entao deveria ler `render_mode` em vez de `gpu_render_mode`.

**Linha 581 (escrita):**
```python
self.config.set('Conversor', 'gpu_render_mode', render_mode)
```
Mesmo raciocinio: verificar que o combo corresponde a gpu_render_mode.

**Acao:** Inspecionar o Glade (`src/gui/main.glade`) para encontrar o widget `pref_render_mode_combo` e verificar quais opcoes ele oferece. Se oferece fast/high_fidelity, manter como esta. Se oferece user/background/both, mudar para ler/escrever `render_mode`.

### 40.2 - Reload completo apos calibrador fechar

**Arquivo:** `src/app/actions/calibration_actions.py`
**Funcao:** `_launch_gtk_calibrator` (linha ~36)

O reload_config ja existe (linha 43). Verificar se todos os widgets da GUI principal sao atualizados apos o reload. Se existir `_refresh_preview`, verificar se tambem atualiza combos de qualidade, modo, etc.

## Verificacao

1. Abrir GUI principal
2. Abrir Opcoes - verificar qual combo eh "Modo de Render" e quais opcoes tem
3. Mudar a opcao, salvar
4. Abrir calibrador - verificar que a opcao salva esta refletida
5. No calibrador, mudar render mode, salvar
6. Voltar para GUI principal, abrir Opcoes - verificar que o valor mudou
