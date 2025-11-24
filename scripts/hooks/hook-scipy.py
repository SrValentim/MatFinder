# hooks/hook-scipy.py
# Hook COMPLETO para SciPy - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs
)

# Coletar TODOS os submódulos automaticamente
hiddenimports = collect_submodules('scipy')

# Coletar TODAS as bibliotecas dinâmicas (DLLs críticas)
binaries = collect_dynamic_libs('scipy')

# Coletar todos os arquivos de dados
datas = collect_data_files('scipy', include_py_files=False)

