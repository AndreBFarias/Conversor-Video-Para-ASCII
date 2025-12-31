# LUNA - ARQUITETURA MULTI-LLM E UX DO TERMINAL

> **Localizacao:** `docs/ARCHITECTURE_LLM.md`
> **Prioridade:** ALTA - Proxima etapa do projeto

---

## 1. VISAO GERAL

Luna deve funcionar **100% local** por padrao, com opcoes pagas para quem quiser.
O usuario nunca deve perceber que esta falando com uma IA - a experiencia deve ser fluida e natural.

### Principios

1. **Local First** - Tudo funciona offline por padrao
2. **Pay-to-Upgrade** - APIs pagas sao opcionais, nunca obrigatorias
3. **Swap Invisivel** - Trocar de modelo nao pode quebrar a experiencia
4. **Performance** - Modelos leves e rapidos, mesmo que menos "inteligentes"

---

## 2. MAPA DE FUNCIONALIDADES E MODELOS

```
┌─────────────────────────────────────────────────────────────────┐
│                         LUNA                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FUNCAO          LOCAL (Gratis)         PAGO (Opcional)         │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  VOZ (TTS)       Chatterbox/Piper       ElevenLabs API          │
│                  ↓                       ↓                       │
│                  Funciona offline        Voz premium             │
│                  VRAM: ~2GB              Custo: $0.30/1K chars   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  OUVIDO (STT)    Faster-Whisper         Whisper API (OpenAI)    │
│                  ↓                       ↓                       │
│                  whisper-small/medium    Mais preciso            │
│                  VRAM: ~1-2GB            Custo: $0.006/min       │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  VISAO           MiniCPM-V / LLaVA      Gemini Flash Vision     │
│                  ↓                       ↓                       │
│                  Modelo local            Rapido e preciso        │
│                  VRAM: ~4-6GB            Custo: $0.075/1K imgs   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  CONVERSA        Dolphin/Hermes 7B      Gemini Pro / GPT-4o     │
│  (Persona)       ↓                       ↓                       │
│                  Via Ollama              Mais inteligente        │
│                  VRAM: ~4-6GB            Custo: $0.50/1M tokens  │
│                  Sem censura                                     │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  CODIGO          DeepSeek Coder 6.7B    DeepSeek API / Gemini   │
│                  ↓                       ↓                       │
│                  Via Ollama              Melhor qualidade        │
│                  VRAM: ~4-6GB            Custo: $0.14/1M tokens  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. MODELOS LOCAIS RECOMENDADOS

### 3.1 VOZ (TTS) - Ja Implementado

| Modelo | VRAM | Qualidade | Velocidade | Status |
|--------|------|-----------|------------|--------|
| **Chatterbox** | ~2GB | Excelente | Media | Atual |
| **Piper** | CPU | Boa | Rapida | Fallback |
| ElevenLabs | - | Premium | Rapida | Pago |

**Configuracao atual funciona.** Manter como esta.

### 3.2 OUVIDO (STT) - Ja Implementado

| Modelo | VRAM | Precisao | Velocidade | Status |
|--------|------|----------|------------|--------|
| **Faster-Whisper small** | ~1GB | Boa | Rapida | Recomendado |
| Faster-Whisper medium | ~2GB | Muito Boa | Media | Opcional |
| Whisper API | - | Excelente | Rapida | Pago |

**Configuracao atual funciona.** Manter como esta.

### 3.3 VISAO - Precisa Modelo Local

| Modelo | VRAM | Qualidade | Velocidade | Notas |
|--------|------|-----------|------------|-------|
| **MiniCPM-V 2.6** | ~4GB | Muito Boa | Rapida | **RECOMENDADO** |
| LLaVA 1.6 7B | ~6GB | Boa | Media | Alternativa |
| Moondream 2 | ~2GB | Basica | Muito Rapida | Leve mas limitado |
| Gemini Flash | - | Excelente | Rapida | Pago (atual) |

**Recomendacao:** MiniCPM-V 2.6 via Ollama
```bash
ollama pull minicpm-v
```

### 3.4 CONVERSA (Persona Luna) - Precisa Modelo Local

| Modelo | VRAM | Qualidade | Censura | Velocidade |
|--------|------|-----------|---------|------------|
| **Dolphin Mistral 7B** | ~4GB | Boa | Nenhuma | Rapida |
| Nous Hermes 2 7B | ~4GB | Muito Boa | Minima | Rapida |
| Llama 3 8B | ~5GB | Muito Boa | Media | Media |
| Gemini Flash | - | Excelente | Media | Rapida |

**Recomendacao:** Dolphin Mistral 7B Q4 via Ollama
```bash
ollama pull dolphin-mistral
```

### 3.5 CODIGO - Precisa Modelo Local

| Modelo | VRAM | Python/SQL | Data Science | Velocidade |
|--------|------|------------|--------------|------------|
| **Qwen2.5 Coder 7B** | ~4GB | Excelente | Muito Boa | Rapida |
| DeepSeek Coder 6.7B | ~4GB | Muito Boa | Boa | Rapida |
| CodeLlama 7B | ~4GB | Boa | Media | Rapida |
| Gemini/DeepSeek API | - | Excelente | Excelente | Rapida |

**Recomendacao:** Qwen2.5 Coder 7B via Ollama
```bash
ollama pull qwen2.5-coder:7b
```

---

## 4. ARQUITETURA DE CONFIGURACAO

### 4.1 config.py - Estrutura

```python
# ═══════════════════════════════════════════════════════════════
# CONFIGURACAO DE MODELOS - LOCAL vs PAGO
# ═══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────
# VOZ (TTS)
# ─────────────────────────────────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "local")  # "local" ou "elevenlabs"

