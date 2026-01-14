Perguntas Frequentes (FAQ)
===========================

Geral
-----

O que é Extase em 4R73?
^^^^^^^^^^^^^^^^^^^^^^^^

Conversor de vídeo para ASCII art em tempo real com aceleração GPU (CUDA), chroma key avançado e modos especiais como Unicode Braille.

É gratuito?
^^^^^^^^^^^

Sim, 100% open source sob licença GPLv3.

Performance
-----------

Qual é o FPS esperado?
^^^^^^^^^^^^^^^^^^^^^^^

Depende do hardware:

- **CPU:** 1-5 FPS (resolução média)
- **GPU RTX 3050:** 30-60 FPS (resolução média-alta)
- **GPU RTX 4090:** 120+ FPS (resolução muito alta)

Preciso de GPU NVIDIA?
^^^^^^^^^^^^^^^^^^^^^^^

Não. O aplicativo funciona em modo CPU, mas será mais lento. GPU é altamente recomendada para conversão em tempo real.

GPU
---

Como ativo a aceleração GPU?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Instale CUDA Toolkit: ``sudo apt install nvidia-cuda-toolkit``
2. Instale CuPy: ``pip install cupy-cuda11x``
3. No aplicativo: Opções → GPU → Ativar

Erro "CUDA out of memory"
^^^^^^^^^^^^^^^^^^^^^^^^^^

Reduza a resolução:

- Diminua largura/altura
- Use preset "Medium" ou "Low"
- Feche outros aplicativos que usam GPU

Formatos
--------

Quais formatos de entrada são suportados?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Vídeo: .mp4, .avi, .mkv, .mov, .webm, .gif
- Imagem: .png, .jpg, .jpeg, .bmp, .webp

Quais formatos de saída?
^^^^^^^^^^^^^^^^^^^^^^^^^

- **.txt:** Frames ASCII com cores ANSI (padrão)
- **.mp4:** Vídeo renderizado com caracteres
- **.gif:** Animação ASCII
- **.html:** Página web interativa

Chroma Key
----------

O que é chroma key?
^^^^^^^^^^^^^^^^^^^

Técnica para remover fundo verde/azul de vídeos, como em efeitos especiais de cinema.

Como calibrar chroma key?
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Clique "Calibrar Chroma Key"
2. Ajuste sliders H/S/V até o fundo verde desaparecer
3. Use "Erode" e "Dilate" para refinar bordas
4. Clique "Salvar"

Features Avançadas
------------------

O que é Unicode Braille?
^^^^^^^^^^^^^^^^^^^^^^^^^

Modo que usa caracteres Braille para aumentar resolução em 4x sem perder performance. Cada caractere representa 2×4 pixels.

Ativação: Opções → GPU → Braille

O que é Temporal Coherence?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sistema anti-flicker que estabiliza caracteres oscilantes entre frames. Ideal para webcam estática.

Ativação: Opções → GPU → Anti-Flicker

O que é High Fidelity mode?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modo que compara textura (MSE) ao invés de apenas luminância, resultando em qualidade visual superior. Mais lento que o modo fast.

Ativação: Opções → GPU → Render Mode: High Fidelity

Troubleshooting
---------------

Aplicativo não inicia
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Verificar instalação
   which extase-em-4r73

   # Verificar logs
   cat ~/.local/share/extase-em-4r73/logs/app.log

Preview em branco
^^^^^^^^^^^^^^^^^

1. Verifique se vídeo foi selecionado
2. Verifique formato suportado
3. Teste com outro vídeo

Conversão trava
^^^^^^^^^^^^^^^

1. Verifique logs em ``logs/``
2. Reduza resolução
3. Desative GPU se houver erro CUDA
4. Reporte bug: https://github.com/usuario/Conversor-Video-Para-ASCII/issues

Contribuir
----------

Como posso contribuir?
^^^^^^^^^^^^^^^^^^^^^^

Veja :doc:`contributing` para detalhes sobre como contribuir com código, documentação ou reportar bugs.
