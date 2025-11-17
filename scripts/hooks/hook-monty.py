# hooks/hook-monty.py
# Hook COMPLETO para Monty - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar todos os submódulos
hiddenimports = collect_submodules('monty')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('monty')

# Dados necessários
datas = collect_data_files('monty', include_py_files=False)

