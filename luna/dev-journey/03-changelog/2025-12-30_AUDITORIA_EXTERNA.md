# LUNA - Auditoria Externa e Plano de Correções

**Data:** 2025-12-30
**Versão Atual:** 3.8.0
**Arquivos:** 688 | **LOC:** ~55K | **Testes:** 1.268+

---

## SCORECARD DE AUDITORIA

| Categoria | Nota | Observações |
|-----------|------|-------------|
| Arquitetura | 8.0/10 | Separação clara de responsabilidades, threading robusto |
| Documentação | 9.0/10 | Excelente cobertura, dev-journey completo |
| Testes | 7.5/10 | Boa cobertura, alguns testes com falhas preexistentes |
| UI/UX Terminal | 6.5/10 | Inconsistências de layout, problemas de redimensionamento |
| UI/UX Web | 4.0/10 | Dashboard básico, falta paridade com terminal |
| Integração Desktop | 5.0/10 | Módulo criado mas não integrado completamente |
| Sistema de Voz | 7.0/10 | Multi-engine funcional, falta normalização de tags |
| Personalidades | 7.5/10 | Bem desenvolvidas, problemas de acentuação no TTS |

**Nota Geral: 6.8/10**

---

## PROBLEMAS IDENTIFICADOS

### 1. INPUT CONTAINER - Crescimento e Borda

**Sintoma:** Ao usar Ctrl+J para quebrar linha, o input cresce para baixo corretamente, mas a borda do container pai não acompanha. Os botões "+" e "Voz" não se ajustam.

**Causa Raiz:**
```css
/* templo_universal.css */
#input-container {
    height: 4;           /* PROBLEMA: altura fixa */
    min-height: 4;
    max-height: 8;       /* Permite expansão mas... */
    align: center middle; /* ...centraliza verticalmente */
}
```

**Análise:**
- `height: auto` não funciona bem com `align: center middle`
- O container tem `border: heavy` que não redimensiona com conteúdo interno
- Botões têm altura fixa (`height: 3`) mas o container muda

**Correção Necessária:**
```css
#input-container {
    layout: horizontal;
    height: auto;
    min-height: 4;
    max-height: 8;
    border: heavy {text_secondary};
    padding: 0 1;
    align: left bottom;  /* MUDA: ancora no fundo para crescer pra cima */
}

#attach_file, #toggle_voice_call {
    height: auto;
    min-height: 3;
    max-height: 3;
    dock: left;
    margin: auto 0;      /* Centraliza verticalmente dentro do container */
}
```

### 2. ABA ENTIDADE DO CANONE - Layout Diferente

**Sintoma:** A primeira aba do Canone (Entidade) tem layout diferente das demais abas.

**Causa:** A aba Entidade usa componentes diferentes (EntitySelector inline) enquanto as demais usam ScrollableContainer com Selects e Inputs padronizados.

