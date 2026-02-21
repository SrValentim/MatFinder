# -*- coding: utf-8 -*-
"""
hook-pyqtgraph.py - Hook para PyQtGraph (visualização 3D)
Versão: 3.24.0

PyQtGraph é usado para o visualizador 3D de estruturas cristalinas.
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
    'pyqtgraph',
    'pyqtgraph.Qt',
    'pyqtgraph.Qt.QtCore',
    'pyqtgraph.Qt.QtGui',
    'pyqtgraph.Qt.QtWidgets',

    # OpenGL - CRÍTICO para visualização 3D
    'pyqtgraph.opengl',
    'pyqtgraph.opengl.GLViewWidget',
    'pyqtgraph.opengl.GLGraphicsItem',
    'pyqtgraph.opengl.MeshData',

    # Items OpenGL
    'pyqtgraph.opengl.items',
    'pyqtgraph.opengl.items.GLMeshItem',
    'pyqtgraph.opengl.items.GLLinePlotItem',
    'pyqtgraph.opengl.items.GLScatterPlotItem',
    'pyqtgraph.opengl.items.GLGridItem',
    'pyqtgraph.opengl.items.GLAxisItem',
    'pyqtgraph.opengl.items.GLBoxItem',

    # Shaders
    'pyqtgraph.opengl.shaders',

    # Gráficos 2D (caso use)
    'pyqtgraph.graphicsItems',
    'pyqtgraph.graphicsItems.PlotItem',
    'pyqtgraph.graphicsItems.ViewBox',
    'pyqtgraph.graphicsItems.AxisItem',

    # Widgets
    'pyqtgraph.widgets',

    # Funções auxiliares
    'pyqtgraph.functions',
    'pyqtgraph.colormap',
    'pyqtgraph.Vector',
    'pyqtgraph.Transform3D',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('pyqtgraph')

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('pyqtgraph', include_py_files=False)
