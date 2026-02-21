# -*- coding: utf-8 -*-
"""
hook-scipy.py - Hook SIMPLIFICADO para SciPy
Versão: 3.24.0

ESTRATÉGIA:
- Usar apenas collect_submodules e collect_dynamic_libs padrão
- Deixar PyInstaller gerenciar os caminhos automaticamente
- Evitar duplicação de binários
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs
)

# =============================================================================
# HIDDEN IMPORTS - Coletar TODOS os submódulos automaticamente
# =============================================================================

hiddenimports = collect_submodules('scipy')

# =============================================================================
# BINARIES - Deixar PyInstaller coletar automaticamente
# =============================================================================

binaries = collect_dynamic_libs('scipy')

# =============================================================================
# DATA FILES - Apenas arquivos de dados, excluindo testes
# =============================================================================

datas = collect_data_files('scipy', include_py_files=False)

# Filtrar testes para reduzir tamanho
datas = [(src, dst) for src, dst in datas
         if 'tests' not in src.lower()
         and 'test_' not in src.lower()]

