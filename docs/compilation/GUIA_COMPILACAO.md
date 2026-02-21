# Guia de Compilação do MatFinder v3.24.0

## Estrutura dos Hooks

Os hooks em `scripts/hooks/` são responsáveis por identificar os módulos necessários de cada biblioteca:

| Hook | Biblioteca | Função |
|------|-----------|--------|
| hook-numpy.py | NumPy 2.x | Core matemático - CRÍTICO |
| hook-scipy.py | SciPy | Processamento de sinais |
| hook-PySide6.py | PySide6 | Interface gráfica (Qt) |
| hook-matplotlib.py | Matplotlib | Gráficos 2D |
| hook-pyqtgraph.py | PyQtGraph | Visualização 3D |
| hook-OpenGL.py | PyOpenGL | Renderização 3D |
| hook-pymatgen.py | Pymatgen | Análise cristalográfica |
| hook-mp_api.py | MP-API | Materials Project |
| hook-emmet.py | Emmet | Modelos de dados |
| hook-monty.py | Monty | I/O e serialização |
| hook-pandas.py | Pandas | Manipulação de dados |
| hook-pydantic.py | Pydantic | Validação de dados |
| hook-spglib.py | Spglib | Simetria cristalográfica |
| hook-orjson.py | orjson | JSON rápido |

## Estratégia de Otimização

### O que é INCLUÍDO:
- Módulos core de cada biblioteca
- DLLs necessárias para funcionamento
- Arquivos de dados (fontes, configurações, etc.)

### O que é EXCLUÍDO:
- Módulos de teste (pytest, unittest)
- Documentação e samples
- Módulos Qt não usados (~300MB de economia):
  - WebEngine
  - Quick/QML
  - Multimedia
  - 3D (usamos pyqtgraph)
  - Bluetooth, NFC, Sensors, etc.

### UPX:
- **DESABILITADO** para DLLs do Qt (causa crashes)
- Pode ser usado em outros arquivos se necessário

## Como Compilar

### Opção 1: Usando o BAT (recomendado)
```batch
cd build_tools
COMPILE.bat
```

### Opção 2: Comando direto
```batch
cd MatFinderRefactor
pyinstaller --clean --noconfirm build_tools\MatFinder.spec
```

## Solução de Problemas

### Erro: "ModuleNotFoundError"
1. Identifique o módulo faltando no erro
2. Adicione ao `hiddenimports` no spec OU
3. Crie/atualize o hook correspondente

### Erro: "DLL load failed"
1. Verifique se a DLL está sendo copiada
2. Adicione ao `binaries` do hook correspondente
3. Verifique se não foi excluída no `excluded_binaries`

### Tamanho muito grande (>700MB)
1. Verifique se os filtros de DLL estão funcionando
2. Confirme que WebEngine não está incluído
3. Execute com `--debug imports` para ver o que está sendo incluído

## Tamanho Esperado

- **Alvo**: 500-600 MB
- **PySide6 otimizado**: ~150MB (vs ~450MB completo)
- **NumPy + SciPy**: ~100MB
- **Matplotlib**: ~50MB
- **Pymatgen + dependências**: ~50MB
- **Outros**: ~100MB
