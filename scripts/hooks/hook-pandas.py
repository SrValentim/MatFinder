# hooks/hook-pandas.py
# Hook COMPLETO para Pandas - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar todos os submódulos
hiddenimports = collect_submodules('pandas')

# Coletar bibliotecas dinâmicas (CRÍTICO para pandas._libs)
binaries = collect_dynamic_libs('pandas')

# Dados necessários
datas = collect_data_files('pandas', include_py_files=False)