TTS_LOCAL = {
    "engine": "chatterbox",  # "chatterbox" ou "piper"
    "model": "default",
    "voice_sample": "assets/voice/luna_sample.wav",
}

TTS_ELEVENLABS = {
    "api_key": os.getenv("ELEVENLABS_API_KEY", ""),
    "voice_id": os.getenv("ELEVENLABS_VOICE_ID", ""),
}

# ─────────────────────────────────────────────────────────────────
# OUVIDO (STT)
# ─────────────────────────────────────────────────────────────────
STT_PROVIDER = os.getenv("STT_PROVIDER", "local")  # "local" ou "openai"

STT_LOCAL = {
    "engine": "faster-whisper",
    "model": "small",  # "tiny", "small", "medium"
    "language": "pt",
}

STT_OPENAI = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "whisper-1",
}

# ─────────────────────────────────────────────────────────────────
# VISAO
# ─────────────────────────────────────────────────────────────────
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "local")  # "local" ou "gemini"

VISION_LOCAL = {
    "engine": "ollama",
    "model": "minicpm-v",
}

VISION_GEMINI = {
    "api_key": os.getenv("GEMINI_API_KEY", ""),
    "model": "gemini-1.5-flash",
}

# ─────────────────────────────────────────────────────────────────
# CONVERSA (Persona)
# ─────────────────────────────────────────────────────────────────
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "local")  # "local" ou "gemini"

CHAT_LOCAL = {
    "engine": "ollama",
    "model": "dolphin-mistral",
    "temperature": 0.85,
    "max_tokens": 1024,
}

CHAT_GEMINI = {
    "api_key": os.getenv("GEMINI_API_KEY", ""),
    "model": "gemini-1.5-flash",
    "temperature": 0.9,
}

# ─────────────────────────────────────────────────────────────────
# CODIGO
# ─────────────────────────────────────────────────────────────────
CODE_PROVIDER = os.getenv("CODE_PROVIDER", "local")  # "local" ou "deepseek"

CODE_LOCAL = {
    "engine": "ollama",
    "model": "qwen2.5-coder:7b",
    "temperature": 0.3,
    "max_tokens": 4096,
}

CODE_API = {
    "provider": "deepseek",  # ou "gemini"
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "model": "deepseek-coder",
}
```

### 4.2 .env.example

```bash
# ═══════════════════════════════════════════════════════════════
# LUNA - CONFIGURACAO DE PROVIDERS
# ═══════════════════════════════════════════════════════════════
# Opcoes: "local" (gratis) ou nome do servico pago

# VOZ
TTS_PROVIDER=local
# TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# OUVIDO
STT_PROVIDER=local
# STT_PROVIDER=openai
OPENAI_API_KEY=

# VISAO
VISION_PROVIDER=local
# VISION_PROVIDER=gemini
GEMINI_API_KEY=

# CONVERSA
CHAT_PROVIDER=local
# CHAT_PROVIDER=gemini

# CODIGO
CODE_PROVIDER=local
# CODE_PROVIDER=deepseek
DEEPSEEK_API_KEY=
```

---

## 5. ROUTER INTELIGENTE

### 5.1 Detectar Intent do Usuario

```python
# src/core/router.py

from enum import Enum
from typing import Tuple
import re


class Intent(Enum):
    CHAT = "chat"           # Conversa normal com Luna
    CODE = "code"           # Pedido de programacao
    VISION = "vision"       # Analise de imagem
    SYSTEM = "system"       # Comando do sistema


CODE_PATTERNS = [
    r"\b(codigo|code|script|funcao|function|classe|class)\b",
    r"\b(python|sql|javascript|typescript|r|bash)\b",
    r"\b(cria|crie|faz|faca|implementa|implementar)\b.*\b(um|uma)\b",
    r"\b(debug|erro|error|bug|fix|corrige|corrigir)\b",
    r"\b(dataframe|pandas|numpy|query|select|insert)\b",
    r"\b(pipeline|etl|airflow|dbt|bigquery|gcp)\b",
    r"\b(power\s*bi|pbi|dashboard|relatorio)\b",
    r"\b(api|endpoint|request|response)\b",
]

