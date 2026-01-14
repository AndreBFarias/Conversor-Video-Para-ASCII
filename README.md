<div align="center">

[![opensource](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](#)
[![Licença](https://img.shields.io/badge/licença-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![GTK](https://img.shields.io/badge/GTK-3.0-green.svg)](https://www.gtk.org/)
[![Estrelas](https://img.shields.io/github/stars/AndreBFarias/Conversor-Video-Para-ASCII.svg?style=social)](https://github.com/AndreBFarias/Conversor-Video-Para-ASCII/stargazers)
[![Contribuições](https://img.shields.io/badge/contribuições-bem--vindas-brightgreen.svg)](https://github.com/AndreBFarias/Conversor-Video-Para-ASCII/issues)

<div align="center">
<div style="text-align: center;">
  <h1 style="font-size: 2.2em;">Extase em 4R73</h1>
  <img src="assets/logo.png" width="120" alt="Logo Extase em 4R73">
</div>
</div>
</div>

---

### Descrição
Conversor de vídeo para ASCII art em tempo real com aceleração GPU (CUDA), chroma key avançado, e modos especiais como Unicode Braille (4x resolução) e high fidelity texture.

**Características Principais:**
- Conversão em tempo real (30-60 FPS com GPU)
- Chroma key avançado (remoção de fundo verde)
- Unicode Braille (resolução 4x)
- Temporal coherence (anti-flicker)
- Gravação de MP4/GIF/HTML
- Suporte webcam
- Interface GTK3 moderna

---
### Interface
<div align="center">
<img src="assets/background.png" width="700" alt="Interface do Extase em 4R73">
</div>


---


### Calibrador
<div align="center">
<img src="assets/calibrator.png" width="700" alt="Calibrador Chroma Key">
</div>

### Funcionalidades

### Funcionalidades Completas

#### 🎥 Visualização & Renderização
- **Conversão em Tempo Real**: Suporte a Webcam e Arquivos de Vídeo
- **Aceleração GPU (CUDA)**: Pipeline otimizado com CuPy para alta performance (60+ FPS)
- **Modos de Renderização**:
    - **ASCII Colorido**: Caracteres ASCII com cores reais (ANSI 24-bit)
    - **High Fidelity**: Mapeamento de textura baseado em MSE (Mean Squared Error)
    - **Unicode Braille**: 4x mais resolução usando caracteres Braille
    - **Pixel Art**: Paletas retro (GameBoy, NES, SNES, CGA, Monochrome)
    - **Matrix Rain**: Efeito de chuva de caracteres com física de partículas na GPU

#### 🎬 Edição & Processamento
- **Chroma Key Avançado**:
    - Calibrador GUI em tempo real
    - Remoção de fundo verde com ajustes finos (Erode/Dilate)
    - **Batch Processing**: Calibração individual por vídeo em conversões em lote
- **Formatos de Saída**:
    - **MP4**: Vídeo ASCII renderizado com áudio original sincronizado
    - **GIF**: Animações ASCII leves
    - **HTML**: Player web standalone
    - **TXT/ANSI**: Arte estática e sequências de texto

#### 🛠️ Ferramentas
- **Terminal VTE Integrado**: Preview fiel ao terminal do usuário
- **Gravação de Screencast**: Capture a saída exatamente como vista na tela
- **Segmentação Automática**: Remoção de fundo sem chroma key (MediaPipe)

### Instalação

#### Via Pacote .deb (Ubuntu/Debian)

```bash
# Baixar release mais recente
wget https://github.com/AndreBFarias/Conversor-Video-Para-ASCII/releases/latest/download/extase-em-4r73_2.1.0_all.deb

# Instalar
sudo dpkg -i extase-em-4r73_2.1.0_all.deb
sudo apt-get install -f  # Instalar dependências

# Executar
extase-em-4r73
# ou procurar "Extase em 4R73" no menu de aplicativos
```

#### Via Script (Manual)

```bash
git clone https://github.com/AndreBFarias/Conversor-Video-Para-ASCII.git
cd Conversor-Video-Para-ASCII
chmod +x install.sh
./install.sh
```

#### Requisitos

**Obrigatórios:**
- Python 3.10+
- GTK 3.0
- NumPy, OpenCV
- FFmpeg

**Recomendados (para aceleração GPU):**
- GPU NVIDIA (RTX 2000+ series)
- CUDA 11.0+
- CuPy

**Opcionais:**
- kitty terminal (melhor suporte ASCII)
- gnome-terminal (alternativa)

### Uso

**Via menu de aplicativos:** Procure por "Extase em 4R73"

**Via terminal:**
```bash
cd Conversor-Video-Para-ASCII
source venv/bin/activate
python3 main.py
```

### Atalhos do Calibrador

| Tecla | Acao |
|-------|------|
| A | Auto-detectar verde |
| R | Resetar valores |
| S | Salvar configuracao |
| T | Abrir terminal externo |
| Q/ESC | Sair |

### Estrutura

```
Conversor-Video-Para-ASCII/
├── main.py              # Entry point
├── config.ini           # Configuracoes
├── install.sh           # Instalacao automatizada
├── src/
│   ├── app/             # Aplicacao GTK principal
│   ├── core/            # Conversores e calibrador
│   └── gui/             # Arquivos Glade
├── data_input/          # Videos de entrada
├── data_output/         # Arte ASCII gerada
└── docs/                # Documentacao
```

### Documentacao

- [Referencia de Configuracao](docs/CONFIG_REFERENCE.md)

### Licenca

GPLv3 - Veja [LICENSE](LICENSE) para detalhes.

