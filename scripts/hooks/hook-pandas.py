# -*- coding: utf-8 -*-
"""
hook-pandas.py - Hook OTIMIZADO para Pandas
Versão: 3.24.0

Pandas é usado para manipulação de dados (tabelas de resultados).
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS - Apenas módulos usados
# =============================================================================

hiddenimports = [
    # Core
    'pandas',
    'pandas.core',
    'pandas.core.api',
    'pandas.core.frame',
    'pandas.core.series',
    'pandas.core.arrays',
    'pandas.core.dtypes',
    'pandas.core.indexes',

    # Bibliotecas compiladas - CRÍTICO
    'pandas._libs',
    'pandas._libs.lib',
    'pandas._libs.tslibs',
    'pandas._libs.tslibs.dtypes',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.timestamps',
    'pandas._libs.tslibs.timezones',
    'pandas._libs.tslibs.tzconversion',
    'pandas._libs.tslibs.offsets',
    'pandas._libs.tslibs.parsing',
    'pandas._libs.tslibs.period',
    'pandas._libs.algos',
    'pandas._libs.hashtable',
    'pandas._libs.internals',
    'pandas._libs.indexing',
    'pandas._libs.index',
    'pandas._libs.arrays',
    'pandas._libs.join',
    'pandas._libs.missing',
    'pandas._libs.ops',
    'pandas._libs.parsers',
    'pandas._libs.properties',
    'pandas._libs.reshape',
    'pandas._libs.sparse',
    'pandas._libs.writers',

    # IO - para ler/escrever arquivos
    'pandas.io',
    'pandas.io.formats',
    'pandas.io.common',

    # Compat
    'pandas.compat',
    'pandas.compat.numpy',

    # API
    'pandas.api',
    'pandas.api.types',
]

# =============================================================================
# BINARIES - CRÍTICO
# =============================================================================

binaries = collect_dynamic_libs('pandas')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('pandas', include_py_files=False)

# Filtrar testes
datas = [(src, dst) for src, dst in datas
         if 'tests' not in src.lower()
         and 'test_' not in src.lower()]

