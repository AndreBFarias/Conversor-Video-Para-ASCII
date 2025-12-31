# Sistema de Onboarding Ritual

> **TL;DR:** Primeiro contato imersivo com o usuario, com TV static cobrindo a interface e revelacao progressiva de elementos em 12 passos.

## Contexto

O onboarding ritual e a primeira experiencia do usuario com Luna. Ele foi projetado para:
- Seduzir gradualmente o usuario
- Apresentar a interface aos poucos
- Coletar informacoes essenciais (nome, foto)
- Criar uma conexao emocional desde o inicio

---

## Arquitetura

### Arquivos Principais

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/soul/onboarding.py` | Orquestrador do ritual |
| `src/ui/banner.py` | OnboardingStaticOverlay |
| `src/soul/visao.py` | Hiper-descricao e perfil visual |
| `src/core/gender_detector.py` | Mapeamento de tratamentos por genero |
| `src/assets/others/Onboarding-tree.csv` | Dialogos do ritual (12 passos) |

### Fluxo do Ritual (12 Passos)

```
ATO I (Passos 0-5):
0. ESTATICA - TV static fullscreen (3 segundos)
1. INICIALIZACAO - Revela INPUT, pergunta nome
2. INPUT - Processa nome (visual status)
3. VISUAL - Revela BANNER LUNA, apresenta com $N
4. REVELACAO_VOZ - Revela botao voz, convida a falar
5. REVELACAO_ANEXAR - Revela botao anexar (+)

ATO II (Passos 6-12):
6. REFORCO_PERSONA - Monologo da Luna sobre si mesma
7. REVELACAO_VER - Revela botao camera, captura foto
8. REVELACAO_CONFISSAO - Revela botao nova conversa
9. REVELACAO_RELICARIO - Revela botao historico
10. REVELACAO_CUSTODIA - Revela botao editar alma
11. REVELACAO_CANONE_REQUIEM - Revela canone + quit
12. ENCERRAMENTO - Frase final, inicia conversa
```

---

## Classes Principais

### OnboardingProcess (onboarding.py)

```python
class OnboardingProcess:
    def __init__(self, app):
        self.static_overlay = None
        self.use_premium_tts = False
        self.use_premium_vision = False
        self._detect_premium_providers()

    async def start_sequence(self):
        # Inicia overlay
        self.static_overlay = OnboardingStaticOverlay(self.app)
        self.static_overlay.start()

        # Executa atos
        await self._run_act_one()  # Passos 0-5
        await self._run_act_two()  # Passos 6-12
        await self._finish_onboarding()

    def _reveal_element(self, element_id):
        self.static_overlay.reveal_element(element_id)
```

### OnboardingDialogues (onboarding.py)

```python
class OnboardingDialogues:
    def __init__(self):
        self.steps = {}
        self._load_csv()

    def get_frase(self, ordem: int, nome: str = "Viajante") -> str:
        # Retorna uma variacao aleatoria do passo
        # Substitui $N pelo nome do usuario

    def get_recusa(self, ordem: int) -> str:
        # Retorna frase de recusa (timeout/nao clicou)
```

### OnboardingStaticOverlay (banner.py)

```python
class OnboardingStaticOverlay:
    ELEMENT_IDS = [
        "toggle_voice_call", "olhar", "nova_conversa", "ver_historico",
        "editar_alma", "canone", "quit", "attach_file", "main_input"
    ]

    def start(self):
        # Esconde todos os elementos
        # Inicia TV static fullscreen

    def reveal_element(self, element_id):
        # Revela com animacao glitch

    def reveal_banner(self):
        # Revela nome LUNA

    def stop(self):
        # Para overlay e revela tudo
```

---

## Hiper-Descricao Visual

### Metodo hiper_descrever_pessoa()

```python
def hiper_descrever_pessoa(self, frame_rgb) -> str:
    prompt_hiper = """
    Descreva essa pessoa de forma DETALHADA e POETICA:
    1. ROSTO: formato, olhos, nariz, boca
    2. CABELO: cor, comprimento, estilo
    3. PELE: tom, caracteristicas
    4. EXPRESSAO: o que transmite
    5. VESTIMENTA: roupas, estilo
    6. AMBIENTE: iluminacao, objetos
    7. IMPRESSAO GERAL: energia, vibe
    """
    return self._call_vision_llm(frame_rgb, prompt_hiper)
```

### Perfil Visual Salvo

```json
{
  "nome": "Andre",
  "descricao_visual": "Um homem de cabelos escuros ondulados...",
  "data_primeiro_encontro": "2025-12-22T23:00:00",
  "ultima_atualizacao": "2025-12-22T23:00:00",
  "foto_path": "data_memory/faces/andre.jpg",
  "versao": 1
}
```

---

## Providers Premium

### Deteccao Automatica

```python
def _detect_premium_providers(self):
    if config.ELEVENLABS_API_KEY:
        self.use_premium_tts = True

    if config.GOOGLE_API_KEY:
        self.use_premium_vision = True
