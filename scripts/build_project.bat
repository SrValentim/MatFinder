@echo off
REM build_project.bat
REM Script para automatizar a compilação do MatFinder com cx_Freeze e a criação do instalador MSI.
REM Otimizado para execução a partir de um terminal como o do PyCharm.

REM --- INÍCIO DA CONFIGURAÇÃO ---
REM Nome do seu ambiente virtual. Mude para o nome da sua pasta.
SET VENV_NAME=pysides

REM Script de configuração do cx_Freeze.
SET SETUP_SCRIPT=setup.py
REM --- FIM DA CONFIGURAÇÃO ---


REM --- Lógica do Script ---

echo.
echo [PASSO 1 de 5] Verificando o ambiente virtual...
REM Verifica se o ambiente virtual existe.
IF NOT EXIST "%VENV_NAME%\Scripts\activate.bat" (
    echo.
    echo ERRO: Ambiente virtual '%VENV_NAME%' nao encontrado.
    echo Por favor, crie o ambiente virtual e instale as dependencias primeiro:
    echo   python -m venv %VENV_NAME%
    echo   call .\%VENV_NAME%\Scripts\activate
    echo   pip install -r requirements.txt
    goto:eof
)

echo.
echo [PASSO 2 de 5] Ativando ambiente virtual: %VENV_NAME%
call .\%VENV_NAME%\Scripts\activate

REM Verifica se cx_Freeze está instalado
python -c "import cx_Freeze" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: cx_Freeze nao esta instalado no ambiente virtual.
    echo Por favor, execute: pip install cx_freeze
    goto:eof
)
echo Ambiente virtual ativado e cx_Freeze encontrado.

echo.
echo [PASSO 3 de 5] Limpando compilacoes anteriores (pastas build e dist)...
IF EXIST build (
    rmdir /s /q build
)
IF EXIST dist (
    rmdir /s /q dist
)
echo Pastas limpas.

echo.
echo [PASSO 4 de 5] Executando cx_Freeze para compilar o projeto...
echo Isto pode demorar alguns minutos...
echo.

python %SETUP_SCRIPT% build

REM Verifica se a compilação com cx_Freeze foi bem-sucedida.
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ***********************************************
    echo *** ERRO: A compilacao com cx_Freeze falhou. ***
    echo ***********************************************
    goto:eof
)

echo.
echo --- Compilacao com cx_Freeze concluida com sucesso! ---
echo.
echo [PASSO 5 de 5] Executando script para criar o instalador MSI...

python build_msi.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ****************************************************
    echo *** ERRO: A criacao do instalador MSI falhou. ***
    echo ****************************************************
    goto:eof
)

echo.
echo.
echo =========================================================
echo === Processo de compilacao concluido com sucesso! ===
echo =========================================================
echo.
echo O instalador se encontra na pasta 'dist'.
echo.

:eof
