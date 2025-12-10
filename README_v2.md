# 🎮 Êxtase em 4R73 v2.0 - Agora com Pixel Art!

Este README documenta as novidades da versão 2.0 do conversor.

## 🆕 O Que Mudou (v2.0)

### ✨ Nova Feature: Modo Pixel Art
Agora você pode escolher entre dois modos de conversão:
- **ASCII Art** (original) - Caracteres variados com detecção de bordas
- **Pixel Art** (novo) - Blocos coloridos pixelados estilo retro

### 🐛 Bugs Corrigidos
- Padronização das chaves de configuração `luminance_ramp`
- Correção de erro de digitação no calibrador

## 🚀 Instalação Rápida

```bash
cd Conversor-Video-Para-ASCII
chmod +x install.sh
./install.sh
```

**OU** se já instalou antes, apenas atualize as dependências:

```bash
source venv/bin/activate
pip install scikit-learn
```

## 🎯 Como Usar

### Iniciar Aplicativo
```bash
python3 main.py
```

### Selecionar Modo Pixel Art
1. Clique em **"Configurações"**
2. Selecione **"Pixel Art"**
3. Configure parâmetros (opcional):
   - Tamanho do Pixel: 2-8
   - Tamanho da Paleta: 8-32 cores
4. **OK** para salvar

### Converter
- Selecione vídeo/imagem
- Clique "Converter Selecionado"
- Clique "Reproduzir" para ver o resultado

## 📖 Documentação Completa

- `TESTE_RAPIDO.md` - Guia de teste rápido
- `walkthrough.md` - Documentação técnica completa (em artifacts/)
- `implementation_plan.md` - Plano de implementação (em artifacts/)

## 🔧 Arquivos Importantes

### Novos Arquivos
- `src/core/pixel_art_converter.py` - Conversor de vídeo Pixel Art
- `src/core/pixel_art_image_converter.py` - Conversor de imagem Pixel Art
- `test_installation.sh` - Script de teste de instalação

### Arquivos Modificados
- `config.ini` - Novas seções [Mode] e [PixelArt]
- `src/main.py` - Suporte a seleção de modo
- `requirements.txt` - Adicionado scikit-learn

## 🎨 Diferenças Visuais

| ASCII Art | Pixel Art |
|-----------|-----------|
| Caracteres variados | Blocos sólidos █ |
| Detecção de bordas (Sobel) | Sem bordas |
| Cores graduais | Paleta reduzida |
| Terminal art clássico | Estilo jogos 8-bit |

## 💡 Dicas

**Para efeito retro máximo:**
- Pixel size: 8
- Palette size: 8
- ✓ Paleta fixa

**Para mais detalhes:**
- Pixel size: 2
- Palette size: 32
- ✗ Paleta adaptativa

## 🧪 Testar Instalação

```bash
./test_installation.sh
```

Este script verifica se todas as dependências estão instaladas corretamente.

## 📋 Requisitos

- Python 3.8+
- GTK 3.0
- OpenCV
- NumPy
- Scikit-learn (novo!)

## 🤝 Compatibilidade

✅ 100% compatível com arquivos ASCII existentes
✅ Player funciona com ambos os formatos
✅ Chroma key funciona em ambos os modos

## 📝 Notas da Versão

**v2.0** (2025-12-08)
- ✨ Adicionado modo Pixel Art com quantização de cores k-means
- 🐛 Corrigidos bugs de configuração
- 📦 Adicionada dependência scikit-learn
- 🎨 Interface atualizada com seleção de modo
- 📚 Documentação expandida

**v1.0** (anterior)
- Conversão ASCII original
- Chroma key
- Calibrador real-time
- Player com cores ANSI

---

Para documentação técnica completa, veja `walkthrough.md` no diretório de artifacts.
