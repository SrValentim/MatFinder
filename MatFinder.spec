# -*- mode: python ; coding: utf-8 -*-
"""
MatFinder.spec - Arquivo de configuração otimizado para PyInstaller
Versão: 3.23.0
Autor: Raynner Valentim - UFAM

Este arquivo configura a compilação do MatFinder com:
- Modo onedir (mais rápido que onefile)
- Hooks customizados para reduzir tamanho
- Exclusão de módulos desnecessários
- Otimizações de performance
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Caminho base do projeto
base_path = os.path.abspath('.')

# Coletar dados do projeto
matfinder_datas = [
    ('matfinder/assets', 'matfinder/assets'),
]

# Arquivos adicionais (ícones, logos, etc.)
added_files = [
    ('matfinder/assets/icons/polvo.ico', 'matfinder/assets/icons'),
    ('matfinder/assets/logos/*', 'matfinder/assets/logos'),
    ('matfinder/assets/config/*', 'matfinder/assets/config'),
    ('LICENSE_FULL.txt', '.'),
]

# Hidden imports - módulos que precisam ser incluídos explicitamente
hidden_imports = [
    # NumPy 2.x - CRÍTICO para evitar erros de importação
    'numpy._core',
    'numpy._core._multiarray_umath',
    'numpy._core._multiarray_tests',
    'numpy._core._exceptions',
    'numpy._core._type_aliases',
    'numpy._core._internal',
    'numpy._core._methods',
    'numpy._core.multiarray',
    'numpy._core.numeric',
    'numpy._core.umath',
    'numpy.core._multiarray_umath',
    'numpy.linalg._umath_linalg',
    'numpy.linalg.linalg',
    'numpy.fft',
    'numpy.random',
    'numpy.random._common',
    'numpy.random._generator',
    'numpy.ma',
    'numpy.lib',

    # SciPy essenciais
    'scipy.special.cython_special',
    'scipy.special._ufuncs',
    'scipy.special._ufuncs_cxx',
    'scipy.ndimage',
    'scipy.signal',
    'scipy.sparse',
    'scipy.sparse.linalg',
    'scipy.linalg',
    'scipy._lib',
    'scipy._lib.messagestream',
    'scipy._lib._ccallback',

    # PySide6
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtPrintSupport',

    # Matplotlib backends
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_agg',
    'matplotlib.ticker',
    'matplotlib.patches',
    'matplotlib.lines',
    'matplotlib.legend',

    # Pymatgen essenciais
    'pymatgen.core',
    'pymatgen.core.periodic_table',
    'pymatgen.core.structure',
    'pymatgen.core.lattice',
    'pymatgen.io',
    'pymatgen.io.cif',
    'pymatgen.symmetry',
    'pymatgen.symmetry.analyzer',
    'pymatgen.analysis',
    'pymatgen.analysis.diffraction',
    'pymatgen.analysis.diffraction.xrd',
    'pymatgen.analysis.diffraction.core',
    'pymatgen.util',
    'pymatgen.electronic_structure',

    # MP API
    'mp_api',
    'mp_api.client',
    'mp_api.client.core',
    'mp_api.client.core.client',
    'mp_api.client.routes',
    'mp_api.client.routes.materials',

    # Emmet
    'emmet.core',
    'emmet.core.utils',
    'emmet.core.symmetry',
    'emmet.core.structure',

    # Monty (usado pelo Pymatgen)
    'monty',
    'monty.io',
    'monty.json',
    'monty.serialization',

    # Pandas
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas._libs.algos',
    'pandas._libs.hashtable',
    'pandas._libs.lib',

    # Outros
    'pkg_resources.py2_warn',
]

# Módulos a EXCLUIR (reduz drasticamente o tamanho)
excluded_modules = [
    # Módulos de teste
    'pytest',
    'unittest',
    'test',
    'tests',

    # Módulos de desenvolvimento
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',

    # Bibliotecas não usadas
    'tkinter',
    'wx',
    'PyQt4',
    'PyQt5',

    # PySide6 - módulos não usados (ECONOMIZA ~200MB!)
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DInput',
    'PySide6.QtQuick',
    'PySide6.QtQml',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtLocation',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtBluetooth',
    'PySide6.QtDBus',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtNfc',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml',
    'PySide6.QtSql',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',
    'PySide6.QtConcurrent',
    'PySide6.QtDataVisualization',
    'PySide6.QtCharts',
    'PySide6.QtStateMachine',

    # Módulos grandes do SciPy não usados (comentados para evitar problemas de dependência)
    # 'scipy.stats',
    # 'scipy.optimize',
    # 'scipy.integrate',
    # 'scipy.interpolate',
    # 'scipy.spatial',

    # Módulos grandes do Matplotlib não usados
    'matplotlib.tests',
    'matplotlib.sphinxext',

    # Outros módulos grandes (comentados para segurança)
    # 'pandas.tests',
    # 'numpy.tests',
    # 'pymatgen.tests',
]

a = Analysis(
    ['run_matfinder.py'],
    pathex=[base_path],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=['scripts/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filtrar binários para excluir DLLs desnecessárias do PySide6
# Isso economiza ~200MB removendo Qt6WebEngineCore.dll e outros
excluded_binaries = [
    'Qt6WebEngineCore',
    'Qt6WebEngine',
    'Qt6Quick',
    'Qt6Qml',
    'Qt6QmlModels',
    'Qt6WebChannel',
    'Qt6Multimedia',
    'avcodec',
    'avformat',
    'avutil',
    'swresample',
    'swscale',
]

a.binaries = [x for x in a.binaries if not any(excl in x[0] for excl in excluded_binaries)]

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
    upx=True,  # Compressão UPX para reduzir tamanho
    console=False,  # Sem console (aplicação GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='matfinder/assets/icons/polvo.ico',
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MatFinder',
)