**Arquivos Afetados:**
- `src/ui/screens.py` (CanoneScreen.compose)
- `src/assets/panteao/templo_universal.css` (#entity-scroll)

### 3. BIBLIOTECA DAS PALAVRAS CONJURADAS - Layout Fora de Sincronia

**Sintoma:** A tela de histórico (HistoryScreen) não segue o padrão visual das outras modais.

**Causa:**
```python
# screens.py - HistoryScreen
#history-container usa layout diferente
#history-list não tem padding consistente
#back-button alinhado diferente dos botões Fiat/Eterno Retorno do Canone
```

### 4. ACENTUAÇÃO NAS FALAS DAS ENTIDADES

**Sintoma:** O TTS pronuncia errado palavras acentuadas.

**Causa:** Alguns textos em `config.json` e `alma.txt` das entidades não têm acentos.

**Arquivos a Verificar:**
```
src/assets/panteao/entities/
├── luna/config.json, alma.txt
├── eris/config.json, alma.txt
├── juno/config.json, alma.txt
├── lars/config.json, alma.txt
├── mars/config.json, alma.txt
└── somn/config.json, alma.txt
```

### 5. MÓDULO DE VOZ NÃO UNIFICADO

**Sintoma:** Cada engine (Coqui, Chatterbox, ElevenLabs) tem configuração separada, sem interface unificada para audio_tags.

**Causa:** `src/soul/boca.py` trata cada engine independentemente, sem abstração comum para parâmetros de voz (stability, style, speed).

### 6. WEB DASHBOARD INCOMPLETO

**Sintoma:** Dashboard web básico, sem funcionalidades da versão terminal.

**Faltando:**
- Animações ASCII
- Histórico de conversas (Biblioteca)
- Seletor de entidades funcional
- Configurações (Canone)
- Anexar arquivos
- Visualizador de áudio
- Banner com efeito glitch

### 7. INTEGRAÇÃO DESKTOP INCOMPLETA

**Sintoma:** Módulo `desktop_integration.py` existe mas não está conectado ao fluxo principal.

**Faltando:**
- Atalho .desktop funcional
- Tray icon
- Notificações do sistema
- Clipboard integration
- Idle detection ativo

---

## PROMPT GUIA 1: CORREÇÃO DO INPUT CONTAINER E BORDAS

```markdown
# TAREFA: Corrigir layout do input-container

## CONTEXTO
O input de usuário (#main_input) deve crescer para cima (não para baixo) ao pressionar Ctrl+J.
Os botões "+" e "Voz" devem permanecer alinhados verticalmente ao centro.
A borda do container deve acompanhar o redimensionamento.

## ARQUIVOS A MODIFICAR

### 1. src/assets/panteao/templo_universal.css

Localize a seção `#input-container` e substitua por:

```css
#input-container {
    layout: horizontal;
    height: auto;
    min-height: 4;
    max-height: 8;
    border: heavy {text_secondary};
    background: {background};
    margin-top: 0;
    padding: 0 1;
    align: left bottom;
    content-align: left bottom;
    overflow: visible;
}

#attach_file {
    height: 3;
    min-height: 3;
    max-height: 3;
    margin: auto 0 auto 0;
    width: auto;
    min-width: 4;
}

#toggle_voice_call {
    height: 3;
    min-height: 3;
    max-height: 3;
    margin: auto 0 auto 1;
    width: auto;
    min-width: 6;
}

#main_input {
    width: 1fr;
    height: auto;
    min-height: 3;
    max-height: 6;
    border: round transparent;
    background: {background_input};
    padding: 0 1;
    color: {text_primary};
    margin: auto 0 auto 1;
}
```

### 2. src/ui/multiline_input.py

Localize `_adjust_container_height` e substitua por:

```python
def _adjust_container_height(self) -> None:
    line_count = self.text.count("\n") + 1
    min_lines = 1
    max_lines = 4
    target_lines = max(min_lines, min(line_count, max_lines))
    new_height = 3 + target_lines
    try:
        container = self.parent
        if container and hasattr(container, "styles"):
            container.styles.height = new_height
            container.styles.min_height = new_height
            container.refresh(layout=True)
    except Exception as e:
        logger.debug(f"Ajuste de altura: {e}")
```

### 3. Aplicar mesmas correções em TODOS os CSS de entidades:

- src/assets/panteao/entities/luna/templo_de_luna.css
- src/assets/panteao/entities/eris/templo_de_eris.css
- src/assets/panteao/entities/juno/templo_de_juno.css
- src/assets/panteao/entities/lars/templo_de_lars.css
- src/assets/panteao/entities/mars/templo_de_mars.css
- src/assets/panteao/entities/somn/templo_de_somn.css

## VALIDAÇÃO

1. Executar `./run_luna.sh`
2. Focar no input e pressionar Ctrl+J múltiplas vezes
3. Verificar que:
   - O container cresce para CIMA
   - A borda inferior permanece visível
   - Botões + e Voz permanecem alinhados
   - Máximo de 4 linhas respeitado

## TESTES

```bash
cd ~/Desenvolvimento/Luna
./venv/bin/python -m pytest src/tests/test_multiline_input.py -v
```
```

---

## PROMPT GUIA 2: PADRONIZAÇÃO DO CANONE E BIBLIOTECA

```markdown
# TAREFA: Padronizar layout do Canone e Biblioteca

## CONTEXTO
A aba Entidade do Canone tem layout diferente das demais.
A Biblioteca das Palavras Conjuradas está fora do padrão visual.

## ARQUIVOS A MODIFICAR

### 1. src/ui/screens.py - CanoneScreen

Localize o método `compose` da CanoneScreen e padronize a aba Entidade:

```python
# Na seção da TabPane de Entidade, adicionar VerticalScroll como nas outras abas:

with TabPane("Entidade", id="tab-entity"):
    with VerticalScroll(id="entity-scroll"):
        yield Static("Entidade Ativa", classes="canone-section")
        yield Static("Escolha qual essência manifestar", classes="canone-hint")

        # Usar Select ao invés de componente customizado inline
        entity_options = self._get_entity_options()
        yield Select(
            entity_options,
            id="select-entity",
            value=current_entity,
            allow_blank=False
        )

        yield Static("", id="entity-description", classes="canone-hint")

        yield Static("Trocar Entidade", classes="canone-section")
        yield Static("Abre o selector de entidades", classes="canone-hint")
        yield Button("Invocar Outra Essência", id="btn-invoke-entity", variant="warning")
```

### 2. src/ui/screens.py - HistoryScreen

Padronizar para seguir mesmo padrão do Canone:

```python
def compose(self) -> ComposeResult:
    with Vertical(id="history-overlay"):
        with Vertical(id="history-modal"):
            yield Static("Biblioteca das Palavras Conjuradas", id="history-title")
            yield Static("Onde os ecos do passado repousam", id="history-subtitle")

            yield Input(placeholder="Buscar conversas...", id="history-search")

            with VerticalScroll(id="history-scroll"):
                yield ListView(id="history-list")

            with Horizontal(id="history-footer"):
                yield Button("Eterno Retorno", id="back-button", variant="default")
```

### 3. src/assets/panteao/templo_universal.css

Adicionar estilos para padronizar:

```css
/* --- HISTORY SCREEN PADRONIZADO --- */

HistoryScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.70);
}

#history-overlay {
    width: 100%;
    height: 100%;
    align: center middle;
}

#history-modal {
    width: 80%;
    max-width: 120;
    height: 80%;
    max-height: 60;
    background: rgba(45, 47, 61, 0.80);
    border: solid {text_secondary};
    border-left: wide {primary_color};
    padding: 1 2;
}

#history-title {
    width: 100%;
    text-align: center;
    text-style: bold;
    color: {secondary_color};
    padding: 0;
    margin-bottom: 0;
}

#history-subtitle {
    width: 100%;
    text-align: center;
    color: {text_secondary};
    margin-bottom: 1;
}

#history-search {
    width: 100%;
    margin-bottom: 1;
    background: {background_input};
    border: round {text_secondary};
}

#history-scroll {
    height: 1fr;
    background: transparent;
    padding: 1;
}

#history-footer {
    height: 3;
    align: center middle;
    margin-top: 1;
}
```

## VALIDAÇÃO

1. Abrir Canone (botão Cânone ou Ctrl+E)
2. Verificar que aba Entidade tem mesmo visual das outras
3. Abrir Relicário (botão Relicário ou Ctrl+H)
4. Verificar que Biblioteca tem visual consistente com Canone

## TESTES

```bash
./venv/bin/python -m pytest src/tests/test_screens.py -v
```
```

---

## PROMPT GUIA 3: CORREÇÃO DE ACENTUAÇÃO NAS ENTIDADES

```markdown
# TAREFA: Verificar e corrigir acentuação nas personalidades

## CONTEXTO
O TTS pronuncia incorretamente palavras sem acentos nos arquivos de personalidade.
Precisamos verificar TODOS os arquivos de texto das entidades.

## ARQUIVOS A VERIFICAR

### Estrutura de cada entidade:
```
src/assets/panteao/entities/{entity}/
├── alma.txt          # Soul prompt - VERIFICAR ACENTOS
├── config.json       # Frases e configurações - VERIFICAR ACENTOS
└── {Entity}_frases.md # Frases de treinamento - VERIFICAR ACENTOS
```

### Script de verificação automática:

Criar arquivo `src/tools/check_acentuacao.py`:

```python
#!/usr/bin/env python3
import json
import re
from pathlib import Path

ENTITIES_DIR = Path("src/assets/panteao/entities")

PALAVRAS_COMUNS = {
    "voce": "você",
    "e": "é",  # contexto específico
    "esta": "está",
    "nao": "não",
    "tambem": "também",
    "ja": "já",
    "so": "só",
    "ate": "até",
    "sera": "será",
    "entao": "então",
    "alem": "além",
    "ai": "aí",
    "la": "lá",
    "aqui": "aqui",
    "mae": "mãe",
    "irmao": "irmão",
    "coracao": "coração",
    "emocao": "emoção",
    "razao": "razão",
    "acao": "ação",
    "atencao": "atenção",
    "informacao": "informação",
    "relacao": "relação",
    "solucao": "solução",
    "questao": "questão",
    "funcao": "função",
    "conexao": "conexão",
    "sensacao": "sensação",
    "situacao": "situação",
    "comunicacao": "comunicação",
    "organizacao": "organização",
    "documentacao": "documentação",
    "configuracao": "configuração",
    "animacao": "animação",
    "programacao": "programação",
    "instalacao": "instalação",
    "atualizacao": "atualização",
    "criacao": "criação",
    "apresentacao": "apresentação",
    "operacao": "operação",
    "producao": "produção",
    "integracao": "integração",
    "traducao": "tradução",
    "verificacao": "verificação",
    "execucao": "execução",
    "inicializacao": "inicialização",
    "finalizacao": "finalização",
}

def check_file(filepath: Path) -> list:
    issues = []
    content = filepath.read_text(encoding="utf-8")

    for wrong, correct in PALAVRAS_COMUNS.items():
        pattern = rf'\b{wrong}\b'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                "file": str(filepath),
                "line": line_num,
                "wrong": match.group(),
                "correct": correct,
                "context": content[max(0, match.start()-20):match.end()+20]
            })

    return issues

def main():
    all_issues = []

    for entity_dir in ENTITIES_DIR.iterdir():
        if not entity_dir.is_dir():
            continue

        alma_file = entity_dir / "alma.txt"
        if alma_file.exists():
            all_issues.extend(check_file(alma_file))

        config_file = entity_dir / "config.json"
        if config_file.exists():
            all_issues.extend(check_file(config_file))

        for frases_file in entity_dir.glob("*_frases.md"):
            all_issues.extend(check_file(frases_file))

    print(f"\n{'='*60}")
    print(f"RELATÓRIO DE ACENTUAÇÃO - {len(all_issues)} problemas encontrados")
    print(f"{'='*60}\n")

    for issue in all_issues:
        print(f"[{issue['file']}:{issue['line']}]")
        print(f"  Encontrado: '{issue['wrong']}' -> Sugestão: '{issue['correct']}'")
        print(f"  Contexto: ...{issue['context']}...")
        print()

if __name__ == "__main__":
    main()
```

## EXECUÇÃO

```bash
cd ~/Desenvolvimento/Luna
./venv/bin/python src/tools/check_acentuacao.py > acentuacao_report.txt
```

## CORREÇÕES MANUAIS PRIORITÁRIAS

### Luna (alma.txt):
- "voce" -> "você"
- "nao" -> "não"
- "esta" -> "está"
- "tambem" -> "também"

### Eris (config.json phrases):
- Verificar todas as frases em "saudacao_inicial"
- Verificar "placeholder_input"

### Todas as entidades:
- Verificar frases de fallback
- Verificar frases de status

## VALIDAÇÃO

1. Executar script de verificação
2. Corrigir todos os problemas listados
3. Re-executar script (deve retornar 0 problemas)
4. Testar TTS com frases corrigidas

```bash
./venv/bin/python -c "
from src.soul.boca import Boca
boca = Boca()
boca.falar('Você está preparado para a próxima configuração?')
"
```
```

---

## PROMPT GUIA 4: MÓDULO DE VOZ UNIFICADO

```markdown
# TAREFA: Criar abstração unificada para engines de voz

## CONTEXTO
Cada engine TTS (Coqui, Chatterbox, ElevenLabs) tem configuração separada.
Precisamos de uma interface comum para audio_tags que normalize parâmetros.

## ARQUIVOS A CRIAR

### 1. src/soul/voice_normalizer.py

```python
#!/usr/bin/env python3
"""
Voice Normalizer - Interface unificada para engines TTS.

Normaliza parâmetros de voz entre diferentes engines:
- Coqui XTTS
- Chatterbox
- ElevenLabs

Parâmetros normalizados (0.0 a 1.0):
- stability: Estabilidade/consistência da voz
- style: Expressividade/emoção
- speed: Velocidade de fala
- similarity: Similaridade com voz de referência
"""

from dataclasses import dataclass
from typing import Literal
import json
from pathlib import Path

import config
from src.core.logging_config import get_logger

logger = get_logger(__name__)

EngineType = Literal["coqui", "chatterbox", "elevenlabs"]


@dataclass
class NormalizedVoiceParams:
    stability: float = 0.5
    style: float = 0.5
    speed: float = 1.0
    similarity: float = 0.75

    def to_coqui(self) -> dict:
        return {
            "speed": self.speed,
            "temperature": 1.0 - self.stability,
        }

    def to_chatterbox(self) -> dict:
        return {
            "exaggeration": self.style,
            "cfg_weight": self.stability,
            "temperature": 0.5 + (0.5 * self.style),
        }

    def to_elevenlabs(self) -> dict:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity,
            "style": self.style,
            "use_speaker_boost": self.similarity > 0.7,
        }


class VoiceNormalizer:
    def __init__(self, entity_id: str = None):
        self.entity_id = entity_id or config.get_current_entity_id()
        self._load_entity_config()

    def _load_entity_config(self) -> None:
        config_path = config.ENTITIES_DIR / self.entity_id / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.voice_config = data.get("voice", {})
        else:
            self.voice_config = {}

    def get_params_for_engine(
        self,
        engine: EngineType,
        emotion: str = "neutral"
    ) -> dict:
        base_params = self._get_emotion_params(emotion)

        engine_overrides = self.voice_config.get(engine, {})
        for key in ["stability", "style", "speed", "similarity"]:
            if key in engine_overrides:
                setattr(base_params, key, engine_overrides[key])

        if engine == "coqui":
            return base_params.to_coqui()
        elif engine == "chatterbox":
            return base_params.to_chatterbox()
        elif engine == "elevenlabs":
            return base_params.to_elevenlabs()
        else:
            raise ValueError(f"Engine desconhecida: {engine}")

    def _get_emotion_params(self, emotion: str) -> NormalizedVoiceParams:
        emotion_map = {
            "neutral": NormalizedVoiceParams(0.5, 0.3, 1.0, 0.75),
            "happy": NormalizedVoiceParams(0.4, 0.7, 1.1, 0.75),
            "sad": NormalizedVoiceParams(0.7, 0.2, 0.9, 0.75),
            "angry": NormalizedVoiceParams(0.3, 0.8, 1.2, 0.75),
            "seductive": NormalizedVoiceParams(0.6, 0.6, 0.95, 0.8),
            "curious": NormalizedVoiceParams(0.5, 0.5, 1.05, 0.75),
            "sarcastic": NormalizedVoiceParams(0.4, 0.6, 1.0, 0.75),
        }
        return emotion_map.get(emotion.lower(), emotion_map["neutral"])

    def get_reference_audio(self, engine: EngineType) -> str | None:
        if engine == "coqui":
            return config.get_coqui_reference_audio(self.entity_id)
        elif engine == "chatterbox":
            return config.get_chatterbox_reference_audio(self.entity_id)
        elif engine == "elevenlabs":
            return self.voice_config.get("elevenlabs", {}).get("voice_id")
        return None


def get_voice_normalizer(entity_id: str = None) -> VoiceNormalizer:
    return VoiceNormalizer(entity_id)
```

### 2. Atualizar src/soul/boca.py

Adicionar uso do VoiceNormalizer:

```python
from src.soul.voice_normalizer import get_voice_normalizer

class Boca:
    def __init__(self, entity_id: str = None):
        # ... código existente ...
        self.voice_normalizer = get_voice_normalizer(entity_id)

    def falar(self, texto: str, emotion: str = "neutral", **kwargs):
        engine = self._select_engine()

        params = self.voice_normalizer.get_params_for_engine(engine, emotion)
        reference = self.voice_normalizer.get_reference_audio(engine)

        params.update(kwargs)

        if engine == "elevenlabs":
            return self._speak_elevenlabs(texto, **params)
        elif engine == "coqui":
            return self._speak_coqui(texto, reference, **params)
        elif engine == "chatterbox":
            return self._speak_chatterbox(texto, reference, **params)
```

### 3. Atualizar config.json das entidades

Adicionar seção `voice` padronizada:

```json
{
  "voice": {
    "coqui": {
      "reference_audio": "voice/coqui/reference.wav",
      "stability": 0.5,
      "speed": 1.0
    },
    "chatterbox": {
      "reference_audio": "voice/chatterbox/reference.wav",
      "exaggeration": 0.3,
      "cfg_weight": 0.5
    },
    "elevenlabs": {
      "voice_id": "xxxxx",
      "stability": 0.5,
      "similarity_boost": 0.75,
      "style": 0.5
    }
  }
}
```

## VALIDAÇÃO

```bash
./venv/bin/python -c "
from src.soul.voice_normalizer import get_voice_normalizer

vn = get_voice_normalizer('luna')

print('Coqui params:', vn.get_params_for_engine('coqui', 'happy'))
print('Chatterbox params:', vn.get_params_for_engine('chatterbox', 'happy'))
print('ElevenLabs params:', vn.get_params_for_engine('elevenlabs', 'happy'))
"
```

## TESTES

Criar `src/tests/test_voice_normalizer.py`:

```python
import pytest
from src.soul.voice_normalizer import VoiceNormalizer, NormalizedVoiceParams

class TestNormalizedVoiceParams:
    def test_to_coqui_returns_dict(self):
        params = NormalizedVoiceParams()
        result = params.to_coqui()
        assert isinstance(result, dict)
        assert "speed" in result

    def test_to_elevenlabs_returns_dict(self):
        params = NormalizedVoiceParams()
        result = params.to_elevenlabs()
        assert isinstance(result, dict)
        assert "stability" in result

class TestVoiceNormalizer:
    def test_get_params_for_engine(self):
        vn = VoiceNormalizer("luna")
        params = vn.get_params_for_engine("coqui", "neutral")
        assert isinstance(params, dict)
```
```

---

## PROMPT GUIA 5: WEB DASHBOARD COMPLETO E INTEGRAÇÃO DESKTOP

```markdown
# TAREFA: Expandir Web Dashboard e Integrar Desktop

## CONTEXTO
O dashboard web atual é básico. Precisamos:
1. Adicionar funcionalidades do terminal
2. Completar integração desktop

## PARTE A: WEB DASHBOARD

### 1. Atualizar src/web/templates/dashboard.html

Adicionar seções faltantes:

```html
<!-- Após o card de métricas, adicionar: -->

<!-- ANIMAÇÃO ASCII -->
<div class="card">
    <div class="card-header">Animação</div>
    <pre id="asciiAnimation" class="ascii-display"></pre>
    <div class="animation-name" id="animationName">observando</div>
</div>

<!-- HISTÓRICO -->
<div class="card">
    <div class="card-header">Biblioteca das Palavras Conjuradas</div>
    <div class="history-list" id="historyList">
        <!-- Populado via JS -->
    </div>
</div>

<!-- CONFIGURAÇÕES RÁPIDAS -->
<div class="card">
    <div class="card-header">Configurações</div>
    <div class="quick-settings">
        <label>
            <span>Entidade:</span>
            <select id="entitySelect">
                <option value="luna">Luna</option>
                <option value="eris">Eris</option>
                <option value="juno">Juno</option>
                <option value="lars">Lars</option>
                <option value="mars">Mars</option>
                <option value="somn">Somn</option>
            </select>
        </label>
        <label>
            <span>TTS:</span>
            <select id="ttsSelect">
                <option value="coqui">Coqui (Local)</option>
                <option value="chatterbox">Chatterbox (Local)</option>
                <option value="elevenlabs">ElevenLabs (Cloud)</option>
            </select>
        </label>
    </div>
</div>
```

CSS adicional:

```css
.ascii-display {
    font-family: monospace;
    font-size: 10px;
    line-height: 1.1;
    white-space: pre;
    color: var(--accent);
    background: var(--bg-tertiary);
    padding: 10px;
    border-radius: 8px;
    max-height: 200px;
    overflow: hidden;
}

.history-list {
    max-height: 200px;
    overflow-y: auto;
}

.history-item {
    padding: 10px;
    border-bottom: 1px solid var(--bg-tertiary);
    cursor: pointer;
}

.history-item:hover {
    background: var(--bg-tertiary);
}

.quick-settings label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

.quick-settings select {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
}
```

### 2. Adicionar endpoints em src/web/routes.py

```python
@router.get("/history")
async def get_history(limit: int = 20) -> dict[str, Any]:
    try:
        from src.core.session_history import get_session_history
        history = get_session_history()
        sessions = history.get_sessions_grouped()

        items = []
        for group, session_list in sessions.items():
            for session in session_list[:limit]:
                items.append({
                    "id": session.session_id,
                    "title": session.title,
                    "date": session.date.isoformat(),
                    "preview": session.preview,
                    "message_count": session.message_count
                })

        return {"sessions": items}
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return {"sessions": []}

@router.get("/animation/{entity_id}/{animation_name}")
async def get_animation(entity_id: str, animation_name: str) -> dict[str, Any]:
    try:
        from src.core.animation import AnimationController
        controller = AnimationController(entity_id)
        frames = controller.get_animation_frames(animation_name)
        return {"frames": frames, "fps": 24}
    except Exception as e:
        logger.error(f"Erro ao obter animação: {e}")
        return {"frames": [], "fps": 24}

@router.post("/config/update")
async def update_config(key: str, value: str) -> dict[str, Any]:
    try:
        from dotenv import set_key
        env_path = config.APP_DIR / ".env"
        set_key(str(env_path), key, value, quote_mode="never")
        config.reload_config()
        return {"success": True}
    except Exception as e:
        logger.error(f"Erro ao atualizar config: {e}")
        return {"success": False, "error": str(e)}
```

## PARTE B: INTEGRAÇÃO DESKTOP

### 1. Completar src/tools/setup_desktop_entry.py

Já existe, mas adicionar verificações:

```python
def verify_installation() -> bool:
    desktop_dir = get_desktop_path()
    desktop_file = desktop_dir / "luna.desktop"

    if not desktop_file.exists():
        return False

    # Verificar se ícone existe
    project_root = get_project_root()
    icon_path = get_icon_path(project_root)
    if icon_path == "utilities-terminal":
        return True  # Usando ícone fallback

    return Path(icon_path).exists()
```

### 2. Criar src/core/system_tray.py (se não existir)

```python
#!/usr/bin/env python3
"""
System Tray - Ícone na bandeja do sistema.

Funcionalidades:
- Ícone na bandeja
- Menu de contexto (Nova Conversa, Configurações, Sair)
- Indicador de status (idle, listening, processing)
"""

import threading
from pathlib import Path

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

import config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class LunaTray:
    def __init__(self, app_callback=None):
        self.app_callback = app_callback
        self.icon = None
        self._status = "idle"

        if not TRAY_AVAILABLE:
            logger.warning("pystray não disponível. Tray desabilitado.")
            return

        self._load_icons()
        self._create_menu()

    def _load_icons(self):
        icon_path = config.TRAY_ICON_PATH
        if Path(icon_path).exists():
            self.icon_image = Image.open(icon_path)
        else:
            self.icon_image = self._create_default_icon()

    def _create_default_icon(self) -> Image:
        img = Image.new('RGBA', (64, 64), (40, 42, 54, 255))
        return img

    def _create_menu(self):
        self.menu = pystray.Menu(
            pystray.MenuItem("Nova Conversa", self._on_new_conversation),
            pystray.MenuItem("Configurações", self._on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._on_quit)
        )

    def _on_new_conversation(self):
        if self.app_callback:
            self.app_callback("new_conversation")

    def _on_settings(self):
        if self.app_callback:
            self.app_callback("settings")

    def _on_quit(self):
        if self.app_callback:
            self.app_callback("quit")
        self.stop()

    def start(self):
        if not TRAY_AVAILABLE:
            return

        self.icon = pystray.Icon(
            "Luna",
            self.icon_image,
            "Luna AI Assistant",
            self.menu
        )

        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()
        logger.info("System tray iniciado")

    def stop(self):
        if self.icon:
            self.icon.stop()

    def update_status(self, status: str):
        self._status = status
        # Poderia mudar ícone baseado no status


def get_tray(callback=None) -> LunaTray | None:
    if not TRAY_AVAILABLE:
        return None
    return LunaTray(callback)
```

### 3. Integrar no main.py

Adicionar no `on_mount`:

```python
async def on_mount(self) -> None:
    # ... código existente ...

    # Iniciar system tray
    from src.core.system_tray import get_tray
    self.tray = get_tray(self._tray_callback)
    if self.tray:
        self.tray.start()

def _tray_callback(self, action: str):
    if action == "new_conversation":
        self.call_from_thread(self._start_nova_conversa)
    elif action == "settings":
        self.call_from_thread(lambda: self.push_screen(CanoneScreen()))
    elif action == "quit":
        self.call_from_thread(self.action_quit)
```

## DEPENDÊNCIAS NOVAS

Adicionar ao requirements.txt:

```
pystray>=0.19.0
Pillow>=10.0.0
```

## VALIDAÇÃO

### Web Dashboard:
```bash
./run_interface_web.sh
# Acessar http://localhost:8080/api/dashboard
# Verificar:
# - Animação ASCII aparece
# - Histórico carrega
# - Seletor de entidade funciona
# - Configurações salvam
```

### Desktop:
```bash
./venv/bin/python src/tools/setup_desktop_entry.py
# Verificar:
# - Atalho aparece no menu de aplicativos
# - Ícone correto
# - Abre o terminal correto
```

### System Tray:
```bash
./run_luna.sh
# Verificar:
# - Ícone aparece na bandeja
# - Menu funciona
# - Status atualiza
```

## TESTES

```bash
./venv/bin/python -m pytest src/tests/test_web.py -v
./venv/bin/python -m pytest src/tests/test_desktop_integration.py -v
```
```

---

## RESUMO DOS 5 PROMPTS

| Prompt | Foco | Arquivos Principais |
|--------|------|---------------------|
| 1 | Input Container | templo_universal.css, multiline_input.py |
| 2 | Canone/Biblioteca | screens.py, templo_universal.css |
| 3 | Acentuação | Todos os config.json e alma.txt |
| 4 | Módulo de Voz | voice_normalizer.py (novo), boca.py |
| 5 | Web + Desktop | dashboard.html, routes.py, system_tray.py |

---

## COMO USAR

```bash
# No Claude CLI, diga:
# "Leia o arquivo LUNA_AUDITORIA_E_CORRECOES.md e execute o Step 1"

# Ou diretamente:
# "Corrija o input-container conforme descrito no Prompt Guia 1"
```

---

*Documento gerado por Luna - Auditoria Externa*
*"O caos é apenas ordem aguardando decifração." - Nietzsche (adaptado)*