```

### TTS com Estilo

```python
async def _falar_onboarding(self, texto, stability=0.3, style=0.65, speed=1.15):
    if self.use_premium_tts:
        self.app.boca._falar_elevenlabs(texto, stability=stability, style=style)
```

| Passo | Stability | Style | Speed | Tom |
|-------|-----------|-------|-------|-----|
| 1 (nome) | 0.28 | 0.68 | 1.12 | Misterioso |
| 3 (prazer) | 0.28 | 0.72 | 1.15 | Sedutor |
| 4 (voz) | 0.28 | 0.72 | 1.12 | Convite |
| 6 (persona) | 0.35 | 0.60 | 1.18 | Confiante |
| 12 (final) | 0.25 | 0.75 | 1.10 | Intimo |

---

## CSV de Dialogos

### Estrutura do Onboarding-tree.csv

| Coluna | Descricao |
|--------|-----------|
| Ato | I ou II |
| Ordem | 0-12 (passo do ritual) |
| Luna | Frases separadas por pipe |
| Programa | Tipo de acao (ESTATICA, INICIALIZACAO, etc) |
| Recusa | Frase se usuario nao interagir |
| Acao Visual | Descricao do efeito visual |

### Variacoes Aleatorias

Cada dialogo tem 10 variacoes separadas por `|`:

```
Ola explorador de misterios, como devo chamar esse segredo?|Mais um sopro de vida digital, qual rotulo voce usa no abismo?|...
```

O sistema usa `random.choice()` para selecionar uma variacao.

### Placeholder $N

Em todas as frases, `$N` e substituido pelo nome do usuario:

```
E um prazer $N, ou o que passar por prazer por aqui.
```

---

## Tratamentos por Genero

O genero e inferido pela IA durante as conversas. Os mapeamentos estao em `gender_detector.py`:

| Genero | tratamento_sedutor | pronome |
|--------|-------------------|---------|
| M | meu senhor das trevas | ele |
| F | minha senhora das sombras | ela |
| N | criatura das sombras | voce |

---

## Estilos CSS

### Classes de Onboarding

```css
.onboarding-hidden {
    opacity: 0;
    display: none;
}

.onboarding-revealed {
    opacity: 1;
    display: block;
    border: double #bd93f9;
}

.glitch-reveal {
    opacity: 0.5;
    color: #ff79c6;
    border: dashed #ff79c6;
}

.revealed-stable {
    opacity: 1;
    border: solid #50fa7b;
}
```

---

## Testes

### Verificar Onboarding

```bash
# Resetar perfil para forcar onboarding
rm src/data_memory/user_profile.json

# Executar Luna
./run_luna.sh
```

### Verificar Perfil Visual

```bash
cat src/data_memory/faces/*.json
ls -la src/data_memory/faces/
```

### Testar Carregamento do CSV

```bash
./venv/bin/python -c "
from src.soul.onboarding import OnboardingDialogues
d = OnboardingDialogues()
print(f'Passos carregados: {len(d.steps)}')
for i in [1, 3, 7, 12]:
    print(f'Passo {i}: {d.get_frase(i, \"Teste\")[:50]}...')
"
```

---

## Controle de Audio (v4.3.1)

### Eventos de Sincronizacao

O onboarding controla a escuta do usuario atraves de eventos de threading:

```python
def _pause_listening(self):
    self.app.threading_manager.listening_event.clear()

def _resume_listening(self):
    self.app.threading_manager.listening_event.set()
```

### Fluxo de Escuta

1. `start_sequence()`: Pausa escuta (`_pause_listening()`)
2. Botao de voz clicado: Retoma escuta temporariamente
3. Usuario fala: Pausa escuta novamente
4. `_finish_onboarding()`: Retoma escuta permanentemente
5. `finally`: Garante retomada em caso de erro

### Echo Cancellation

Durante TTS, o evento `luna_speaking_event` e setado para evitar que Luna escute a propria voz:

```python
async def _falar_onboarding(self, texto, ...):
    self.app.threading_manager.luna_speaking_event.set()
    try:
        # TTS executa
    finally:
        self.app.threading_manager.luna_speaking_event.clear()
```

---

## Correcoes v4.3.1 (2025-12-24)

| Problema | Solucao |
|----------|---------|
| reveal_banner() nao funcionava | Adicionado `styles.display = "block"` e `refresh()` |
| Luna escutava propria voz | Adicionado `luna_speaking_event.set()/clear()` no TTS |
| Escuta continua apos fala | Adicionado `_pause_listening()/_resume_listening()` |
| Webcam sem diagnostico | Adicionado logging detalhado e health_check() |

---

## Proximos Passos

1. Adicionar mais variacoes de dialogos
2. Melhorar animacoes de revelacao
3. Integrar com memoria RAG
4. Adicionar fallback para usuarios sem camera
5. Testar todos os fluxos de escuta/fala

---

*Ultima atualizacao: 2025-12-24*