VISION_PATTERNS = [
    r"\b(ve|veja|olha|olhe|analisa|analise)\b.*\b(isso|imagem|foto|tela)\b",
    r"\b(o\s+que\s+(voce\s+)?ve|que\s+ve)\b",
    r"\b(descreve|descreva|identifica|identifique)\b",
]

SYSTEM_PATTERNS = [
    r"^/(nova|historico|alma|sair|config|ajuda|help)",
]


def detect_intent(user_input: str, has_image: bool = False) -> Intent:
    """Detecta a intencao do usuario para rotear pro modelo correto."""

    input_lower = user_input.lower().strip()

    # Comandos do sistema tem prioridade
    for pattern in SYSTEM_PATTERNS:
        if re.search(pattern, input_lower):
            return Intent.SYSTEM

    # Se tem imagem anexada, provavelmente quer analise
    if has_image:
        return Intent.VISION

    # Verifica padroes de visao
    for pattern in VISION_PATTERNS:
        if re.search(pattern, input_lower):
            return Intent.VISION

    # Verifica padroes de codigo
    for pattern in CODE_PATTERNS:
        if re.search(pattern, input_lower):
            return Intent.CODE

    # Default: conversa normal
    return Intent.CHAT


def get_provider_for_intent(intent: Intent) -> Tuple[str, dict]:
    """Retorna o provider e config baseado na intent."""

    import config

    if intent == Intent.CODE:
        if config.CODE_PROVIDER == "local":
            return ("ollama", config.CODE_LOCAL)
        else:
            return (config.CODE_API["provider"], config.CODE_API)

    elif intent == Intent.VISION:
        if config.VISION_PROVIDER == "local":
            return ("ollama", config.VISION_LOCAL)
        else:
            return ("gemini", config.VISION_GEMINI)

    else:  # CHAT
        if config.CHAT_PROVIDER == "local":
            return ("ollama", config.CHAT_LOCAL)
        else:
            return ("gemini", config.CHAT_GEMINI)
```

---

## 6. UX DO TERMINAL - ATALHOS E INTERACAO

### 6.1 Mapa de Atalhos de Teclado

| Atalho | Acao | Contexto |
|--------|------|----------|
| `Ctrl+C` | Copiar texto selecionado | Global |
| `Ctrl+V` | Colar texto | Input |
| `Ctrl+X` | Recortar texto | Input |
| `Ctrl+A` | Selecionar tudo | Input ou Chat |
| `Ctrl+Q` | Fechar Luna | Global |
| `Ctrl+T` | Nova conversa | Global |
| `Ctrl+H` | Ver historico | Global |
| `Ctrl+E` | Editar alma | Global |
| `Escape` | Cancelar/Voltar | Modal/Menu |
| `Enter` | Enviar mensagem | Input |
| `Shift+Enter` | Quebra de linha | Input |

### 6.2 Implementacao dos Atalhos

```python
# main.py - Adicionar bindings

from textual.binding import Binding

class LunaApp(App):

    BINDINGS = [
        Binding("ctrl+q", "quit", "Sair", show=True),
        Binding("ctrl+t", "nova_conversa", "Nova Conversa", show=True),
        Binding("ctrl+h", "ver_historico", "Historico", show=False),
        Binding("ctrl+e", "editar_alma", "Editar Alma", show=False),
        Binding("ctrl+c", "copy", "Copiar", show=False),
        Binding("ctrl+v", "paste", "Colar", show=False),
        Binding("ctrl+a", "select_all", "Selecionar Tudo", show=False),
        Binding("escape", "cancel", "Cancelar", show=False),
    ]

    def action_copy(self) -> None:
        """Copia texto selecionado para clipboard."""
        # Implementar com pyperclip
        import pyperclip

        # Tentar pegar texto selecionado do chat
        focused = self.focused
        if hasattr(focused, 'selected_text'):
            pyperclip.copy(focused.selected_text)
            self.notify("Copiado!", timeout=1)

    def action_paste(self) -> None:
        """Cola texto do clipboard no input."""
        import pyperclip

        try:
            text = pyperclip.paste()
            input_widget = self.query_one("#user_input", Input)
            input_widget.insert_text_at_cursor(text)
        except:
            pass

    def action_select_all(self) -> None:
        """Seleciona todo o texto do input."""
        try:
            input_widget = self.query_one("#user_input", Input)
            input_widget.action_select_all()
        except:
            pass

    def action_nova_conversa(self) -> None:
        """Inicia nova conversa."""
        self.call_later(self._start_nova_conversa)

    def action_cancel(self) -> None:
        """Cancela operacao atual ou fecha modal."""
        if self.screen.is_modal:
            self.pop_screen()
```

### 6.3 Click no Bloco de Codigo para Copiar

```python
# src/ui/widgets.py - CodeBlock com click-to-copy

