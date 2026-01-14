Início Rápido
=============

Este guia mostra como converter seu primeiro vídeo para ASCII art em menos de 5 minutos.

Passo 1: Abrir o Aplicativo
----------------------------

.. code-block:: bash

   extase-em-4r73  # Se instalou via .deb
   # ou
   python3 main.py  # Se instalou manualmente

A interface principal será exibida.

Passo 2: Selecionar Vídeo
--------------------------

1. Clique em **"Selecionar Arquivo"** ou **"Selecionar Pasta"**
2. Navegue até seu vídeo (suporta: .mp4, .avi, .mkv, .mov, .webm)
3. O vídeo será carregado e exibido na lista

Passo 3: Configurar Qualidade
------------------------------

No painel lateral direito:

- **Preset:** Escolha qualidade (Mobile / Low / Medium / High / Very High)
- **Largura/Altura:** Ajustado automaticamente pelo preset
- **Aspect Ratio:** Proporção dos caracteres (padrão: 0.48)

Recomendação inicial: **Medium** (180x45)

Passo 4: Converter
-------------------

1. Clique no botão **"Converter"**
2. Acompanhe o progresso na barra
3. Vídeo convertido será salvo em ``data_output/``

Formato padrão: arquivo ``.txt`` com frames ASCII + códigos de cor ANSI.

Passo 5: Reproduzir
--------------------

Clique em **"Reproduzir"** para ver o resultado em:

- **Terminal externo** (kitty/gnome-terminal) - Recomendado
- **Janela interna** (player GTK)

Atalhos Durante Reprodução
---------------------------

- **Space:** Pausar/Continuar
- **Q:** Sair
- **Setas:** Avançar/Retroceder frames

Próximos Passos
---------------

- :doc:`user_guide/calibration` - Configurar chroma key (fundo verde)
- :doc:`user_guide/conversion` - Formatos de saída (MP4, GIF, HTML)
- :doc:`user_guide/advanced` - Features avançadas (GPU, Braille, High Fidelity)

Exemplo Completo
----------------

.. code-block:: bash

   # Converter vídeo com chroma key
   1. Abrir aplicativo
   2. Clicar "Calibrar Chroma Key"
   3. Ajustar sliders HSV até fundo verde ficar transparente
   4. Clicar "Salvar"
   5. Selecionar vídeo
   6. Converter
   7. Reproduzir

Resultado: Vídeo ASCII sem fundo verde!
