@echo off
title MatFinder - Compilar do zero
cd /d "%~dp0"

echo(
echo ============================================================
echo   MatFinder - Compilacao otimizada (resultado ~426 MB)
echo ============================================================
echo(

REM --- 1) Verifica Python 3.11 ---
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python 3.11 nao encontrado no sistema.
  echo(
  echo Baixe o Python 3.11 ^(64-bit^) em:
  echo   https://www.python.org/downloads/release/python-3119/
  echo Na instalacao marque "Add python.exe to PATH". Depois rode este arquivo de novo.
  echo(
  pause
  exit /b 1
)
echo [1/3] Python 3.11 encontrado.

REM --- 2) Ambiente de build (reusa ..\.venv-build se existir; senao cria .venv-build aqui) ---
set "VENV=.venv-build"
if exist "..\.venv-build\Scripts\python.exe" set "VENV=..\.venv-build"

if not exist "%VENV%\Scripts\python.exe" (
  echo [2/3] Criando ambiente em "%VENV%" e instalando dependencias...
  echo       ^(So na 1a vez; pode levar ~10 minutos e precisa de internet.^)
  py -3.11 -m venv "%VENV%"
  "%VENV%\Scripts\python" -m pip install -r "build_tools\requirements-build.lock.txt"
  if errorlevel 1 (
    echo(
    echo [ERRO] Falha ao instalar as dependencias. Veja as mensagens acima.
    pause
    exit /b 1
  )
) else (
  echo [2/3] Ambiente de build encontrado em "%VENV%".
)

REM --- 3) Compila + auto-teste headless + tamanho ---
echo [3/3] Compilando...
echo(
"%VENV%\Scripts\python" "build_tools\build_clean.py"
set "RC=%ERRORLEVEL%"

echo(
if "%RC%"=="0" (
  echo ============================================================
  echo   SUCESSO!  -^>  dist\MatFinder\MatFinder.exe
  echo ============================================================
) else (
  echo ============================================================
  echo   FALHOU ^(codigo %RC%^). Veja o relatorio do --selftest acima.
  echo ============================================================
)
echo(
pause
exit /b %RC%
