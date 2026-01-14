# Unificação de Configurações - Análise e Plano

## Problema Identificado

**Sintoma:** Alterar configurações em uma interface (Calibrador, Opções, etc.) não reflete nas outras.

**Causa Raiz:** `config.ini` é lido UMA VEZ no `__init__` e mantido em memória (`self.config`). Mudanças em uma interface não recarregam o config nas outras.

---

## Mapeamento Atual

### Fontes de Configuração

#### 1. config.ini (Arquivo - Fonte de Verdade)
**Localização:** `/home/andrefarias/Desenvolvimento/Conversor-Video-Para-ASCII/config.ini`

**Seções:**
```ini
[Conversor]
- luminance_ramp
- target_width
- target_height
- sobel_threshold
- char_aspect_ratio
- sharpen_enabled
- sharpen_amount

[ChromaKey]
- h_min, h_max
- s_min, s_max
- v_min, v_max
- erode, dilate

[Player]
- loop
- show_fps
- speed

[PixelArt]
- pixel_size
- color_palette_size
- use_fixed_palette
- fixed_palette_name

[Mode]
- conversion_mode

[Output]
- format
```

#### 2. App Principal (src/app/app.py)
**Leitura:** Linha 147 - `self.config.read(self.config_path)`
**Escrita:** Linha 228 - `self.config.write(f)` via `save_config()`

**Problema:** Config é carregado UMA VEZ no `__init__`. Nunca recarrega.

#### 3. Calibrador GTK (src/core/gtk_calibrator.py)
**Leitura:** Linha 151 - `self.config.read(self.config_path)`
**Escrita:** Linha 1101 - `self.config.write(f)` via `on_save_config_clicked()`

**Problema:** Calibrador salva no arquivo, mas app principal não recarrega.

#### 4. Interface de Opções (src/app/actions/options_actions.py)
**Leitura:** Linha 236-272 - `on_options_button_clicked()` lê `self.config` (memória)
**Escrita:** Várias linhas - chama `self.save_config()`

**Problema:** Lê da cópia em memória, não do arquivo atualizado.

---

## Fluxo Atual (Bugado)

```
[Usuário abre app]
    ↓
[App carrega config.ini → self.config (memória)]
    ↓
[Usuário clica "Calibrar Chroma Key"]
    ↓
[Calibrador carrega config.ini → calibrador.config (cópia separada)]
    ↓
[Usuário ajusta chroma key]
    ↓
[Calibrador salva → config.ini ATUALIZADO]
    ↓
[Calibrador fecha]
    ↓
[Usuário abre Configurações]
    ↓
[Opções lê self.config (DESATUALIZADO)]  ← PROBLEMA
    ↓
[Usuário vê valores antigos]
```

---

## Solução: Recarregar Config em Pontos-Chave

### Estratégia

1. **Criar função `reload_config()`** - Recarrega config.ini do disco
2. **Chamar reload antes de abrir qualquer interface** - Garante valores atualizados
3. **Chamar reload após fechar calibrador** - Sincroniza mudanças
4. **Opcional: Watch file changes** - Recarrega automaticamente se arquivo mudar

### Implementação

#### Passo 1: Adicionar `reload_config()` em app.py

```python
def reload_config(self):
    """
    Recarrega configurações do arquivo config.ini
    Deve ser chamado antes de abrir interfaces que dependem de config
    """
    try:
        self.config.read(self.config_path, encoding='utf-8')
        self.logger.info("Configuracoes recarregadas do disco")
    except Exception as e:
        self.logger.error(f"Erro ao recarregar config: {e}")
```

#### Passo 2: Chamar reload em pontos-chave

**Antes de abrir Opções:**
```python
def on_options_button_clicked(self, widget):
    self.reload_config()  # ← ADICIONAR
    # ... resto do código
```

**Depois de fechar Calibrador:**
```python
def on_calibrate_button_clicked(self, widget):
    # ... abrir calibrador ...
    subprocess.run([...])  # Bloqueia até fechar
    self.reload_config()  # ← ADICIONAR APÓS O PROCESSO TERMINAR
```

**Antes de converter:**
```python
def run_conversion(self, file_paths: list):
    self.reload_config()  # ← ADICIONAR para pegar configs mais recentes
    # ... resto do código
```

#### Passo 3: Garantir calibrador salva corretamente

Já implementado em `gtk_calibrator.py:1101`:
```python
with open(self.config_path, 'w', encoding='utf-8') as f:
    self.config.write(f)
```

