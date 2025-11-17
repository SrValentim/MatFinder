# hooks/hook-emmet.py
# Hook COMPLETO para emmet-core - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar TODOS os submódulos
hiddenimports = collect_submodules('emmet')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('emmet')

# Coletar todos os dados
datas = collect_data_files('emmet', include_py_files=False)
