# -*- coding: utf-8 -*-
"""
hook-spglib.py - Hook para spglib
Versão: 3.24.0

spglib é usado pelo pymatgen para análise de simetria cristalográfica.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    'spglib',
    'spglib.spglib',
]

# =============================================================================
# BINARIES - CRÍTICO! spglib tem extensões C
# =============================================================================

binaries = collect_dynamic_libs('spglib')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('spglib', include_py_files=False)
