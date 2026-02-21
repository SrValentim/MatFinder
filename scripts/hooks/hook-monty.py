# -*- coding: utf-8 -*-
"""
hook-monty.py - Hook para Monty
Versão: 3.24.0

Monty é usado pelo pymatgen para I/O e serialização.
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
    'monty',
    'monty.io',
    'monty.json',
    'monty.serialization',
    'monty.functools',
    'monty.itertools',
    'monty.string',
    'monty.re',
    'monty.os',
    'monty.os.path',
    'monty.collections',
    'monty.dev',
    'monty.termcolor',
    'monty.tempfile',
    'monty.shutil',
    'monty.subprocess',
    'monty.multiprocessing',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('monty')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('monty', include_py_files=False)