---

## Fluxo Corrigido

```
[Usuário abre app]
    ↓
[App carrega config.ini → self.config]
    ↓
[Usuário clica "Calibrar Chroma Key"]
    ↓
[Calibrador carrega config.ini → calibrador.config]
    ↓
[Usuário ajusta chroma key]
    ↓
[Calibrador salva → config.ini ATUALIZADO]
    ↓
[Calibrador fecha]
    ↓
[App chama reload_config()]  ← NOVO
    ↓
[self.config ATUALIZADO]
    ↓
[Usuário abre Configurações]
    ↓
[Opções chama reload_config()]  ← NOVO
    ↓
[Opções lê self.config (ATUALIZADO)]  ✅
    ↓
[Usuário vê valores corretos]
```

---

## Casos de Uso a Testar

### Caso 1: Calibrador → Opções
1. Abrir calibrador
2. Mudar `sobel_threshold` para 50
3. Salvar e fechar calibrador
4. Abrir janela de opções
5. **Esperado:** `sobel_threshold` mostra 50

### Caso 2: Opções → Calibrador
1. Abrir opções
2. Mudar `target_width` para 100
3. Salvar opções
4. Abrir calibrador
5. **Esperado:** Largura mostra 100

### Caso 3: Calibrador → Conversão
1. Abrir calibrador
2. Ajustar chroma key (H: 60-80, S: 100-255, V: 100-255)
3. Salvar e fechar
4. Converter vídeo
5. **Esperado:** Vídeo usa novos valores de chroma key

### Caso 4: Opções → Conversão
1. Abrir opções
2. Mudar formato para "MP4"
3. Salvar
4. Converter arquivo
5. **Esperado:** Gera arquivo .mp4

---

## Arquivos a Modificar

### 1. src/app/app.py
**Adicionar função:**
```python
def reload_config(self):
    try:
        self.config.read(self.config_path, encoding='utf-8')
        self.logger.info("Configuracoes recarregadas")
    except Exception as e:
        self.logger.error(f"Erro ao recarregar: {e}")
```

### 2. src/app/actions/options_actions.py
**Modificar função existente:**
```python
def on_options_button_clicked(self, widget):
    self.reload_config()  # ← ADICIONAR NO INÍCIO
    try:
        loop_val_str = self.config.get('Player', 'loop', fallback='nao').lower()
        # ... resto
```

### 3. src/app/actions/calibrator_actions.py (se existir) ou app.py
**Modificar chamada do calibrador:**
```python
def on_calibrate_button_clicked(self, widget):
    # ... código existente ...
    subprocess.run([...], check=True)  # Espera fechar
    self.reload_config()  # ← ADICIONAR APÓS
```

### 4. src/app/actions/conversion_actions.py
**Modificar função:**
```python
def run_conversion(self, file_paths: list):
    self.reload_config()  # ← ADICIONAR NO INÍCIO
    python_executable = self._get_python_executable()
    # ... resto
```

---

## Riscos e Mitigações

### Risco 1: Recarregar durante edição
**Cenário:** Usuário está editando opções enquanto config.ini é recarregado
**Mitigação:** Recarregar APENAS ao abrir interfaces, não durante edição

### Risco 2: Conflitos de escrita
**Cenário:** Calibrador e Opções tentam salvar simultaneamente
**Mitigação:** Processos são sequenciais (GTK é single-threaded)

### Risco 3: Config corrompido
**Cenário:** Erro ao escrever deixa config.ini inválido
**Mitigação:** Backup automático antes de salvar (futuro)

---

## Alternativas Consideradas

### Opção A: Singleton Config Manager ❌
**Pro:** Única instância em memória
**Contra:** Complexo, requer refatoração grande

### Opção B: File Watcher ❌
**Pro:** Recarrega automaticamente
**Contra:** Overhead, dependência extra (watchdog)

### Opção C: Reload em Pontos-Chave ✅ (ESCOLHIDA)
**Pro:** Simples, mínimo de mudanças, confiável
**Contra:** Precisa lembrar de chamar reload

---

## Implementação Proposta

1. Adicionar `reload_config()` em app.py
2. Chamar reload em 3 lugares:
   - Antes de abrir opções
   - Depois de fechar calibrador
   - Antes de iniciar conversão
3. Testar todos os casos de uso
4. Commit: `fix: Sincronizar configurações entre interfaces`

---

**Próximo passo:** Implementar mudanças
