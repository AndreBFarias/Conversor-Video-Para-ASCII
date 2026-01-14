# Instalação e Desinstalação - Extase em 4R73

## Pré-requisitos

### Sistema Operacional
- Pop!_OS / Ubuntu 22.04+
- Git instalado
- Permissões sudo (para instalação de pacotes do sistema)

### Hardware (Recomendado)
- GPU NVIDIA com suporte a CUDA 12.x (opcional, mas recomendado para GPU Converter)
- Mínimo: 4GB RAM, 500MB disco

## Instalação Rápida

```bash
cd /caminho/para/Conversor-Video-Para-ASCII
chmod +x install.sh
./install.sh
```

O script automaticamente:
1. Atualiza repositórios apt
2. Instala dependências do sistema (GTK, OpenCV, etc)
3. Cria ambiente virtual Python (venv)
4. Instala pacotes Python (numpy, opencv, Pillow, scikit-learn, cupy)
5. Cria diretórios de trabalho (data_input, data_output, .cache, logs)
6. Registra aplicação no menu GNOME
7. Configura ícone da aplicação

## Instalação com GPU (NVIDIA)

**Pré-requisito:** NVIDIA Driver + CUDA 12.x instalados

```bash
# nvidia-smi deve funcionar
nvidia-smi

# Executar instalação normal
./install.sh
```

O script detectará GPU automaticamente e tentará instalar cupy-cuda12x.

**Se cupy falhar:**
```bash
source venv/bin/activate
pip install cupy-cuda12x
```

## Início Manual (sem Menu GNOME)

```bash
cd /caminho/para/Conversor-Video-Para-ASCII
source venv/bin/activate
python3 main.py
```

## Desinstalação

```bash
cd /caminho/para/Conversor-Video-Para-ASCII
chmod +x uninstall.sh
./uninstall.sh
```

Isto remove:
- Ambiente virtual (venv)
- Ícone e launcher GNOME
- Cache Python (__pycache__)
- Atlas GPU (.cache/)
- Logs
- Arquivos temporários

**NÃO remove:**
- Dependências do sistema (GTK, OpenCV)
- Diretórios data_input/data_output (dados do usuário)
- config.ini (configurações salvas)

## Estrutura de Diretórios

Após instalação:
```
Conversor-Video-Para-ASCII/
├── venv/                    # Ambiente Python isolado
├── .cache/                  # Atlas Braille (gerado automaticamente)
├── logs/                    # Logs de execução
├── data_input/              # Vídeos/imagens para converter
├── data_output/             # Saída (vídeos ASCII, frames, etc)
├── src/                     # Código-fonte
├── config.ini               # Configurações (editável)
└── main.py                  # Entry point
```

## Configuração

**config.ini** - Editar manualmente ou via Interface Gráfica

Principais seções:
- `[Conversor]`: Braille, Temporal Coherence, Resolução
- `[ChromaKey]`: Chroma Key HSV
- `[PixelArt]`: Configurações Pixel Art
- `[Geral]`: Modo display, velocidade, etc

## Troubleshooting

### cupy não instala
```bash
# Verificar CUDA
nvidia-smi

# Tentar instalação manual
source venv/bin/activate
pip install cupy-cuda12x --no-cache-dir

# Se ainda falhar, desativar GPU no config.ini:
# gpu_enabled = false
```

### Erro "cannot open video"
- Verificar se vídeo existe em data_input/
- Verificar permissões do arquivo
- Testar com ffmpeg: `ffmpeg -i video.mp4 -f null -`

### Interface GTK não funciona
```bash
# Reinstalar dependências GTK
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 --reinstall
```

### .cache crescendo muito
Atlas Braille (256 padrões) ocupa ~50MB. Limpar:
```bash
rm -rf .cache/
# Será regenerado automaticamente
```

## Atualizações

Para atualizar para nova versão:

```bash
# Puxar mudanças
git pull origin dev

# Reinstalar dependências (em caso de novos pacotes)
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Pronto!
```

## Performance

**CPU Mode:** ~240s para vídeo 30s @ 1080p30fps
**GPU Fast:** ~13s
**GPU High Fidelity:** ~32s
**GPU Braille:** ~13-15s (4x resolução)

Tempos estimados variam com hardware.
