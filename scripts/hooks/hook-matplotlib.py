# hooks/hook-matplotlib.py
# Hook COMPLETO para Matplotlib - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar todos os submódulos
hiddenimports = collect_submodules('matplotlib')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('matplotlib')

# Arquivos de dados necessários (fontes, configurações)
datas = collect_data_files('matplotlib', include_py_files=False)

