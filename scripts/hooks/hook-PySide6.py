# hooks/hook-PySide6.py
# Hook COMPLETO para PySide6 - inclui DLLs, binários e submódulos

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# Coletar os módulos PySide6 usados
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtPrintSupport',
]

# Coletar submódulos
hiddenimports += collect_submodules('PySide6.QtCore')
hiddenimports += collect_submodules('PySide6.QtGui')
hiddenimports += collect_submodules('PySide6.QtWidgets')

# Coletar bibliotecas dinâmicas
binaries = collect_dynamic_libs('PySide6')

# Arquivos de dados (plugins, etc.)
datas = collect_data_files('PySide6', include_py_files=False)