from textual.widgets import Static
from textual.message import Message
from rich.syntax import Syntax
import pyperclip


class CodeBlock(Static):
    """Bloco de codigo com click para copiar."""

    class Copied(Message):
        """Mensagem emitida quando codigo e copiado."""
        pass

    def __init__(self, code: str, language: str = "python", **kwargs):
        super().__init__(**kwargs)
        self.code = code
        self.language = language
        self.add_class("code-block")

    def compose(self):
        syntax = Syntax(
            self.code,
            self.language,
            theme="dracula",
            line_numbers=True,
            word_wrap=True,
        )
        yield Static(syntax, classes="code-content")

    def on_click(self) -> None:
        """Clica no bloco = copia o codigo."""
        try:
            pyperclip.copy(self.code)
            self.post_message(self.Copied())
            self.app.notify("Codigo copiado!", timeout=1.5)
        except Exception as e:
            self.app.notify(f"Erro ao copiar: {e}", severity="error")

    def on_mount(self) -> None:
        """Tooltip de instrucao."""
        self.tooltip = "Clique para copiar"
```

### 6.4 Menu de Contexto (Botao Direito)

```python
# src/ui/context_menu.py

from textual.widgets import Static, ListView, ListItem
from textual.containers import Vertical
from textual.screen import ModalScreen


class ContextMenuItem(ListItem):
    def __init__(self, label: str, action: str, shortcut: str = ""):
        super().__init__()
        self.label = label
        self.action = action
        self.shortcut = shortcut

    def compose(self):
        text = f"{self.label}"
        if self.shortcut:
            text += f"  [{self.shortcut}]"
        yield Static(text)


class ContextMenu(ModalScreen):
    """Menu de contexto do botao direito."""

    CSS = """
    ContextMenu {
        align: center middle;
    }

    #context-menu-container {
        width: 30;
        height: auto;
        max-height: 15;
        background: #2d2f3d;
        border: solid #6272a4;
        padding: 0;
    }

    ContextMenuItem {
        padding: 0 1;
        height: 1;
    }

    ContextMenuItem:hover {
        background: #44475a;
    }

    ContextMenuItem:focus {
        background: #bd93f9;
        color: #282a36;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Fechar"),
    ]

    def __init__(self, x: int, y: int):
        super().__init__()
        self.menu_x = x
        self.menu_y = y

    def compose(self):
        with Vertical(id="context-menu-container"):
            yield ListView(
                ContextMenuItem("Copiar", "copy", "Ctrl+C"),
                ContextMenuItem("Colar", "paste", "Ctrl+V"),
                ContextMenuItem("Selecionar Tudo", "select_all", "Ctrl+A"),
                ContextMenuItem("─" * 20, "separator"),
                ContextMenuItem("Nova Conversa", "nova_conversa", "Ctrl+T"),
                ContextMenuItem("Ver Historico", "ver_historico", "Ctrl+H"),
                ContextMenuItem("─" * 20, "separator"),
                ContextMenuItem("Sair", "quit", "Ctrl+Q"),
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ContextMenuItem):
            if item.action != "separator":
                self.dismiss()
                self.app.call_later(getattr(self.app, f"action_{item.action}", lambda: None))
```

### 6.5 Output Mode (Code Dump)

Modo especial onde Luna so cospe codigo, sem conversa.

```python
# src/ui/code_output_panel.py

from textual.widgets import Static, TextArea
from textual.containers import Vertical


class CodeOutputPanel(Static):
    """Painel de output puro de codigo - sem chat, so resultado."""

    CSS = """
    CodeOutputPanel {
        height: 100%;
        background: #1e1f29;
    }

    #code-output-area {
        height: 1fr;
        background: #1e1f29;
        border: none;
    }

    #code-status {
        height: 1;
        background: #2d2f3d;
        color: #6272a4;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code_buffer = ""

    def compose(self):
        yield Static("Code Output Mode - Clique para copiar", id="code-status")
        yield TextArea(id="code-output-area", read_only=True)

    def append_code(self, code: str) -> None:
        """Adiciona codigo ao buffer."""
        self.code_buffer += code + "\n\n"
        area = self.query_one("#code-output-area", TextArea)
        area.load_text(self.code_buffer)
        area.scroll_end()

    def clear(self) -> None:
        """Limpa o buffer."""
        self.code_buffer = ""
        area = self.query_one("#code-output-area", TextArea)
        area.load_text("")

    def on_click(self) -> None:
        """Clica = copia tudo."""
        import pyperclip
        pyperclip.copy(self.code_buffer)
        self.app.notify("Todo codigo copiado!", timeout=1.5)
```

---

## 7. FLUXO DE OPERACAO

### 7.1 Startup

```
1. Luna inicia
2. Verifica .env para providers configurados
3. Para cada provider "local":
   - Verifica se Ollama esta rodando
   - Verifica se modelo esta baixado
   - Se nao, oferece baixar ou usa fallback
