@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ==============================================
REM LUNA - Instalacao para Windows
REM ==============================================
REM Execute como Administrador para melhores resultados
REM ==============================================

title Luna - Protocolo de Instalacao

echo.
echo   _    _   _ _   _    _
echo  ^| ^|  ^| ^| ^| ^| \ ^| ^|  / \
echo  ^| ^|  ^| ^| ^| ^|  \^| ^| / _ \
echo  ^| ^|__^| ^|_^| ^| ^|\  ^|/ ___ \
echo  ^|_____\___/^|_^| \_/_/   \_\
echo.
echo ==============================================
echo        LUNA - Protocolo de Instalacao
echo ==============================================
echo.

REM ----------------------------------------------
REM FASE 0: Verificar Python
REM ----------------------------------------------
echo [0/7] Verificando Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Instale Python 3.10+ de: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante instalacao
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER% detectado
echo.

REM ----------------------------------------------
REM FASE 1: Criar VENV Principal
REM ----------------------------------------------
echo [1/7] Criando ambiente virtual principal...

if not exist "venv" (
    python -m venv venv
    echo [OK] venv criado
) else (
    echo [SKIP] venv ja existe
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
echo [OK] pip atualizado
echo.

REM ----------------------------------------------
REM FASE 2: Instalar Dependencias Core
REM ----------------------------------------------
echo [2/7] Instalando dependencias principais...
echo       (Isso pode levar alguns minutos)
echo.

if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [AVISO] Algumas dependencias podem ter falhado
    ) else (
        echo [OK] Dependencias instaladas
    )
) else (
    echo [ERRO] requirements.txt nao encontrado!
    pause
    exit /b 1
)
echo.

REM ----------------------------------------------
REM FASE 3: Criar VENV TTS (Opcional)
REM ----------------------------------------------
echo [3/7] Configurando ambiente TTS (voz)...

if exist "requirements_tts.txt" (
    if not exist "venv_tts" (
        python -m venv venv_tts
        echo [OK] venv_tts criado
    ) else (
        echo [SKIP] venv_tts ja existe
    )

    call venv_tts\Scripts\activate.bat
    python -m pip install --upgrade pip -q

    echo [AVISO] Instalando TTS - pode demorar 5-10 minutos...
    pip install -r requirements_tts.txt

    call venv\Scripts\activate.bat
    echo [OK] TTS configurado
) else (
    echo [SKIP] requirements_tts.txt nao encontrado
)
echo.

REM ----------------------------------------------
REM FASE 4: Criar Estrutura de Pastas
REM ----------------------------------------------
echo [4/7] Criando estrutura de pastas...

if not exist "src\logs" mkdir "src\logs"
if not exist "src\sessions" mkdir "src\sessions"
if not exist "src\temp\audio" mkdir "src\temp\audio"
if not exist "src\data_memory\events" mkdir "src\data_memory\events"
if not exist "src\data_memory\faces" mkdir "src\data_memory\faces"
if not exist "src\data_memory\user" mkdir "src\data_memory\user"
if not exist "logs" mkdir "logs"

echo [OK] Estrutura criada
echo.

REM ----------------------------------------------
REM FASE 5: Configurar .env
REM ----------------------------------------------
echo [5/7] Verificando configuracao...

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [OK] .env criado a partir de .env.example
        echo [IMPORTANTE] Edite .env com suas API keys!
    ) else (
        echo [AVISO] .env.example nao encontrado
    )
) else (
    echo [SKIP] .env ja existe
)
echo.

REM ----------------------------------------------
REM FASE 6: Ollama (Opcional)
REM ----------------------------------------------
echo [6/7] Verificando Ollama (modelos locais)...

where ollama >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama nao instalado
    echo.
    echo Para usar modelos locais, instale Ollama:
    echo https://ollama.ai/download/windows
    echo.
    echo Apos instalar, execute:
    echo   ollama pull dolphin-mistral
    echo   ollama pull moondream
    echo   ollama pull llama3.2:3b
    echo.
) else (
    echo [OK] Ollama detectado
    echo.
    echo Modelos recomendados (execute manualmente):
    echo   ollama pull dolphin-mistral
    echo   ollama pull moondream
    echo   ollama pull llama3.2:3b
)
echo.

REM ----------------------------------------------
REM FASE 7: Verificacao Final
REM ----------------------------------------------
echo [7/7] Verificacao final...
echo.
echo ==============================================
echo              VERIFICACAO
echo ==============================================
echo.

call venv\Scripts\activate.bat

echo Testando imports...
python -c "import textual; print('  [OK] textual')" 2>nul || echo "  [FALTA] textual"
python -c "import rich; print('  [OK] rich')" 2>nul || echo "  [FALTA] rich"
python -c "import numpy; print('  [OK] numpy')" 2>nul || echo "  [FALTA] numpy"
python -c "import pydantic; print('  [OK] pydantic')" 2>nul || echo "  [FALTA] pydantic"

echo.
echo ==============================================
echo       INSTALACAO CONCLUIDA!
echo ==============================================
echo.
echo Como iniciar Luna:
echo.
echo   1. Ative o ambiente:
echo      venv\Scripts\activate
echo.
echo   2. Execute:
echo      python main.py
echo.
echo   Ou use o atalho:
echo      run_luna.bat
echo.

REM Criar atalho run_luna.bat
echo @echo off > run_luna.bat
echo call venv\Scripts\activate.bat >> run_luna.bat
echo python main.py >> run_luna.bat
echo pause >> run_luna.bat

echo [OK] Criado run_luna.bat para inicializacao rapida
echo.

if not exist ".env" (
    echo [IMPORTANTE] Configure GOOGLE_API_KEY no arquivo .env
    echo.
)

echo Pressione qualquer tecla para sair...
pause >nul
