# hooks/hook-pymatgen.py
# Hook COMPLETO para Pymatgen - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar TODOS os submódulos
hiddenimports = collect_submodules('pymatgen')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('pymatgen')

# Coletar TODOS os arquivos de dados
datas = collect_data_files('pymatgen', include_py_files=False)
