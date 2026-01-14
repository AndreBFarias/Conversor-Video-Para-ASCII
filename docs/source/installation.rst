Instalação
===========

Via Pacote .deb (Ubuntu/Debian)
--------------------------------

Método recomendado para Ubuntu 20.04+, Debian 11+, Pop!_OS 22.04+.

.. code-block:: bash

   # Baixar release mais recente
   wget https://github.com/usuario/Conversor-Video-Para-ASCII/releases/latest/download/extase-em-4r73_1.0.0_amd64.deb

   # Instalar
   sudo dpkg -i extase-em-4r73_1.0.0_amd64.deb
   sudo apt-get install -f  # Instalar dependências

   # Executar
   extase-em-4r73

O aplicativo também estará disponível no menu de aplicativos como "Extase em 4R73".

Via Script Manual
-----------------

Para desenvolvimento ou distribuições não-Debian.

.. code-block:: bash

   git clone https://github.com/usuario/Conversor-Video-Para-ASCII.git
   cd Conversor-Video-Para-ASCII
   chmod +x install.sh
   ./install.sh

   # Ativar ambiente virtual
   source venv/bin/activate

   # Executar
   python3 main.py

Requisitos
----------

Obrigatórios
^^^^^^^^^^^^

- Python 3.10 ou superior
- GTK 3.0
- NumPy
- OpenCV (python3-opencv)
- FFmpeg

Recomendados (para GPU)
^^^^^^^^^^^^^^^^^^^^^^^

- GPU NVIDIA (RTX 2000+ series)
- CUDA 11.0 ou superior
- CuPy (instalado automaticamente via pip)

Opcionais
^^^^^^^^^

- kitty terminal (melhor suporte a Unicode)
- gnome-terminal (alternativa)

Verificar Instalação
---------------------

.. code-block:: bash

   # Verificar GPU CUDA
   nvidia-smi

   # Verificar CuPy
   python3 -c "import cupy; print(cupy.__version__)"

   # Testar aplicação
   extase-em-4r73 --version  # (se instalou .deb)
   python3 main.py            # (se instalou manual)

Troubleshooting
---------------

Erro: "Gtk not found"
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

Erro: "cv2 not found"
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   sudo apt install python3-opencv
   # ou
   pip install opencv-python

Erro: "CUDA not found"
^^^^^^^^^^^^^^^^^^^^^^

GPU não é obrigatória. O aplicativo funcionará em modo CPU (mais lento).

Para ativar GPU:

.. code-block:: bash

   # Instalar CUDA Toolkit
   sudo apt install nvidia-cuda-toolkit

   # Instalar CuPy
   pip install cupy-cuda11x  # ou cupy-cuda12x, conforme sua versão CUDA
