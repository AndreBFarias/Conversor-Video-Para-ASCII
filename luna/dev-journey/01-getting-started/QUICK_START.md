# Quick Start - Luna

**Data:** 2025-12-18
**Status:** Estavel

---

## TL;DR

Instale e execute Luna em 3 comandos:

```bash
git clone https://github.com/AndreBFarias/Luna.git
cd Luna && chmod +x install.sh && ./install.sh
./run_luna.sh
```

---

## Contexto

Luna e uma assistente IA com interface TUI construida em Python. Ela possui capacidades multimodais: conversacao via texto, voz (STT/TTS), visao computacional e reconhecimento facial.

Este documento cobre apenas o minimo necessario para rodar Luna pela primeira vez.

---

## Conteudo

### Pre-requisitos Minimos

**Sistema Operacional:**
- Linux (testado em Pop!_OS/Ubuntu)
- Windows (parcial, requer WSL para alguns recursos)
- macOS (parcial)

**Software:**
- Python 3.10+
- pip
- venv
- portaudio (para audio input)
- ffmpeg (para processamento de audio)

**Hardware:**
- Webcam (opcional, para visao)
- Microfone (opcional, para voz)
- GPU NVIDIA com CUDA (opcional, melhora desempenho de Whisper e TTS)

**API Keys:**
- Google Gemini API (obrigatorio)
- ElevenLabs API (opcional, se usar TTS ElevenLabs)

### Instalacao

1. Clone o repositorio:
```bash
git clone https://github.com/AndreBFarias/Luna.git
cd Luna
```

2. Configure as variaveis de ambiente:
```bash
cp .env.example .env
nano .env
```

Preencha no minimo:
```
GOOGLE_API_KEY=sua_chave_aqui
```

3. Execute o instalador automatizado:
```bash
chmod +x install.sh
./install.sh
```

O script `install.sh` cria as venvs necessarias, instala dependencias (incluindo face_recognition que requer dlib) e prepara o ambiente.

### Primeiro Uso

Execute Luna:
```bash
./run_luna.sh
```

Na primeira execucao, Luna executara um onboarding interativo onde:
1. Apresenta-se e explica suas capacidades
2. Pede seu nome
3. Testa a chamada de voz (se disponivel)
4. Mostra como interagir

Para pular o onboarding:
```bash
python main.py --skip-onboarding
```

### Controles Basicos

**Teclado:**
- Digite no campo de texto e pressione Enter
- ESC: Sair

**Botoes:**
- Nova Conversa: Inicia nova sessao
- Ver Historico: Carrega conversas anteriores
- Editar Alma: Abre arquivo de personalidade
- Ver: Captura imagem da webcam
- Voz: Ativa/desativa modo de chamada de voz
- +: Anexa arquivo ou diretorio
- Sair: Encerra aplicacao

**Voz:**
- Ative o botao "Voz"
- Fale normalmente
- Luna detecta quando voce para de falar (VAD)
- Desative o botao para voltar ao modo texto

---

## Links Relacionados

- [ARCHITECTURE.md](ARCHITECTURE.md) - Diagrama da arquitetura interna
- [TECH_STACK.md](TECH_STACK.md) - Tecnologias utilizadas
- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Estrutura de diretorios
- `/home/andrefarias/Desenvolvimento/Luna/README.md` - Visao geral do projeto
- `/home/andrefarias/Desenvolvimento/Luna/.env.example` - Template de configuracao
