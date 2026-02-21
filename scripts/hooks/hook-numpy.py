# -*- coding: utf-8 -*-
"""
hook-numpy.py - Hook SIMPLIFICADO para NumPy
Versão: 3.24.0

ESTRATÉGIA:
- Usar apenas collect_submodules e collect_dynamic_libs padrão
- Deixar PyInstaller gerenciar os caminhos automaticamente
- Evitar duplicação de binários que causa erro FileNotFound
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS - Coletar TODOS os submódulos automaticamente
# =============================================================================

hiddenimports = collect_submodules('numpy')

# =============================================================================
# BINARIES - Deixar PyInstaller coletar automaticamente
# =============================================================================

binaries = collect_dynamic_libs('numpy')

# =============================================================================
# DATA FILES - Arquivos de dados necessários
# =============================================================================

datas = collect_data_files('numpy', include_py_files=False)

# Filtrar testes para reduzir tamanho
datas = [(src, dst) for src, dst in datas
         if 'tests' not in src.lower()
         and 'test_' not in src.lower()
         and 'conftest' not in src.lower()]
