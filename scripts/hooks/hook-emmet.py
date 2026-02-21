# -*- coding: utf-8 -*-
"""
hook-emmet.py - Hook para emmet-core
Versão: 3.24.0

Emmet é usado pelo mp_api para modelos de dados.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    # Core
    'emmet',
    'emmet.core',
    'emmet.core.utils',
    'emmet.core.symmetry',
    'emmet.core.structure',
    'emmet.core.settings',
    'emmet.core.material',
    'emmet.core.mpid',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('emmet')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('emmet', include_py_files=False)
