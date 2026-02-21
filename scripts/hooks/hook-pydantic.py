# -*- coding: utf-8 -*-
"""
hook-pydantic.py - Hook para Pydantic
Versão: 3.24.0

Pydantic é usado pelo mp_api e emmet para validação de dados.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules
)

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    'pydantic',
    'pydantic.main',
    'pydantic.fields',
    'pydantic.validators',
    'pydantic.types',
    'pydantic.dataclasses',
    'pydantic.json',
    'pydantic.error_wrappers',
    'pydantic.errors',
    'pydantic.networks',
    'pydantic.datetime_parse',
    'pydantic.color',
    'pydantic.config',
    'pydantic.schema',
    'pydantic.utils',
    'pydantic.version',

    # Pydantic v2 (se instalado)
    'pydantic_core',
    'pydantic.v1',
]

# Coletar submódulos do pydantic_core se existir
try:
    hiddenimports += collect_submodules('pydantic_core')
except:
    pass

# =============================================================================
# BINARIES - CRÍTICO para pydantic_core (Rust)
# =============================================================================

binaries = collect_dynamic_libs('pydantic')

try:
    binaries += collect_dynamic_libs('pydantic_core')
except:
    pass

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('pydantic', include_py_files=False)
