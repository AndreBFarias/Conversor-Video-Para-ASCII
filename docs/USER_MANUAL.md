# Extase em 4R73 - Manual do Usuario

## Visao Geral

Extase em 4R73 e um conversor de videos para arte ASCII colorida com suporte a GPU CUDA, efeitos visuais em tempo real e modulacao por audio.

---

## Instalacao

### Via .deb (Ubuntu/Debian)
```bash
sudo dpkg -i extase-em-4r73_2.2.0_all.deb
sudo apt-get install -f
```

### Via Script
```bash
git clone https://github.com/AndreBFarias/Conversor-Video-Para-ASCII
cd Conversor-Video-Para-ASCII
./install.sh
```

---

## Interface Principal

### 1. Selecao de Arquivo
- **Selecionar Arquivo**: Escolhe video ou imagem para converter
- **Selecionar Pasta**: Processa multiplos arquivos em batch
- **Selecionar ASCII**: Abre arquivo .txt com arte ASCII

### 2. Presets de Qualidade
| Preset | Resolucao | Uso |
|--------|-----------|-----|
| Mobile | 100x25 | Dispositivos moveis |
| Low | 120x30 | PCs antigos |
| Medium | 180x45 | Uso geral |
| High | 240x60 | Alta qualidade |
| Very High | 300x75 | Maxima definicao |

### 3. Motor Grafico
- **ASCII**: Conversao tradicional com caracteres
- **Pixel Art**: Blocos coloridos com paletas retro

---

## Calibrador de Chroma Key

### Acesso
Clique em "Calibrar Chroma Key" na interface principal.

### Paineis
1. **Original**: Video/webcam original
2. **Chroma**: Visualizacao da mascara de chroma key
3. **Resultado**: Preview ASCII em tempo real

### Controles HSV

| Slider | Funcao | Range |
|--------|--------|-------|
| H Min/Max | Matiz (tom de cor) | 0-180 |
| S Min/Max | Saturacao | 0-255 |
| V Min/Max | Valor (brilho) | 0-255 |
| Erode | Remove ruido | 0-10 |
| Dilate | Preenche buracos | 0-10 |

### Atalhos

| Tecla | Acao |
|-------|------|
| `a` | Auto-detect chroma key |
| `p` | Ciclar presets |
| `r` | Reset para valores padrao |
| `s` | Salvar configuracoes |
| `Space` | Pausar/Continuar |
| `Esc` | Fechar calibrador |

### Presets de Chroma Key
- **Studio**: Verde de estudio profissional
- **Natural**: Verde natural/outdoor
- **Bright**: Verde vibrante/iluminado

---

## Efeitos Visuais (PostFX)

### Bloom
Adiciona brilho neon em areas claras.
- **Intensity**: Forca do efeito (0.0-2.0)
- **Radius**: Tamanho do glow (5-30)
- **Threshold**: Limite de brilho (50-200)

### Chromatic Aberration
Separacao RGB nas bordas (efeito de lente).
- **Shift**: Deslocamento em pixels (5-20)

### Scanlines
Linhas horizontais estilo CRT.
- **Intensity**: Escurecimento das linhas (0.3-1.0)
- **Spacing**: Espacamento entre linhas (2-5)

### Glitch
Distorcao aleatoria estilo VHS.
- **Intensity**: Probabilidade de glitch (0.3-0.8)
- **Block Size**: Tamanho dos blocos (4-16)

---

## Style Transfer (Presets de Estilo)

### Presets Disponiveis

| Preset | Descricao |
|--------|-----------|
| None | Original, sem efeito |
| Sketch | Desenho a lapis |
| Ink | Nanquim com alto contraste |
| Comic | Estilo HQ/Manga |
| Neon | Cores vibrantes com glow |
| Emboss | Relevo 3D |
| Cyberpunk | Neon magenta/ciano com bordas brilhantes |

---

## Motion Blur (Optical Flow)

Efeito de rastro de movimento baseado em analise de fluxo optico.

### Como Funciona
1. Calcula o movimento entre frames consecutivos
2. Aplica blur direcional seguindo a direcao do movimento
3. Areas com mais movimento tem mais blur

### Parametros
| Parametro | Range | Descricao |
|-----------|-------|-----------|
| Intensity | 0.3-1.0 | Forca do efeito |
| Samples | 3-8 | Qualidade (mais = melhor, mais lento) |
| Quality | fast/medium/high | Preset de calculo do flow |

### Quando Usar
- Videos com movimento rapido
- Efeito cinematografico
- Transicoes suaves

### Ativacao
Marque "Optical Flow" no calibrador. O Motion Blur e aplicado automaticamente.

---

## Audio Reactive

### Configuracao

1. Conecte um dispositivo de audio (microfone ou loopback)
2. Ative "Audio Reactive" no calibrador
3. Selecione quais efeitos modular:
   - Bloom (responde ao bass)
   - Chromatic (responde ao bass)
   - Glitch (responde aos agudos)

### Bandas de Frequencia

| Banda | Frequencia | Afeta |
|-------|-----------|-------|
| Bass | 20-250Hz | Bloom, Chromatic, Brightness |
| Mids | 250-4kHz | Brightness |
| Treble | 4k-16kHz | Glitch |

### Sensibilidade
Ajuste os sliders de sensibilidade para cada banda conforme o tipo de audio.

---

## Matrix Rain

Efeito de chuva de caracteres estilo Matrix.

### Modos
- **User**: Sobreposto ao conteudo do usuario
- **Background**: Apenas no fundo (mascarado)
- **Foreground**: Apenas no primeiro plano

### Charsets
- Katakana (caracteres japoneses)
- Binary (0 e 1)
- ASCII (letras e numeros)
- Mixed (combinacao)

### Parametros
- **Particles**: Quantidade de particulas (500-5000)
- **Speed**: Velocidade da queda (0.5-3.0)

---

## Gravacao

### MP4 Screencast
1. Clique no botao "MP4" (icone de filme)
2. A borda fica vermelha durante gravacao
3. Clique novamente para parar
4. Arquivo salvo em ~/Videos

### ASCII (.txt)
1. Clique no botao "TXT" (icone de documento)
2. Grave a sequencia desejada
3. Clique novamente para parar
4. Reproduza com o player integrado

---

## Exportacao

### Formatos Suportados
- **.txt**: ASCII colorido (códigos ANSI)
- **.html**: Player web autocontido
- **.mp4**: Video renderizado

### Conversao em Batch
1. Selecione uma pasta com videos
2. Clique em "Converter Pasta"
3. Arquivos processados sequencialmente

---

## Solucao de Problemas

### GPU nao detectada
```bash
nvidia-smi
```
Se nao funcionar, verifique drivers NVIDIA.

### Webcam nao abre
```bash
ls /dev/video*
```
Verifique se o dispositivo existe.

### Audio nao funciona
```bash
pip install pyaudio
```
No Ubuntu: `sudo apt install python3-pyaudio`

### Performance baixa
1. Reduza a resolucao (preset Mobile/Low)
2. Desative efeitos PostFX
3. Ative GPU se disponivel

---

## Atalhos Globais

| Atalho | Acao |
|--------|------|
| `Ctrl+O` | Abrir arquivo |
| `Ctrl+S` | Salvar configuracoes |
| `Ctrl+Q` | Sair |
| `F11` | Tela cheia |

---

## Creditos

- Desenvolvido por: AndreBFarias
- Licenca: GPLv3
- Repositorio: https://github.com/AndreBFarias/Conversor-Video-Para-ASCII
