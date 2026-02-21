# -*- coding: utf-8 -*-
"""
hook-OpenGL.py - Hook para PyOpenGL
Versão: 3.24.0

PyOpenGL é usado pelo pyqtgraph para renderização 3D.
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
    # Core OpenGL
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'OpenGL.GLUT',

    # Plataformas
    'OpenGL.platform',
    'OpenGL.platform.win32',

    # Arrays
    'OpenGL.arrays',
    'OpenGL.arrays.ctypesarrays',
    'OpenGL.arrays.ctypesparameters',
    'OpenGL.arrays.ctypespointers',
    'OpenGL.arrays.numpymodule',
    'OpenGL.arrays.lists',
    'OpenGL.arrays.numbers',
    'OpenGL.arrays.strings',
    'OpenGL.arrays.arraydatatype',

    # Convergters
    'OpenGL.converters',

    # Raw bindings
    'OpenGL.raw',
    'OpenGL.raw.GL',
    'OpenGL.raw.GL.VERSION',
    'OpenGL.raw.GL.VERSION.GL_1_0',
    'OpenGL.raw.GL.VERSION.GL_1_1',
    'OpenGL.raw.GL.VERSION.GL_2_0',
    'OpenGL.raw.GL.VERSION.GL_3_0',

    # Error handling
    'OpenGL.error',

    # Accelerate (se disponível)
    'OpenGL_accelerate',
]

# =============================================================================
# BINARIES
# =============================================================================

binaries = collect_dynamic_libs('OpenGL')

# Tentar coletar OpenGL_accelerate também
try:
    binaries += collect_dynamic_libs('OpenGL_accelerate')
except:
    pass

# =============================================================================
# DATA FILES
# =============================================================================

datas = collect_data_files('OpenGL', include_py_files=False)
