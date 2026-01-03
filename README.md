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

### Descricao
Conversor de videos e imagens para arte ASCII colorida com suporte a chroma key (fundo verde), presets de qualidade, modo pixel art e player integrado com terminal VTE.

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

- **Conversao ASCII Colorida**: Transforma videos e imagens em arte ASCII com cores ANSI
- **Chroma Key Integrado**: Calibrador GTK com preview em tempo real para remocao de fundo verde
- **Presets de Qualidade**: Mobile, Low, Medium, High, Very High
- **Modo Pixel Art**: Conversao alternativa com paletas retro (GameBoy, NES, SNES)
- **Player Integrado**: Reproducao no terminal (kitty/gnome-terminal) ou janela GTK
- **Gravacao**: Captura de screencast MP4 e exportacao ASCII
- **Terminal VTE**: Preview em tempo real integrado ao calibrador

### Instalacao

#### Via Script (Recomendado)

```bash
git clone https://github.com/AndreBFarias/Conversor-Video-Para-ASCII.git
cd Conversor-Video-Para-ASCII
chmod +x install.sh
./install.sh
```

#### Dependencias

- Python 3.10+
- GTK 3.0
- OpenCV
- VTE 2.91
- kitty (terminal recomendado)

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

### Creditos

- **AndreBFarias**: Criador Original
