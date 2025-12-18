# Histórico: Solução do Problema de Resolução e Terminal

## Contexto Histórico

Este documento descreve como o projeto resolveu o problema de imagens ASCII transbordando do terminal em altas resoluções, culminando na implementação do sistema de `player_zoom` e presets de qualidade.

---

## Problema Original (v1.0)

### Sintomas
- Imagens ASCII em alta resolução transbordavam do terminal
- Ao aumentar `target_width` para melhorar qualidade, a imagem quebrava
- Terminal com fonte padrão comportava ~80-120 colunas
- Usuário tinha duas opções ruins:
  1. Baixa resolução (cabe no terminal, mas sem detalhes)
  2. Alta resolução (muitos detalhes, mas não cabe)

### Exemplo do Problema
```
Config: target_width = 300
Terminal: 120 colunas visíveis
Resultado: Imagem quebrada, ilegível
```

---

## Primeira Solução: Player Zoom (v2.0 - Dezembro 2025)

### Descoberta

Identificado que gnome-terminal aceita parâmetro `--zoom` para ajustar tamanho da fonte:

```bash
gnome-terminal --zoom=0.6  # Reduz fonte para 60%
```

### Implementação

**Arquivo:** `src/main.py` (funções de lançamento do player)

```python
# Ler zoom do config
player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

# gnome-terminal com zoom
cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', ...]

# xterm fallback (não suporta --zoom, usa fonte fixa)
cmd = ['xterm', '-fn', '6x10', '-maximized', ...]
```

**Configuração:** `config.ini`
```ini
[Quality]
player_zoom = 0.6
```

### Resultado

- Terminal com zoom 0.6 comporta ~400x100 caracteres
- Imagens de alta resolução cabem perfeitamente
- Fonte menor = mais informação visível

**CHANGELOG v2.0 (linha 45):**
> **Zoom isolado no terminal do player:** `--zoom=0.6` (gnome-terminal) ou fonte `6x10` (xterm)  
> Não afeta configurações de fonte de outros terminais do sistema  
> Permite até ~400x100 caracteres na tela

---

## Segunda Solução: Presets de Qualidade (v2.0)

### Motivação

Usuários não sabiam qual `target_width` escolher ou qual `player_zoom` usar. Solução: presets prontos.

### Implementação

**ComboBox de Presets** em `src/main.py`:

```python
resolution_presets = {
    'mobile': {'width': 100, 'height': 25, 'aspect': 0.50, 'zoom': 1.0},
    'low': {'width': 120, 'height': 30, 'aspect': 0.50, 'zoom': 0.9},
    'medium': {'width': 180, 'height': 45, 'aspect': 0.48, 'zoom': 0.7},
    'high': {'width': 240, 'height': 60, 'aspect': 0.45, 'zoom': 0.6},
    'veryhigh': {'width': 300, 'height': 75, 'aspect': 0.42, 'zoom': 0.5},
}
```

**Handler:**
```python
def on_quality_preset_changed(self, combo):
    preset = resolution_presets[preset_id]
    self.config.set('Conversor', 'target_width', str(preset['width']))
    self.config.set('Quality', 'player_zoom', str(preset['zoom']))
    self.save_config()
```

### Lógica dos Valores

| Preset | Width | Zoom | Raciocínio |
|--------|-------|------|------------|
| Mobile | 100 | 1.0 | Resolução baixa, fonte normal |
| Low | 120 | 0.9 | Redução leve |
| Medium | 180 | 0.7 | Balanceado (padrão) |
| High | 240 | 0.6 | Alta qualidade |
| Very High | 300 | 0.5 | Máxima qualidade, fonte 50% |

**Fórmula aproximada:** `zoom ≈ 1.0 - (width / 600)`

---

## Problema Redescoberto: Webcam (Dezembro 2025)

### Sintoma
Webcam em alta resolução transbordava do terminal - **mesmo problema de v1.0!**

### Causa
Código de lançamento da webcam (`_launch_calibrator_in_terminal`) não implementava `player_zoom`:

```python
# ANTES - sem zoom
cmd = ['gnome-terminal', '--maximize', '--title=...', '--'] + cmd_base
```

### Solução Aplicada

Aplicar mesma estratégia do player:

```python
# DEPOIS - com zoom
player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)
cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', ...]
```

**Resultado:** Webcam agora respeita preset selecionado.

---

## Arquitetura Final

### Fluxo Completo

1. **Usuário seleciona preset** (ex: High)
2. **on_quality_preset_changed** atualiza:
   - `target_width = 240`
   - `player_zoom = 0.6`
3. **Conversão** usa `target_width=240` para gerar ASCII
4. **Player/Webcam** abre terminal com `--zoom=0.6`
5. **Resultado:** 240 colunas cabem perfeitamente

### Arquivos Modificados

```
src/main.py
├── on_quality_preset_changed()  # Ajusta width + zoom
├── _launch_player_in_terminal() # Player com zoom
└── _launch_calibrator_in_terminal() # Webcam com zoom

config.ini
└── [Quality]
    ├── preset = medium
    └── player_zoom = 0.7
```

---

## Lições Aprendidas

### 1. Isolamento de Fonte
`--zoom` afeta **apenas o terminal lançado**, não o sistema. Perfeito para aplicação específica.

### 2. Fallback para xterm
xterm não suporta `--zoom`, mas aceita `-fa Mono-{size}`. Cálculo:
```python
font_size = int(12 * player_zoom)  # Ex: 0.6 → 7pt
```

### 3. Presets Facilitam UX
Em vez de usuário ajustar 2 parâmetros (width + zoom), seleciona 1 preset que ajusta ambos automaticamente.

### 4. Reutilização de Solução
Webcam tinha mesmo problema do player (v1.0). Reutilizar solução economizou tempo.

---

## Evolução Timeline

| Versão | Feature | Impacto |
|--------|---------|---------|
| v1.0 | ASCII básico | Problema: overflow |
| v2.0 | player_zoom | Solução: player funciona |
| v2.0 | Presets | UX: seleção fácil |
| v2.1 | Webcam zoom | Paridade: webcam = player |

---

## Referências

- `CHANGELOG.md` linha 45: "Zoom isolado no terminal do player"
- `src/main.py` linhas 611-657: Implementação player
- `src/main.py` linhas 717-740: Implementação webcam
- `config.ini` seção `[Quality]`

---

## Como Replicar em Novo Projeto

Se encontrar problema similar:

1. **Identificar:** Terminal overflow em alta resolução
2. **Testar:** `gnome-terminal --zoom=0.5` manualmente
3. **Implementar:** Passar `--zoom={value}` via subprocess
4. **Automatizar:** Criar presets que ajustam width + zoom
5. **Fallback:** Suportar xterm com `-fa Mono-{size}`

**Código template:**
```python
zoom = config.getfloat('Quality', 'player_zoom', fallback=0.7)
cmd = ['gnome-terminal', f'--zoom={zoom}', '--maximize', '--'] + your_cmd
subprocess.Popen(cmd)
```
