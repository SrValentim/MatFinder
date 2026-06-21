@echo off
title MatFinder - Instalar requisitos
cd /d "%~dp0"

echo(
echo ============================================================
echo   MatFinder - Instalar requisitos  (rode 1x)
echo   Instala Python 3.11 (se faltar) + dependencias de build
echo ============================================================
echo(

REM ------------------------------------------------------------
REM 1) Python 3.11
REM ------------------------------------------------------------
py -3.11 --version >nul 2>&1
if not errorlevel 1 goto HAVE_PY

echo Python 3.11 nao encontrado. Tentando instalar via winget...
where winget >nul 2>&1
if errorlevel 1 (
  echo(
  echo [ERRO] winget nao esta disponivel neste Windows.
  echo Instale o Python 3.11 ^(64-bit^) manualmente e rode este arquivo de novo:
  echo   https://www.python.org/downloads/release/python-3119/
  echo Na instalacao, marque "Add python.exe to PATH".
  echo(
  pause
  exit /b 1
)

winget install -e --id Python.Python.3.11 --scope user --accept-source-agreements --accept-package-agreements
echo(
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] O Python 3.11 foi instalado mas ainda nao esta visivel nesta janela.
  echo        Feche esta janela, abra de novo e rode INSTALAR_REQUISITOS.bat outra vez.
  echo(
  pause
  exit /b 1
)

:HAVE_PY
echo [OK] Python 3.11 presente.
echo(

REM ------------------------------------------------------------
REM 2) Ambiente de build + dependencias
REM ------------------------------------------------------------
set "VENV=.venv-build"
if exist "..\.venv-build\Scripts\python.exe" set "VENV=..\.venv-build"

if not exist "%VENV%\Scripts\python.exe" (
  echo Criando ambiente em "%VENV%"...
  py -3.11 -m venv "%VENV%"
)

echo Instalando dependencias ^(pode levar ~10 min e precisa de internet^)...
echo(
"%VENV%\Scripts\python" -m pip install -r "build_tools\requirements-build.lock.txt"
if errorlevel 1 (
  echo(
  echo [ERRO] Falha ao instalar as dependencias. Veja as mensagens acima.
  echo(
  pause
  exit /b 1
)

echo(
echo ============================================================
echo   PRONTO!  Agora de duplo clique em  COMPILAR.bat
echo ============================================================
echo(
pause
