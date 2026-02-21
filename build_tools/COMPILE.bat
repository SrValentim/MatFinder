@echo off
echo ============================================================
echo     COMPILACAO OTIMIZADA - MatFinder v3.24.0
echo     Hooks otimizados para ~500-600MB
echo ============================================================
echo.

echo [1/4] Limpando builds anteriores...
cd ..
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo OK!
echo.

echo [2/4] Verificando dependencias...
python -c "import pyinstaller; print('PyInstaller OK')" 2>nul || (
    echo PyInstaller nao encontrado! Instalando...
    pip install pyinstaller
)
echo.

echo [3/4] Compilando com PyInstaller (isso pode levar 5-10 minutos)...
echo       Logs detalhados serao exibidos abaixo:
echo.
pyinstaller --clean --noconfirm build_tools\MatFinder.spec
echo.

if exist dist\MatFinder\MatFinder.exe (
    echo [4/4] Sucesso! Executavel criado.
    echo.

    REM Calcular tamanho da pasta
    for /f "tokens=3" %%a in ('dir dist\MatFinder /s ^| findstr "arquivo(s)"') do set SIZE=%%a

    echo ============================================================
    echo     COMPILACAO FINALIZADA COM SUCESSO!
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
    echo [4/4] ERRO! Executavel nao foi criado.
    echo.
    echo Possiveis causas:
    echo   1. Modulo faltando - verifique os logs acima
    echo   2. Erro de sintaxe no spec file
    echo   3. DLL faltando
    echo.
    echo Dica: Execute novamente com --debug para mais detalhes:
    echo   pyinstaller --debug all build_tools\MatFinder.spec
    echo.
)

pause

