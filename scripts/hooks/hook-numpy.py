# hooks/hook-numpy.py
# Hook COMPLETO para NumPy 2.x - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs,
    get_package_paths
)

# Coletar TODOS os submódulos automaticamente
hiddenimports = collect_submodules('numpy')

# Coletar TODAS as bibliotecas dinâmicas (DLLs, PYDs, SOs)
# ISSO É CRÍTICO - sem isso, _multiarray_umath.pyd não é incluído
binaries = collect_dynamic_libs('numpy')

# Coletar TODOS os arquivos de dados
datas = collect_data_files('numpy', include_py_files=False)

