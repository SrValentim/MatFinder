@echo off
title MatFinder - Compilar
REM Este .bat fica em build_tools\; tudo roda a partir da raiz do projeto.
cd /d "%~dp0.."

echo(
echo ============================================================
echo   MatFinder - Compilar  (clique e compile)
echo ============================================================
echo(

REM Ambiente de build: .venv-build na raiz do projeto (ou ..\.venv-build, fora dela)
set "VENV=.venv-build"
if exist "..\.venv-build\Scripts\python.exe" set "VENV=..\.venv-build"

if not exist "%VENV%\Scripts\python.exe" (
  echo [ERRO] Ambiente de build nao encontrado.
  echo        Rode primeiro:  build_tools\INSTALAR_REQUISITOS.bat
  echo(
  pause
  exit /b 1
)

REM Confere que as dependencias estao instaladas
"%VENV%\Scripts\python" -c "import PyInstaller, PySide6, pymatgen" >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Dependencias ausentes ou incompletas no ambiente de build.
  echo        Rode:  build_tools\INSTALAR_REQUISITOS.bat
  echo(
  pause
  exit /b 1
)

echo Compilando...  ^(rebuild limpo, se precisar:  build_tools\COMPILAR.bat --clean^)
echo(
"%VENV%\Scripts\python" "build_tools\build_clean.py" %*
set "RC=%ERRORLEVEL%"

echo(
if "%RC%"=="0" (
  echo ============================================================
  echo   SUCESSO!  -^>  dist\MatFinder\MatFinder.exe
  echo ============================================================
) else (
  echo ============================================================
  echo   FALHOU ^(codigo %RC%^). Veja as mensagens acima.
  echo ============================================================
)
echo(
pause
exit /b %RC%