4. Carrega modelos em ordem de prioridade:
   - STT (precisa ouvir primeiro)
   - TTS (precisa falar)
   - CHAT (precisa conversar)
   - VISION e CODE (sob demanda)
```

### 7.2 Runtime

```
Usuario envia mensagem
        │
        ▼
┌───────────────────┐
│  detect_intent()  │
└────────┬──────────┘
         │
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
  CHAT      CODE     VISION
    │         │         │
    ▼         ▼         ▼
 Ollama    Ollama    Ollama
 dolphin   qwen2.5   minicpm
    │         │         │
    └────┬────┴─────────┘
         │
         ▼
   pos_process()
   - Remove emojis
   - Aplica persona
   - Formata output
         │
         ▼
   Exibe no chat
   (ou CodeOutputPanel)
```

---

## 8. CHECKLIST DE IMPLEMENTACAO

### Fase 1: Modelos Locais
- [ ] Instalar Ollama
- [ ] Baixar dolphin-mistral (conversa)
- [ ] Baixar qwen2.5-coder (codigo)
- [ ] Baixar minicpm-v (visao)
- [ ] Criar wrapper unificado para Ollama
- [ ] Implementar fallback para API se modelo local falhar

### Fase 2: Router
- [ ] Criar src/core/router.py
- [ ] Implementar detect_intent()
- [ ] Integrar com fluxo existente
- [ ] Testar roteamento automatico

### Fase 3: UX Terminal
- [ ] Adicionar BINDINGS ao LunaApp
- [ ] Implementar action_copy/paste/select_all
- [ ] Instalar pyperclip como dependencia
- [ ] Criar CodeBlock com click-to-copy
- [ ] Testar todos os atalhos

### Fase 4: Menu de Contexto
- [ ] Criar ContextMenu
- [ ] Integrar com right-click
- [ ] Testar em diferentes terminais

### Fase 5: Code Output Mode
- [ ] Criar CodeOutputPanel
- [ ] Adicionar toggle para modo code
- [ ] Implementar streaming de codigo

### Fase 6: Testes e Polish
- [ ] Testar 100% local (sem internet)
- [ ] Testar com APIs pagas
- [ ] Testar swap entre providers
- [ ] Documentar no README

---

## 9. DEPENDENCIAS NOVAS

```txt
# requirements.txt - adicionar

# Clipboard
pyperclip>=1.8.2

# Ollama client
ollama>=0.1.0

# Opcional: APIs pagas
openai>=1.0.0        # Para Whisper API
```

---

## 10. COMANDOS DE SETUP

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelos (primeira vez)
ollama pull dolphin-mistral      # ~4GB - Conversa
ollama pull qwen2.5-coder:7b     # ~4GB - Codigo
ollama pull minicpm-v            # ~4GB - Visao

# Verificar modelos instalados
ollama list

# Testar modelo
ollama run dolphin-mistral "Ola, me chamo Luna"
```

---

---

## 11. THREADING E PERFORMANCE - ANALISE DE GARGALOS

### 11.1 Arquitetura Atual de Threads

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREADS ATUAIS (7)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ AUDIO       │───▶│ TRANSCR.   │───▶│ PROCESSING  │         │
│  │ CAPTURE     │    │ (Whisper)   │    │ (Gemini)    │         │
│  │             │    │             │    │             │         │
│  │ 44100Hz     │    │ VAD + STT   │    │ LLM Call    │         │
│  │ Chunk=1024  │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                                      │                │
│         │           ┌─────────────┐            │                │
│         │           │ COORDINATOR │◀───────────┘                │
│         │           │             │                             │
│         │           │ Orquestra   │                             │
│         │           └──────┬──────┘                             │
│         │                  │                                    │
│         ▼                  ▼                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ MONITOR     │    │ ANIMATION   │    │ TTS         │         │
│  │             │    │             │    │             │         │
│  │ Health      │    │ Frames      │    │ ElevenLabs  │         │
│  │ Check 30s   │    │             │    │ Chatterbox  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 PROBLEMAS IDENTIFICADOS NOS LOGS

#### PROBLEMA 1: TTS BLOQUEANTE (CRITICO)

```
LOG EVIDENCIA:
09:51:26,607 - Chamando API ElevenLabs...
09:51:29,783 - Audio recebido do ElevenLabs      [+3.1s]
09:51:39,024 - ElevenLabs executado com sucesso  [+9.2s]
09:51:39,025 - PERF CRITICAL: boca.falar took 12.418s

OUTRO EXEMPLO:
09:51:53,505 - Chamando API ElevenLabs...
09:51:57,073 - Audio recebido                    [+3.5s]
09:52:10,867 - Executado com sucesso             [+13.8s]
09:52:10,879 - PERF CRITICAL: boca.falar took 17.385s
```

