# -*- coding: utf-8 -*-
"""
hook-matplotlib.py - Hook OTIMIZADO para Matplotlib
Versão: 3.24.0

ESTRATÉGIA:
- Incluir backend Qt (usado com PySide6)
- Incluir módulos de plotagem usados
- Excluir backends não usados (Tk, Wx, GTK)
- Manter dados de fontes

MÓDULOS MATPLOTLIB USADOS NO MATFINDER:
- backends.backend_qtagg (backend Qt para PySide6)
- pyplot (API principal)
- figure, axes (gráficos)
- patches, lines (elementos gráficos)
- ticker (formatação de eixos)
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs
)
import os

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

hiddenimports = [
    # Backend Qt - CRÍTICO
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_agg',
    'matplotlib.backends.backend_qt',

    # Módulos principais
    'matplotlib.pyplot',
    'matplotlib.figure',
    'matplotlib.axes',
    'matplotlib.axis',

    # Elementos gráficos
    'matplotlib.patches',
    'matplotlib.lines',
    'matplotlib.text',
    'matplotlib.legend',
    'matplotlib.legend_handler',
    'matplotlib.collections',
    'matplotlib.markers',
    'matplotlib.path',
    'matplotlib.transforms',

    # Formatação
    'matplotlib.ticker',
    'matplotlib.scale',
    'matplotlib.dates',
    'matplotlib.colors',
    'matplotlib.colorbar',
    'matplotlib.cm',

    # Widgets interativos
    'matplotlib.widgets',

    # Configuração
    'matplotlib.rcsetup',
    'matplotlib.style',
    'matplotlib.font_manager',
    'matplotlib.mathtext',
    'matplotlib.textpath',

    # Imagens
    'matplotlib.image',

    # Utilitários
    'matplotlib.cbook',
    'matplotlib._api',
    'matplotlib._pylab_helpers',

    # Animação (para visualização 3D)
    'matplotlib.animation',

    # Projeções
    'matplotlib.projections',
    'matplotlib.projections.polar',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('matplotlib')

# =============================================================================
# DATA FILES - Fontes são CRÍTICAS
# =============================================================================

all_datas = collect_data_files('matplotlib', include_py_files=False)

# Filtrar para excluir testes e docs, mas MANTER fontes
datas = []
for src, dst in all_datas:
    # Excluir testes
    if 'tests' in src.lower() or 'test_' in src.lower():
        continue
    # Excluir docs/samples
    if 'sample_data' in src.lower():
        continue
    # Manter todo o resto (especialmente mpl-data com fontes)
    datas.append((src, dst))

