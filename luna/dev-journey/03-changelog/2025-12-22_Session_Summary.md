# Session Summary - 2025-12-22

## Resumo

Sessao focada em duas areas principais:
1. **Gerenciamento de VRAM** - Resolver CUDA OOM em GPU de 4GB
2. **Sistema de Transicoes TV Static** - Efeitos visuais cinematicos

---

## Problemas Resolvidos

### 1. CUDA Out of Memory

**Problema:** Modelos Ollama ficavam carregados na VRAM indefinidamente, causando OOM ao usar multiplos modelos (chat + visao + whisper).

**Solucao:**
- Adicionado `keep_alive: "30s"` em todas as chamadas Ollama
- Metodos `unload_model()` e `list_loaded_models()` no OllamaClient
- Variaveis de ambiente: `OLLAMA_KEEP_ALIVE=30s`, `OLLAMA_MAX_LOADED_MODELS=1`
- Whisper reduzido de `medium` para `small`
- Embeddings forcados para CPU
- Modelo de visao alterado de `minicpm-v` para `moondream`

### 2. Modelo de Visao Gerando Lixo

**Problema:** minicpm-v gerava texto em thai quando VRAM estava sob pressao.

**Solucao:** Substituido por `moondream` (1.7GB, mais estavel).

---

## Implementacoes

### Sistema de Transicoes TV Static

Implementado sistema completo de transicoes visuais estilo TV analogica:

| Evento | Comportamento |
|--------|---------------|
| Startup | TV static nas 3 areas (banner, status, animacao) com fade out |
| Shutdown | TV static apenas na animacao |
| Processamento | Banner e animacao ocultos, TV static no lugar |
| Entre emocoes | TV static rapido antes de voltar ao `observando` |
| Botao Ver | Fullscreen piscando + TV static ao final |
| Botao Voz (off) | TV static apenas no banner |
| Botao Voz (on) | Transicao para audio visualizer |

### Funcoes Criadas em banner.py

```python
run_startup_static(app, duration=0.8)
run_processing_static(app, on=True)
run_emotion_transition(app, duration=0.5)
run_banner_only_static(app, duration=0.5)
run_fullscreen_piscando(app, duration=2.0)
```

---

## Arquivos Modificados

### Core
- `main.py` - Imports, on_mount (startup static), _perform_vision_capture
- `src/core/animation.py` - Transicao entre emocoes
- `src/core/ollama_client.py` - Metodos de gerenciamento VRAM

### UI
- `src/ui/banner.py` - Novas funcoes de transicao
- `src/ui/screens.py` - Removidos modelos de codigo do Canone

### Luna
- `src/soul/processing_threads.py` - Reset UI com static
- `src/soul/visao.py` - Unload antes de usar visao
- `src/soul/consciencia.py` - Unload antes de usar chat

### Config
- `config.py` - Whisper small, compute_type int8
- `src/data_memory/embeddings.py` - Forcado CPU

### Scripts
- `run_luna.sh` - Variaveis OLLAMA_KEEP_ALIVE
- `install.sh` - Modelos reduzidos, memoria Ollama configurada
- `cleanup_models.sh` - Novo script para limpar modelos antigos

---

## Metricas

### Uso de VRAM (antes vs depois)

| Componente | Antes | Depois |
|------------|-------|--------|
| Whisper | ~2.5GB (medium) | ~1GB (small) |
| Embeddings | ~0.5GB (GPU) | 0GB (CPU) |
| Ollama persistente | Indefinido | 30s timeout |
| Modelo visao | ~4GB (minicpm-v) | ~1.7GB (moondream) |

### Resultado

GPU de 4GB agora suporta uso simultaneo de:
- Whisper small (~1GB)
- Modelo chat dolphin-mistral (~4GB, descarrega apos 30s)
- Modelo visao moondream (~1.7GB, descarrega apos 30s)

---

## Sessao 2 - Navegacao por Teclado e UX

### Implementacoes

#### 1. Sistema de Navegacao por Teclado

