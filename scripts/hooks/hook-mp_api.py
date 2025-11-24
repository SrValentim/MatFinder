# hooks/hook-mp_api.py
# Hook COMPLETO para mp-api - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar TODOS os submódulos
hiddenimports = collect_submodules('mp_api')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('mp_api')

# Coletar todos os dados
datas = collect_data_files('mp_api', include_py_files=False)
