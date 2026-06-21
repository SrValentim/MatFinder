@echo off
REM ============================================================
REM   COMPILACAO OTIMIZADA - MatFinder
REM   Usa o VENV LIMPO dedicado (.venv-build) + build_clean.py
REM   (build + smoke test headless + relatorio de tamanho)
REM ============================================================
echo.

REM Vai para a raiz do projeto (este .bat esta em build_tools\)
cd /d "%~dp0.."

REM Python do venv LIMPO (fica fora da pasta do repo, em MatFinderRefactor\.venv-build)
set "VENVPY=..\.venv-build\Scripts\python.exe"

if not exist "%VENVPY%" (
    echo [ERRO] venv de build nao encontrado em %VENVPY%
    echo.
    echo Crie-o uma vez com ^(Python 3.11^):
    echo   py -3.11 -m venv ..\.venv-build
    echo   ..\.venv-build\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
    echo.
    pause
    exit /b 1
)

echo Compilando com o venv limpo: %VENVPY%
echo.
"%VENVPY%" build_tools\build_clean.py
set RC=%ERRORLEVEL%

echo.
if "%RC%"=="0" (
    echo ============================================================
    echo   SUCESSO! Executavel em: dist\MatFinder\MatFinder.exe
    echo ============================================================
) else (
    echo ============================================================
    echo   FALHOU (codigo %RC%). Veja o relatorio do selftest acima.
    echo ============================================================
)
echo.
pause
exit /b %RC%
