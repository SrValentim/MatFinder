# -*- coding: utf-8 -*-
"""
hook-mp_api.py - Hook para Materials Project API
Versão: 3.24.0

mp_api é usado para buscar dados do Materials Project.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    # Core
    'mp_api',
    'mp_api.client',
    'mp_api.client.core',
    'mp_api.client.core.client',

    # Routes usadas
    'mp_api.client.routes',
    'mp_api.client.routes.materials',
    'mp_api.client.routes.materials.summary',

    # Modelos
    'mp_api.client.core.utils',
    'mp_api.client.mprester',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('mp_api')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('mp_api', include_py_files=False)
