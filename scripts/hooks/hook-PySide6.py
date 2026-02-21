# -*- coding: utf-8 -*-
"""
hook-PySide6.py - Hook OTIMIZADO para PySide6
Versão: 3.24.0

ESTRATÉGIA:
- Incluir APENAS módulos usados (QtCore, QtGui, QtWidgets, QtNetwork, QtPrintSupport, QtOpenGL)
- EXCLUIR módulos pesados (WebEngine ~200MB, Multimedia, Quick/Qml)
- Filtrar DLLs para não incluir as não usadas

MÓDULOS PYSIDE6 USADOS NO MATFINDER:
- QtCore (base)
- QtGui (interface gráfica)
- QtWidgets (widgets)
- QtNetwork (requisições API)
- QtPrintSupport (impressão de gráficos)
- QtOpenGL (visualização 3D de estruturas)
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs
)
import os

# =============================================================================
# HIDDEN IMPORTS - APENAS o que é usado
# =============================================================================

hiddenimports = [
    # Core
    'PySide6.QtCore',

    # GUI
    'PySide6.QtGui',

    # Widgets
    'PySide6.QtWidgets',

    # Network (para APIs)
    'PySide6.QtNetwork',

    # PrintSupport (para salvar gráficos)
    'PySide6.QtPrintSupport',

    # OpenGL (para visualização 3D)
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',

    # Shiboken (bindings)
    'shiboken6',
    'shiboken6.Shiboken',
]

# =============================================================================
# BINARIES - DLLs necessárias (filtradas)
# =============================================================================

# Coletar todas as DLLs
all_binaries = collect_dynamic_libs('PySide6')

# DLLs a EXCLUIR (economiza ~300MB!)
excluded_dlls = [
    # WebEngine - ENORME, não usado
    'Qt6WebEngine',
    'Qt6WebEngineCore',
    'Qt6WebEngineWidgets',
    'Qt6WebChannel',
    'Qt6WebSockets',
    'QtWebEngine',

    # Quick/QML - não usado
    'Qt6Quick',
    'Qt6Qml',
    'Qt6QmlModels',
    'Qt6QmlCore',
    'Qt6QmlLocalStorage',
    'Qt6QmlWorkerScript',
    'Qt6QuickControls2',
    'Qt6QuickLayouts',
    'Qt6QuickParticles',
    'Qt6QuickShapes',
    'Qt6QuickTemplates2',
    'Qt6QuickWidgets',

    # Multimedia - não usado
    'Qt6Multimedia',
    'Qt6MultimediaWidgets',
    'avcodec',
    'avformat',
    'avutil',
    'swresample',
    'swscale',

    # 3D avançado - não usado
    'Qt63DCore',
    'Qt63DRender',
    'Qt63DInput',
    'Qt63DLogic',
    'Qt63DAnimation',
    'Qt63DExtras',

    # Outros não usados
    'Qt6Bluetooth',
    'Qt6Concurrent',
    'Qt6DataVisualization',
    'Qt6Charts',
    'Qt6Designer',
    'Qt6Help',
    'Qt6Location',
    'Qt6Nfc',
    'Qt6Pdf',
    'Qt6Positioning',
    'Qt6RemoteObjects',
    'Qt6Scxml',
    'Qt6Sensors',
    'Qt6SerialPort',
    'Qt6Sql',
    'Qt6StateMachine',
    'Qt6Test',
    'Qt6TextToSpeech',
    'Qt6UiTools',
    'Qt6Xml',
    'Qt6VirtualKeyboard',
    'Qt6LanguageServer',
]

# Filtrar binários
binaries = []
for src, dst in all_binaries:
    filename = os.path.basename(src)
    if not any(excl in filename for excl in excluded_dlls):
        binaries.append((src, dst))

# =============================================================================
# DATA FILES - Plugins necessários
# =============================================================================

all_datas = collect_data_files('PySide6', include_py_files=False)

# Filtrar para incluir apenas plugins essenciais
essential_plugins = [
    'platforms',      # CRÍTICO - sem isso não inicia
    'styles',         # Estilos visuais
    'imageformats',   # PNG, JPG, etc.
    'iconengines',    # Ícones SVG
]

datas = []
for src, dst in all_datas:
    # Incluir sempre arquivos na raiz
    if 'plugins' not in dst.lower():
        datas.append((src, dst))
    else:
        # Para plugins, incluir apenas os essenciais
        if any(plugin in src.lower() for plugin in essential_plugins):
            datas.append((src, dst))

