# -*- mode: python ; coding: utf-8 -*-
"""
MatFinder.spec - Arquivo de configuração OTIMIZADO para PyInstaller
Versão: 3.24.0
Autor: Raynner Valentim - UFAM

Este arquivo configura a compilação do MatFinder com:
- Modo onedir (mais rápido que onefile)
- Hooks customizados para reduzir tamanho (~500-600MB alvo)
- Exclusão agressiva de módulos não usados
- Filtragem de DLLs pesadas do Qt

IMPORTANTE:
- NÃO usar UPX em DLLs do Qt (causa crashes)
- Os hooks em scripts/hooks/ são carregados automaticamente
- Execute da RAIZ do projeto: pyinstaller build_tools/MatFinder.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Caminho base do projeto - detecta automaticamente
# Se executado da raiz do projeto, usa o diretório atual
# Se executado de build_tools, sobe um nível
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
if os.path.basename(spec_dir) == 'build_tools':
    base_path = os.path.dirname(spec_dir)
else:
    base_path = spec_dir

# Garante que estamos no diretório correto
if not os.path.exists(os.path.join(base_path, 'run_matfinder.py')):
    # Tenta o diretório atual
    base_path = os.getcwd()
    if not os.path.exists(os.path.join(base_path, 'run_matfinder.py')):
        raise FileNotFoundError(
            f"run_matfinder.py não encontrado! Execute o PyInstaller da raiz do projeto MatFinderRefactor.\n"
            f"Diretório atual: {os.getcwd()}\n"
            f"Diretório do spec: {spec_dir}"
        )

print(f"[SPEC] Base path: {base_path}")

# =============================================================================
# ARQUIVOS DE DADOS DO PROJETO
# =============================================================================

added_files = [
    # Assets do MatFinder
    (os.path.join(base_path, 'matfinder', 'assets', 'icons'), os.path.join('matfinder', 'assets', 'icons')),
    (os.path.join(base_path, 'matfinder', 'assets', 'logos'), os.path.join('matfinder', 'assets', 'logos')),
    (os.path.join(base_path, 'matfinder', 'assets', 'config'), os.path.join('matfinder', 'assets', 'config')),
    (os.path.join(base_path, 'matfinder', 'assets', 'translations'), os.path.join('matfinder', 'assets', 'translations')),

    # Licença
    (os.path.join(base_path, 'licenses', 'LICENSE_FULL.txt'), '.'),

    # VERSION file
    (os.path.join(base_path, 'VERSION'), '.'),
]

# =============================================================================
# HIDDEN IMPORTS - Módulos que DEVEM ser incluídos
# Os hooks já cuidam da maioria, mas alguns precisam ser explícitos
# =============================================================================

hidden_imports = [
    # =========================================================================
    # NumPy 2.x - Módulos críticos
    # NOTA: Os hooks cuidam da maioria, aqui só os essenciais
    # =========================================================================
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'numpy.linalg',
    'numpy.fft',
    'numpy.random',
    'numpy.ma',
    'numpy.lib',
    'numpy.polynomial',

    # =========================================================================
    # SciPy - Módulos usados para processamento de sinais
    # =========================================================================
    'scipy._lib',
    'scipy._lib.messagestream',
    'scipy._lib._ccallback',
    'scipy.signal',
    'scipy.signal._savitzky_golay',
    'scipy.signal._peak_finding',
    'scipy.ndimage',
    'scipy.sparse',
    'scipy.sparse.linalg',
    'scipy.linalg',
    'scipy.special',
    'scipy.special._ufuncs',
    'scipy.special.cython_special',
    'scipy.interpolate',
    'scipy.optimize',

    # =========================================================================
    # PySide6 - Interface gráfica
    # =========================================================================
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtPrintSupport',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'shiboken6',
    'shiboken6.Shiboken',

    # =========================================================================
    # Matplotlib - Gráficos
    # =========================================================================
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'matplotlib.backends.backend_qt',
    'matplotlib.pyplot',
    'matplotlib.figure',
    'matplotlib.axes',
    'matplotlib.ticker',
    'matplotlib.patches',
    'matplotlib.lines',
    'matplotlib.legend',
    'matplotlib.widgets',
    'matplotlib.font_manager',
    'matplotlib.colors',
    'matplotlib.cm',

    # =========================================================================
    # PyQtGraph + OpenGL - Visualização 3D
    # =========================================================================
    'pyqtgraph',
    'pyqtgraph.Qt',
    'pyqtgraph.opengl',
    'pyqtgraph.opengl.GLViewWidget',
    'pyqtgraph.opengl.items.GLMeshItem',
    'pyqtgraph.opengl.items.GLLinePlotItem',
    'pyqtgraph.opengl.items.GLScatterPlotItem',
    'pyqtgraph.opengl.items.GLGridItem',
    'pyqtgraph.opengl.MeshData',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'OpenGL.arrays',
    'OpenGL.arrays.numpymodule',
    'OpenGL.platform',
    'OpenGL.platform.win32',

    # =========================================================================
    # Pymatgen - Análise cristalográfica
    # =========================================================================
    'pymatgen.core',
    'pymatgen.core.composition',
    'pymatgen.core.lattice',
    'pymatgen.core.periodic_table',
    'pymatgen.core.structure',
    'pymatgen.core.sites',
    'pymatgen.core.bonds',
    'pymatgen.io',
    'pymatgen.io.cif',
    'pymatgen.symmetry',
    'pymatgen.symmetry.analyzer',
    'pymatgen.symmetry.groups',
    'pymatgen.analysis',
    'pymatgen.analysis.diffraction',
    'pymatgen.analysis.diffraction.xrd',
    'pymatgen.analysis.diffraction.core',
    'pymatgen.analysis.local_env',
    'pymatgen.transformations',
    'pymatgen.util',

    # =========================================================================
    # Materials Project API
    # =========================================================================
    'mp_api',
    'mp_api.client',
    'mp_api.client.core',
    'mp_api.client.core.client',
    'mp_api.client.routes',
    'mp_api.client.routes.materials',
    'mp_api.client.routes.materials.summary',

    # =========================================================================
    # Dependências do Pymatgen/MP-API
    # =========================================================================
    'emmet.core',
    'emmet.core.utils',
    'emmet.core.symmetry',
    'monty',
    'monty.io',
    'monty.json',
    'monty.serialization',
    'spglib',
    'orjson',

    # =========================================================================
    # Pydantic - Validação de dados
    # =========================================================================
    'pydantic',
    'pydantic.main',
    'pydantic.fields',
    'pydantic_core',

    # =========================================================================
    # Pandas - Manipulação de dados
    # =========================================================================
    'pandas',
    'pandas._libs',
    'pandas._libs.lib',
    'pandas._libs.tslibs',
    'pandas._libs.algos',
    'pandas._libs.hashtable',
    'pandas.core',
    'pandas.core.frame',
    'pandas.io',

    # =========================================================================
    # Outros módulos necessários
    # =========================================================================
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'json',
    'logging',
    'pkg_resources',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
]

# =============================================================================
# MÓDULOS A EXCLUIR - Reduz drasticamente o tamanho!
# =============================================================================

excluded_modules = [
    # =========================================================================
    # Módulos de teste/desenvolvimento
    # =========================================================================
    'pytest',
    'pytest_cov',
    'unittest',
    'nose',
    'test',
    'tests',
    '_pytest',
    'IPython',
    'jupyter',
    'jupyter_client',
    'jupyter_core',
    'notebook',
    'nbformat',
    'nbconvert',
    'sphinx',
    'docutils',

    # =========================================================================
    # GUIs não usadas
    # =========================================================================
    'tkinter',
    '_tkinter',
    'Tkinter',
    'wx',
    'wxPython',
    'PyQt4',
    'PyQt5',
    'PyQt6',

    # =========================================================================
    # PySide6 - Módulos PESADOS não usados (~300MB economia!)
    # =========================================================================
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'PySide6.QtWebSockets',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DExtras',
    'PySide6.QtQuick',
    'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickWidgets',
    'PySide6.QtQml',
    'PySide6.QtQmlModels',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtLocation',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtSerialBus',
    'PySide6.QtBluetooth',
    'PySide6.QtDBus',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtNfc',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml',
    'PySide6.QtSql',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools',
    'PySide6.QtXml',
    'PySide6.QtConcurrent',
    'PySide6.QtDataVisualization',
    'PySide6.QtCharts',
    'PySide6.QtStateMachine',
    'PySide6.QtVirtualKeyboard',
    'PySide6.QtLanguageServer',

    # =========================================================================
    # Matplotlib - módulos não usados
    # =========================================================================
    'matplotlib.tests',
    'matplotlib.testing',
    'matplotlib.sphinxext',
    'mpl_toolkits.mplot3d',  # Usamos pyqtgraph para 3D

    # =========================================================================
    # Outros módulos grandes não usados
    # =========================================================================
    'PIL.ImageQt',  # Conflita com PySide
    'cv2',
    'tensorflow',
    'torch',
    'keras',
    'sklearn',
    'scikit-learn',
]

# =============================================================================
# ANÁLISE
# =============================================================================

a = Analysis(
    [os.path.join(base_path, 'run_matfinder.py')],
    pathex=[base_path],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[os.path.join(base_path, 'scripts', 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# =============================================================================
# FILTRAGEM DE BINÁRIOS - Remove DLLs pesadas não usadas
# =============================================================================

# DLLs do PySide6/Qt que devem ser EXCLUÍDAS (economia de ~300MB!)
excluded_binaries = [
    # WebEngine - ENORME (~150MB sozinho)
    'Qt6WebEngineCore',
    'Qt6WebEngine',
    'QtWebEngine',

    # Quick/QML - não usado
    'Qt6Quick',
    'Qt6Qml',
    'Qt6QmlModels',
    'Qt6QmlCore',
    'Qt6QmlWorkerScript',
    'Qt6QuickControls2',
    'Qt6QuickLayouts',
    'Qt6QuickParticles',
    'Qt6QuickShapes',
    'Qt6QuickTemplates2',
    'Qt6QuickWidgets',
    'QtQuick',
    'QtQml',

    # Multimedia - não usado
    'Qt6Multimedia',
    'Qt6MultimediaWidgets',
    'QtMultimedia',
    'avcodec',
    'avformat',
    'avutil',
    'swresample',
    'swscale',

    # 3D Qt (usamos pyqtgraph)
    'Qt63DCore',
    'Qt63DRender',
    'Qt63DInput',
    'Qt63DLogic',
    'Qt63DAnimation',
    'Qt63DExtras',
    'Qt3D',

    # PDF
    'Qt6Pdf',
    'Qt6PdfWidgets',

    # Outros
    'Qt6WebChannel',
    'Qt6WebSockets',
    'Qt6Bluetooth',
    'Qt6Designer',
    'Qt6Help',
    'Qt6Location',
    'Qt6Nfc',
    'Qt6Positioning',
    'Qt6RemoteObjects',
    'Qt6Scxml',
    'Qt6Sensors',
    'Qt6SerialPort',
    'Qt6SerialBus',
    'Qt6Sql',
    'Qt6Test',
    'Qt6TextToSpeech',
    'Qt6VirtualKeyboard',
    'Qt6Charts',
    'Qt6DataVisualization',
    'Qt6StateMachine',
    'Qt6LanguageServer',
]

# Aplicar filtro de binários
a.binaries = [
    (name, path, type_)
    for name, path, type_ in a.binaries
    if not any(excl in name for excl in excluded_binaries)
]

# =============================================================================
# EMPACOTAMENTO
# =============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MatFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # DESABILITADO - UPX causa crashes em DLLs do Qt!
    console=False,  # Aplicação GUI sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_path, 'matfinder', 'assets', 'icons', 'polvo.ico'),
    version_file=None,
)

# =============================================================================
# COLEÇÃO FINAL
# =============================================================================

# Lista de arquivos que NÃO devem ser comprimidos com UPX
# (DLLs do Qt falham quando comprimidas)
upx_exclude_list = [
    'Qt*.dll',
    'PySide6*.dll',
    'shiboken*.dll',
    'python*.dll',
    'vcruntime*.dll',
    'msvcp*.dll',
    'ucrtbase.dll',
    'api-ms-*.dll',
]

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Desabilitado globalmente para estabilidade
    upx_exclude=upx_exclude_list,
    name='MatFinder',
)