**Diagnostico:**
- API call demora ~3s (aceitavel)
- TOCAR o audio demora +10-14s (BLOQUEANTE!)
- A funcao `falar()` espera o audio TERMINAR de tocar antes de retornar
- Isso trava toda a UI enquanto Luna "fala"

**Solucao:**
```python
# ERRADO (atual - bloqueante)
def falar(self, texto: str):
    audio = self.elevenlabs.generate(texto)  # 3s
    self.play_audio(audio)  # BLOQUEIA ate terminar (10s+)
    return  # So retorna depois de tocar tudo

# CORRETO (fire-and-forget)
def falar(self, texto: str):
    audio = self.elevenlabs.generate(texto)  # 3s
    self.tts_queue.put(audio)  # Retorna imediatamente
    return  # UI liberada

# Thread separada consome a queue
def _tts_playback_loop(self):
    while self.running:
        audio = self.tts_queue.get()
        self.play_audio(audio)  # Toca em background
```

---

#### PROBLEMA 2: QUEUE DE AUDIO TRANSBORDANDO (CRITICO)

```
LOG EVIDENCIA:
09:52:11,047 - [AUDIO_CAPTURE] Stats: captured=1, sent=0, queue=0
09:52:11,444 - Queue cheia! chunks_captured=200
09:52:12,438 - Queue cheia! chunks_captured=300
09:52:12,609 - Queue cheia! chunks_captured=400
09:52:12,635 - Queue cheia! chunks_captured=500
09:52:12,639 - Queue cheia! chunks_captured=600
09:52:12,641 - Queue cheia! chunks_captured=700
...
09:52:14,931 - Queue cheia! chunks_captured=2200
```

**Diagnostico:**
- Em ~3 segundos, a queue foi de 0 a 2200+ chunks
- Audio capture produz a 44100Hz / 1024 = ~43 chunks/segundo
- Mas a log mostra 2200 chunks em 3s = ~733 chunks/segundo (BUG!)
- A TranscriptionThread nao esta consumindo rapido o suficiente
- Chunks estao sendo PERDIDOS (queue cheia = descartado)

**Causas provaveis:**
1. Whisper ainda carregando enquanto audio ja captura
2. VAD muito lento para processar
3. Queue com tamanho fixo muito pequeno
4. GIL do Python causando contencao

**Solucao:**
```python
# 1. Lazy start da captura (so comeca quando Whisper pronto)
class TranscriptionThread:
    def run(self):
        self._load_whisper()  # Carrega primeiro
        self.whisper_ready.set()  # Sinaliza
        # Agora sim processa

class AudioCaptureThread:
    def run(self):
        self.whisper_ready.wait()  # Espera Whisper
        self._start_capture()  # So entao comeca

# 2. Backpressure inteligente
if self.audio_queue.full():
    # Em vez de descartar, reduz sample rate temporariamente
    self._reduce_capture_rate()

# 3. Queue circular (ring buffer)
from collections import deque
self.audio_buffer = deque(maxlen=1000)  # Descarta mais antigo
```

---

#### PROBLEMA 3: GAP DE INICIALIZACAO

```
LOG EVIDENCIA:
09:51:23,637 - 7/7 threads iniciadas
09:51:23,646 - [AUDIO_CAPTURE] Thread rodando...
09:51:23,684 - [WHISPER] INICIANDO CARREGAMENTO...
09:51:25,107 - [WHISPER] MODELO CARREGADO (1.4s depois)
09:51:25,107 - [TRANSCRIPTION] Thread rodando...
```

**Diagnostico:**
- AudioCapture inicia ANTES do Whisper estar pronto
- 1.4s de audio capturado vai pra queue sem consumidor
- Isso causa o "burst" inicial de queue cheia

**Solucao:** Ordem de inicializacao correta
```python
# Ordem CORRETA de startup:
1. Carregar Whisper (bloqueante, ~2s)
2. Iniciar TranscriptionThread (consumidor)
3. Iniciar AudioCaptureThread (produtor)
4. Iniciar demais threads

# Implementacao:
async def startup_sequence():
    # Fase 1: Modelos (sequencial, bloqueante)
    await load_whisper()
    await load_tts_model()

    # Fase 2: Consumidores primeiro
    transcription_thread.start()
    tts_thread.start()
    processing_thread.start()

    # Fase 3: Produtores por ultimo
    await asyncio.sleep(0.1)  # Garante consumidores prontos
    audio_capture_thread.start()
```

---

#### PROBLEMA 4: THREADS vs ASYNCIO

**Diagnostico:**
- Muitas operacoes sao IO-bound (API calls, file I/O)
- Python GIL limita paralelismo real de threads
- ThreadPoolExecutor adiciona overhead

**Analise de cada thread:**

