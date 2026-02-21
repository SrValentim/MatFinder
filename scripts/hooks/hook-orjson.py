# -*- coding: utf-8 -*-
"""
hook-orjson.py - Hook para orjson
Versão: 3.24.0

orjson é usado pelo pymatgen para serialização JSON rápida.
"""

from PyInstaller.utils.hooks import (
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    'orjson',
]

# =============================================================================
# BINARIES - CRÍTICO! orjson é uma extensão compilada
# =============================================================================

binaries = collect_dynamic_libs('orjson')
