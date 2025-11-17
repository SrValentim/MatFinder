@echo off
echo ============================================================
echo     COMPILACAO DEFINITIVA - MatFinder v3.23.0
echo     Com hooks corrigidos para incluir DLLs
echo ============================================================
echo.

echo [1/3] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo OK!
echo.

echo [2/3] Compilando com PyInstaller (isso pode levar 5-10 minutos)...
python build_optimized.py
echo.

if exist dist\MatFinder\MatFinder.exe (
    echo [3/3] Sucesso! Executavel criado.
    echo.
    echo ============================================================
    echo     COMPILACAO FINALIZADA!
    echo ============================================================
    echo.
    echo Executavel em: dist\MatFinder\MatFinder.exe
    echo.
    echo Para testar:
    echo   cd dist\MatFinder
    echo   MatFinder.exe
    echo.
    echo Para criar instalador MSI:
    echo   cd scripts
    echo   python build_msi.py
    echo.
) else (
    echo [3/3] ERRO! Executavel nao foi criado.
    echo Verifique os logs acima para detalhes.
    echo.
)

pause