| Thread | Tipo de Trabalho | Melhor Modelo |
|--------|------------------|---------------|
| audio_capture | IO-bound (hardware) | Thread (correto) |
| transcription | CPU-bound (Whisper) | Process (multiprocessing) |
| processing | IO-bound (API) | Asyncio |
| coordinator | CPU-light | Asyncio |
| animation | CPU-light | Asyncio/Timer |
| tts | IO-bound (API) + CPU (playback) | Thread + Asyncio |
| monitor | CPU-light | Timer |

**Solucao Hibrida:**
```python
# Arquitetura proposta:
#
# THREADS (para trabalho real de CPU/hardware):
#   - AudioCaptureThread (PyAudio precisa de thread)
#   - WhisperProcess (multiprocessing, nao thread!)
#   - AudioPlaybackThread (sounddevice precisa de thread)
#
# ASYNCIO (para IO e coordenacao):
#   - API calls (Gemini, ElevenLabs, DeepSeek)
#   - Coordinator
#   - Animation updates
#   - UI updates

import asyncio
from concurrent.futures import ProcessPoolExecutor

class LunaCore:
    def __init__(self):
        # Pool de processos para CPU-bound
        self.cpu_pool = ProcessPoolExecutor(max_workers=2)

        # Event loop para IO-bound
        self.loop = asyncio.new_event_loop()

    async def process_audio(self, audio_data):
        # Whisper em processo separado (bypassa GIL)
        result = await self.loop.run_in_executor(
            self.cpu_pool,
            self._transcribe_whisper,
            audio_data
        )
        return result

    async def call_llm(self, prompt):
        # API call assincrono (nao bloqueia)
        async with aiohttp.ClientSession() as session:
            response = await session.post(...)
        return response
```

---

### 11.3 METRICAS PARA MONITORAR

```python
# src/core/metrics.py

from dataclasses import dataclass
from time import perf_counter
import threading

@dataclass
class PerformanceMetrics:
    # Latencias (em segundos)
    tts_api_latency: float = 0.0      # Tempo da API call
    tts_playback_latency: float = 0.0 # Tempo de playback
    stt_latency: float = 0.0          # Whisper transcription
    llm_latency: float = 0.0          # Gemini/Ollama response

    # Queues
    audio_queue_size: int = 0
    audio_queue_drops: int = 0        # Chunks perdidos
    tts_queue_size: int = 0

    # Throughput
    chunks_per_second: float = 0.0
    transcriptions_per_minute: float = 0.0

    # Thread health
    thread_alive: dict = None
    thread_cpu_usage: dict = None

class MetricsCollector:
    _instance = None

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._lock = threading.Lock()

    @classmethod
    def get(cls) -> 'MetricsCollector':
        if cls._instance is None:
            cls._instance = MetricsCollector()
        return cls._instance

    def record_latency(self, operation: str, duration: float):
        with self._lock:
            if duration > 5.0:
                logger.error(f"PERF CRITICAL: {operation} took {duration:.3f}s")
            elif duration > 2.0:
                logger.warning(f"PERF SLOW: {operation} took {duration:.3f}s")

            setattr(self.metrics, f"{operation}_latency", duration)

    def record_queue_drop(self):
        with self._lock:
            self.metrics.audio_queue_drops += 1

    def get_report(self) -> dict:
        with self._lock:
            return {
                "latencies": {
                    "tts_api": f"{self.metrics.tts_api_latency:.2f}s",
                    "tts_playback": f"{self.metrics.tts_playback_latency:.2f}s",
                    "stt": f"{self.metrics.stt_latency:.2f}s",
                    "llm": f"{self.metrics.llm_latency:.2f}s",
                },
                "queues": {
                    "audio_size": self.metrics.audio_queue_size,
                    "audio_drops": self.metrics.audio_queue_drops,
                    "tts_size": self.metrics.tts_queue_size,
                },
                "health": "OK" if self.metrics.audio_queue_drops < 10 else "DEGRADED"
            }
```

---

### 11.4 THRESHOLDS DE PERFORMANCE

| Metrica | Aceitavel | Warning | Critico |
|---------|-----------|---------|---------|
| TTS API latency | < 2s | 2-5s | > 5s |
| TTS playback | < 1s overhead | 1-3s | > 3s |
| Whisper latency | < 1s | 1-3s | > 3s |
| LLM latency | < 3s | 3-8s | > 8s |
| Audio queue size | < 50 | 50-100 | > 100 |
| Audio queue drops | 0 | 1-10 | > 10 |
| End-to-end response | < 5s | 5-10s | > 10s |

---

### 11.5 SCRIPT DE DIAGNOSTICO