- **Foco visual**: Borda roxa (#4f48d0) em elementos focados
- **Navegacao por setas**: Left/Right/Up/Down para mover entre elementos
- **Tab funcional**: Navegacao nativa do Textual preservada
- **GlitchButton.focused**: Classe CSS para estilo de foco em botoes customizados

#### 2. Comandos de Chat

| Comando | Descricao |
|---------|-----------|
| `/teclado` | Ajuda de navegacao por teclado |
| `/comandos` | Lista todos os comandos disponiveis |
| `/user <tipo>` | Filtra mensagens (luna, user, kernel, code) |

#### 3. Melhorias de Resumo de Conversas

- **Trigger alterado**: De 6 mensagens (user+luna) para 2 mensagens do user
- **Contagem isolada**: Apenas mensagens do user disparam resumo

#### 4. Ajustes Visuais

- **Cor dos botoes**: #ad7fa8 (rosa/lilas)
- **Input border**: `round transparent` / `round #4f48d0` no foco
- **Animacao piscando**: FPS aumentado para 240

### Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `main.py` | Bindings de setas, comandos /teclado /comandos /user |
| `src/core/session.py` | Trigger de resumo para 2 msgs do user |
| `src/core/animation.py` | FPS piscando = 240 |
| `src/ui/glitch_button.py` | can_focus=True, classe .focused |
| `src/assets/css/templo_de_luna.css` | Estilos de foco, cor dos botoes |

### Verificacao de Projeto

- **JSON response**: Schema bem implementado (fala_tts, log_terminal, animacao, etc)
- **Arquivos raiz**: Todos essenciais presentes
- **Gitignore**: Completo e organizado
- **README**: Segue template visual

---

## Sessao 3 - Sistema de Onboarding Ritual

### Implementacoes

#### Sistema de Dialogos via CSV

- **CSV Path**: `src/assets/others/Onboarding-tree.csv`
- **12 passos** do ritual de onboarding
- **10 variacoes** por frase (random.choice)
- **Substituicao**: `$N` e `$NOME_DELE` pelo nome do usuario
- **Recusas/Fallbacks** para quando usuario nao interage

#### Revelacao Progressiva

Sistema de "desencanto" gradual da interface:

| Passo | Elemento Revelado | Descricao |
|-------|-------------------|-----------|
| 1 | `#main_input` | Input para nome |
| 3 | Banner LUNA | Nome surge com glitch |
| 4 | `#toggle_voice_call` | Botao Voz |
| 5 | `#olhar` | Botao Ver |
| 7 | `#nova_conversa` | Confissao |
| 8 | `#ver_historico` | Relicario |
| 9 | `#editar_alma` | Custodia |
| 10 | `#canone`, `#quit` | Canone e Requiem |
| 11 | `#attach_file` | Anexar |

#### Classes CSS Adicionadas

```css
.onboarding-hidden { display: none; opacity: 0; }
.onboarding-revealed { border: double #bd93f9; background: rgba(...); }
```

### Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `src/soul/onboarding.py` | Reescrito com OnboardingDialogues + CSV |
| `src/assets/css/templo_de_luna.css` | Classes .onboarding-hidden/revealed |

---

---

## Sessao 4 - Onboarding Ritual Aprimorado

### Implementacoes

#### 1. Hiper-Descricao do Usuario (Vision)

Novo metodo `hiper_descrever_pessoa()` em `visao.py`:
- Prompt especializado para descricao poetica e detalhada
- Captura: rosto, cabelo, pele, expressao, vestimenta, ambiente
- Tom intimo e sedutor (personalidade Luna)
- Salva descricao em `data_memory/faces/{nome}.json`

#### 2. Perfil Visual Persistente

Novo metodo `salvar_perfil_visual()` em `visao.py`:
- Salva foto JPG em `data_memory/faces/`
- Salva JSON com descricao, data, versao
- Integrado ao perfil do usuario em `user_profile.json`

#### 3. OnboardingStaticOverlay (banner.py)

Nova classe para revelacao granular:
- TV static cobre TODA a interface no inicio
- `reveal_element(id)` - revela elementos individuais com glitch
- `reveal_banner()` - revela nome LUNA apos receber nome do user
- Animacao de revelacao com classes `.glitch-reveal` e `.revealed-stable`

#### 4. Deteccao de Providers Premium

Metodo `_detect_premium_providers()` em `onboarding.py`:
- Detecta ElevenLabs via `config.ELEVENLABS_API_KEY`
- Detecta Gemini via `config.GOOGLE_API_KEY`
- Usa ElevenLabs para TTS com parametros de estilo variados
- Logs informativos sobre providers ativos

#### 5. TTS com Estilo Variavel

`_falar_onboarding()` agora aceita:
- `stability` (0.0-1.0): estabilidade da voz
- `style` (0.0-1.0): expressividade

Valores usados por fase:
| Fase | Stability | Style | Tom |
|------|-----------|-------|-----|
| Pergunta nome | 0.7 | 0.3 | Formal |
| Prazer conhecer | 0.5 | 0.5 | Equilibrado |
| Voz/Visao | 0.4 | 0.6 | Sedutor |

### Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `src/soul/visao.py` | +hiper_descrever_pessoa(), +salvar_perfil_visual() |
| `src/soul/onboarding.py` | OnboardingStaticOverlay, ElevenLabs, hiper-descricao |
| `src/ui/banner.py` | +OnboardingStaticOverlay class |
| `src/assets/css/templo_de_luna.css` | +.glitch-reveal, +.revealed-stable |

### Fluxo do Onboarding Atualizado

```
1. TV static fullscreen (tudo coberto)
2. Revela INPUT -> pergunta nome
3. Detecta genero via CSV -> pergunta pronome
4. Revela BANNER LUNA -> nome surge com glitch
5. Revela BOTAO VOZ -> convida a falar
6. Revela BOTAO VER -> captura foto
7. HIPER-DESCRICAO -> Gemini descreve user em detalhes
8. Salva perfil visual em data_memory/faces/
9. Revela restante dos botoes progressivamente
10. TV static para -> interface completa revelada
```

---

## Proximos Passos

1. Testar onboarding completo end-to-end
2. Verificar hiper-descricao com Gemini Vision
3. Validar persistencia do perfil visual
4. Ajustar timings de revelacao se necessario

---

## Comandos Uteis

```bash
# Verificar modelos carregados
curl -s http://localhost:11434/api/ps | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'{m[\"name\"]}: {m.get(\"size_vram\",0)//1024//1024}MB') for m in d.get('models',[])]"

# Descarregar todos os modelos
curl http://localhost:11434/api/generate -d '{"model": "dolphin-mistral", "keep_alive": 0}'

# Limpar modelos antigos
./cleanup_models.sh
```
