# -*- coding: utf-8 -*-
"""
hook-pymatgen.py - Hook ROBUSTO para Pymatgen
Versão: 3.24.0

ESTRATÉGIA:
- Coletar TODOS os submódulos (mais seguro)
- Coletar TODAS as DLLs e dados
- Filtrar apenas testes
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS - Coletar TODOS os submódulos
# =============================================================================

hiddenimports = collect_submodules('pymatgen')

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('pymatgen')

# =============================================================================
# DATA FILES - CRÍTICO! Contém dados de elementos, grupos espaciais, etc.
# =============================================================================

datas = collect_data_files('pymatgen', include_py_files=False)

# Filtrar apenas testes
datas = [(src, dst) for src, dst in datas
         if 'tests' not in src.lower()
         and 'test_' not in src.lower()]

