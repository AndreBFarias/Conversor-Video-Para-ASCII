Extase em 4R73 - Documentação
==============================

Conversor de vídeo para ASCII art em tempo real com aceleração GPU.

.. image:: ../../assets/logo.png
   :width: 200
   :align: center
   :alt: Logo Extase em 4R73

----

**Características Principais:**

- Conversão em tempo real (30-60 FPS com GPU)
- Chroma key avançado (remoção de fundo verde)
- Unicode Braille (resolução 4x)
- Temporal coherence (anti-flicker)
- Gravação de MP4/TXT
- Suporte webcam
- Interface GTK3 moderna

**Modos de Conversão:**

- ASCII Art clássico com múltiplas rampas de luminância
- Pixel Art com paletas customizáveis (Game Boy, CGA, NES, PICO-8, Dracula, etc.)
- Matrix Rain com sistema de partículas GPU

**Efeitos Pós-Processamento (PostFX):**

- Bloom (brilho neon com Gaussian blur)
- Chromatic Aberration (RGB shift cyberpunk)
- Scanlines CRT (efeito monitor antigo)
- Glitch effect (distorção aleatória)

.. toctree::
   :maxdepth: 2
   :caption: Guia do Usuário

   installation
   quickstart
   user_guide/interface
   user_guide/calibration
   user_guide/conversion
   user_guide/advanced

.. toctree::
   :maxdepth: 2
   :caption: Referência da API

   api/converter
   api/gpu
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Informações Adicionais

   faq
   troubleshooting
   contributing
   changelog

Índices e Tabelas
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