```python
#!/usr/bin/env python3
# tools/diagnose_performance.py

"""
Analisa logs de sessao e identifica gargalos.
Uso: python diagnose_performance.py session_*.log
"""

import re
import sys
from collections import defaultdict
from datetime import datetime

def parse_log(filepath: str) -> dict:
    issues = defaultdict(list)

    with open(filepath) as f:
        for line in f:
            # Detectar TTS lento
            if "PERF CRITICAL" in line or "PERF SLOW" in line:
                match = re.search(r'(\w+\.\w+) took ([\d.]+)s', line)
                if match:
                    operation, duration = match.groups()
                    issues['slow_operations'].append({
                        'operation': operation,
                        'duration': float(duration),
                        'line': line.strip()
                    })

            # Detectar queue overflow
            if "Queue cheia" in line:
                match = re.search(r'chunks_captured=(\d+)', line)
                if match:
                    issues['queue_overflow'].append(int(match.group(1)))

            # Detectar erros
            if " ERROR " in line:
                issues['errors'].append(line.strip())

    return dict(issues)

def generate_report(issues: dict) -> str:
    report = []
    report.append("=" * 60)
    report.append("RELATORIO DE PERFORMANCE - LUNA")
    report.append("=" * 60)

    # Operacoes lentas
    if 'slow_operations' in issues:
        report.append("\n[OPERACOES LENTAS]")
        for op in issues['slow_operations']:
            status = "CRITICO" if op['duration'] > 10 else "LENTO"
            report.append(f"  {status}: {op['operation']} = {op['duration']:.1f}s")

    # Queue overflow
    if 'queue_overflow' in issues:
        max_chunks = max(issues['queue_overflow'])
        count = len(issues['queue_overflow'])
        report.append(f"\n[QUEUE OVERFLOW]")
        report.append(f"  Ocorrencias: {count}")
        report.append(f"  Max chunks perdidos: {max_chunks}")
        report.append(f"  DIAGNOSTICO: TranscriptionThread nao consome rapido o suficiente")

    # Erros
    if 'errors' in issues:
        report.append(f"\n[ERROS]")
        for err in issues['errors'][:5]:
            report.append(f"  {err}")

    # Recomendacoes
    report.append("\n[RECOMENDACOES]")
    if any(op['duration'] > 10 for op in issues.get('slow_operations', [])):
        report.append("  1. TTS esta bloqueante - implementar playback assincrono")
    if issues.get('queue_overflow'):
        report.append("  2. Queue overflow - iniciar captura so apos Whisper pronto")
        report.append("  3. Considerar ring buffer para audio")

    return "\n".join(report)

if __name__ == "__main__":
    for logfile in sys.argv[1:]:
        issues = parse_log(logfile)
        print(generate_report(issues))
```

---

### 11.6 CHECKLIST DE OTIMIZACAO

**Fase 1: Fixes Criticos**
- [ ] Separar TTS API call de playback (nao bloqueante)
- [ ] Iniciar AudioCapture so apos Whisper carregar
- [ ] Implementar ring buffer para audio queue
- [ ] Adicionar metricas de latencia em pontos criticos

**Fase 2: Refatoracao**
- [ ] Migrar API calls para asyncio
- [ ] Usar multiprocessing para Whisper (bypass GIL)
- [ ] Implementar backpressure na audio queue
- [ ] Criar health checks com thresholds

**Fase 3: Monitoramento**
- [ ] Dashboard de metricas em tempo real
- [ ] Alertas quando thresholds ultrapassados
- [ ] Log estruturado (JSON) para analise
- [ ] Script de diagnostico automatico

---

### 11.7 ARQUITETURA OTIMIZADA PROPOSTA

```
┌─────────────────────────────────────────────────────────────────┐
│                 ARQUITETURA OTIMIZADA                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ASYNCIO EVENT LOOP                    │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ LLM API  │  │ TTS API  │  │ Coord    │  │ Anim    │ │   │
│  │  │ (Gemini) │  │ (11Labs) │  │ inator   │  │ ation   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         │                                       │
│           ┌─────────────┴─────────────┐                        │
│           ▼                           ▼                        │
│  ┌─────────────────┐        ┌─────────────────┐               │
│  │  THREAD POOL    │        │  PROCESS POOL   │               │
│  │                 │        │                 │               │
│  │ - AudioCapture  │        │ - Whisper STT   │               │
│  │ - AudioPlayback │        │ - (CPU-bound)   │               │
│  │ - (IO-bound)    │        │                 │               │
│  └────────┬────────┘        └────────┬────────┘               │
│           │                          │                         │
│           ▼                          ▼                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    RING BUFFER                           │   │
│  │           (audio_queue com backpressure)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

FLUXO OTIMIZADO:
1. AudioCapture -> Ring Buffer (thread)
2. Ring Buffer -> Whisper Process (multiprocessing)
3. Texto -> Asyncio LLM call (non-blocking)
4. Resposta -> Asyncio TTS API (non-blocking)
5. Audio -> AudioPlayback Thread (non-blocking)
```

---

*"A tecnologia e melhor quando aproxima as pessoas." - Matt Mullenweg*

*"Luna nao precisa de cloud. Ela vive no seu terminal. Sempre presente, sempre sua."*
