# 🚀 Guia Rápido de Teste - Pixel Art Mode

## ✅ Instalação Completa!

Todas as dependências foram instaladas com sucesso:
- ✓ OpenCV
- ✓ NumPy  
- ✓ Scikit-learn (para k-means clustering)
- ✓ GTK3 (interface gráfica)

## 🧪 Como Testar

### Opção 1: Interface Gráfica (Recomendado)

```bash
cd /home/vitoriamaria/Desenvolvimento/Conversor-Video-Para-ASCII
source venv/bin/activate
python3 main.py
```

**Passos na GUI:**
1. Clique em **"Configurações"** (botão com ícone de engrenagem)
2. No topo da janela, selecione **"Pixel Art"**
3. Configure (opcional):
   - **Tamanho do Pixel**: 2-8 para efeito moderado
   - **Tamanho da Paleta**: 16 cores (estilo retro) ou 32+ (mais gradiente)
   - **☑ Paleta Fixa**: Marque para usar paleta de cores fixas (jogos antigos)
4. Clique **"OK"** para salvar
5. Selecione um vídeo ou imagem
6. Clique **"Converter Selecionado"**
7. Clique **"Reproduzir"** para ver o resultado no terminal

### Opção 2: Linha de Comando (Testes Rápidos)

#### Converter vídeo para Pixel Art:
```bash
source venv/bin/activate
python3 src/core/pixel_art_converter.py \
  --video videos_entrada/SEU_VIDEO.mp4 \
  --config config.ini
```

#### Converter imagem para Pixel Art:
```bash
python3 src/core/pixel_art_image_converter.py \
  --image videos_entrada/SUA_IMAGEM.png \
  --config config.ini
```

## 🎨 Teste Comparativo

Para ver a diferença entre ASCII e Pixel Art com o mesmo vídeo:

1. **Modo ASCII** (padrão):
   - Abra configurações → selecione "ASCII Art" → OK
   - Converta um vídeo → salva como `video.txt`
   - Reproduza e observe os caracteres variados

2. **Modo Pixel Art**:
   - Abra configurações → selecione "Pixel Art" → OK
   - Converta o MESMO vídeo → sobrescreve `video.txt`
   - Reproduza e observe os blocos coloridos pixelados

## 📁 Arquivos de Saída

Outputs são salvos em: `/home/vitoriamaria/Desenvolvimento/Conversor-Video-Para-ASCII/videos_saida/`

Formato: `nome_do_video.txt` ou `nome_da_imagem.txt`

## 🐛 Solução de Problemas

### Erro: "No module named 'sklearn'"
```bash
source venv/bin/activate
pip install scikit-learn
```

### Erro: "Não foi possível carregar o arquivo de interface"
Certifique-se de executar de dentro do diretório do projeto.

### GUI não abre
Verifique dependências GTK:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

## 💡 Dicas de Teste

1. **Comece com parâmetros pequenos** para testes rápidos:
   - Tamanho do pixel: 4
   - Paleta: 8 cores
   - Vídeo curto (5-10 segundos)

2. **Experimente diferentes configurações**:
   - Pixel pequeno (2) + paleta grande (32) = Mais detalhado
   - Pixel grande (8) + paleta pequena (8) = Mais retro/pixelado

3. **Teste diferentes mídias**:
   - Vídeo com cores vibrantes
   - Imagem estática
   - Vídeo com chroma key (fundo verde)

## 📊 Configuração Atual

Seu `config.ini` está configurado com:
- **Modo**: ASCII (padrão)
- **Pixel Size**: 2
- **Palette Size**: 16
- **Fixed Palette**: false (paleta adaptativa)

Você pode mudar isso pela GUI ou editando `config.ini` diretamente.

---

**Pronto para testar! 🎉** 

Qualquer problema, verifique o `walkthrough.md` no diretório de artifacts para mais detalhes técnicos.
