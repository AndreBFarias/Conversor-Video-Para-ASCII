<div align="center">
  
[![opensource](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](#)
[![Licença](https://img.shields.io/badge/licença-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Estrelas](https://img.shields.io/github/stars/AndreBFarias/ArteAsciiConversor.svg?style=social)](https://github.com/AndreBFarias/ArteAsciiConversor/stargazers)
[![Contribuições](https://img.shields.io/badge/contribuições-bem--vindas-brightgreen.svg)](https://github.com/AndreBFarias/ArteAsciiConversor/issues)

<div align="center">
<div style="text-align: center;">
  <h1 style="font-size: 2em;">Êxtase em Arte ASCII: Conversor de Vídeos para TXT</h1>
  <img src="assets/logo.png" width="200" alt="Logo">
</div>
</div></div>

### Funcionalidades da Interface

O grimório principal é invocado com `python3 main.py`, abrindo o Altar de Transmutação (GUI).



> #### `main.py`: O Altar Principal
> ![Main](src/assets/main.png)

A partir daqui, os seguintes rituais estão disponíveis:

1.  **Seleção (Arquivo ou Pasta):**
    * **Selecionar Arquivo:** Marca um único vídeo para sacrifício.
    * **Selecionar Pasta:** Marca um diretório inteiro. Todos os vídeos `.mp4`, `.mkv`, etc., dentro dele serão processados.

2.  **A Transmutação (Conversão):**
    * **Converter Selecionado:** Inicia a conversão apenas do arquivo selecionado.
    * **Converter Pasta Inteira:** Inicia um ritual em lote, convertendo todos os vídeos da pasta selecionada (ou da `input_dir` padrão). O processo utiliza todos os núcleos da sua máquina para banir o *chroma key* e selar a essência do vídeo em arquivos `.txt`.

> #### `main_cli.py` / `player.py`: O Projetor de Sombras
> ![Player](src/assets/player.png)

3.  **A Projeção (Playback):**
    * **Reproduzir (no Terminal):** Invoca um novo terminal e projeta a arte ASCII (`.txt`) correspondente ao vídeo selecionado.

> #### `calibrator.py`: O Triptych (O Oráculo)
> ![Calibrator](src/assets/calibrator.png)

4.  **A Calibração (O Triptych):**
    * **Calibrar Chroma Key:** O ritual mais complexo. Abre três portais simultâneos:
        * **Janela 1 (Vídeo):** A realidade crua (sua webcam ou vídeo).
        * **Janela 2 (Vídeo):** O resultado do filtro chroma key.
        * **Janela 3 (Terminal):** A transmutação ASCII *em tempo real* do resultado.
    * Use os controles deslizantes para ajustar o filtro e pressione `s` para selar (salvar) os valores no `config.ini`.

5.  **Abertura de Portais (Utilitários):**
    * **Abrir Vídeo Original:** Abre o arquivo de vídeo selecionado no seu player padrão.
    * **Abrir Pasta de Saída:** Abre o diretório `output_dir` onde os arquivos `.txt` repousam.
    
### Instalação
- Clone o repositório: 
  > git clone [https://github.com/AndreBFarias/Extase-em-Arte-ASCII](https://github.com/AndreBFarias/Extase-em-Arte-ASCII) 
- Instale dependências: 
  > pip install -r requirements.txt.
- Crie pastas: mkdir videos_entrada videos_saida.
- Edite config.ini pra caminhos e defaults do player
- Converta todos vídeos da pasta entrada: 
  > python3 main.py.
- Calibre chroma key: 
  > python3 calibrator.py [--video nome.mp4]
- Projete um TXT: 
  > python3 player.py --arquivo videos_saida/seu_video.txt 
- Projete todos TXT da saída em sequência: 
  >python3 player.py 

### Configuração (config.ini)
```
[Pastas]
-input_dir = videos_entrada
-output_dir = videos_saida

[Player]
-arquivo = videos_saida/Luna_feliz.txt
-loop = sim
-all = nao
```
### Dependências
```-opencv-python
-numpy
-configparser
```

### Licença GLP
>Livre para modificar e usar da forma que preferir desde que tudo permaneça livre.
