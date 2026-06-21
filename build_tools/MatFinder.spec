# -*- mode: python ; coding: utf-8 -*-
"""
MatFinder.spec - Configuração OTIMIZADA para PyInstaller (v2)
Autor: Raynner Valentim - UFAM

ESTRATÉGIA (resolve o "loop infinito de módulo faltando" + o tamanho de 1,5GB):

  1) Compilar a partir de um VENV LIMPO e dedicado (build_tools/requirements-build.txt),
     SEM jupyter/jax/opencv/PyQt5/boto3/... O PyInstaller não empacota o que não está
     instalado. É a maior parte da otimização de tamanho.

  2) collect_all() / collect_submodules() para os pacotes de IMPORT DINÂMICO/LAZY
     (pymatgen, mp_api, emmet, monty, chempy, spglib, pyqtgraph, cloudscraper, ...).
     Pega TODOS os submódulos + arquivos de dados + binários de uma vez, em vez de
     listar módulo por módulo (que é o que causava o whack-a-mole).

  3) collect_submodules('matfinder') garante que TODO o código próprio entre,
     mesmo os módulos carregados sob demanda.

  4) Filtro de DLLs do Qt remove WebEngine/Quick/Multimedia/3D/Charts (PySide6_Addons),
     que sozinhos são ~300MB.

IMPORTANTE:
  - NÃO usar UPX em DLLs do Qt (causa crashes).
  - PyInstaller 6.x: NÃO existe mais 'cipher'/'block_cipher' (removidos).
  - Rode da RAIZ do projeto com o python do venv limpo:
      .venv-build\\Scripts\\pyinstaller --clean --noconfirm build_tools\\MatFinder.spec
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# -----------------------------------------------------------------------------
# Caminho base do projeto (raiz onde está run_matfinder.py)
# -----------------------------------------------------------------------------
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
if os.path.basename(spec_dir) == 'build_tools':
    base_path = os.path.dirname(spec_dir)
else:
    base_path = spec_dir

if not os.path.exists(os.path.join(base_path, 'run_matfinder.py')):
    base_path = os.getcwd()
    if not os.path.exists(os.path.join(base_path, 'run_matfinder.py')):
        raise FileNotFoundError(
            "run_matfinder.py não encontrado! Rode o PyInstaller da raiz do projeto.\n"
            f"Diretório atual: {os.getcwd()}\nDiretório do spec: {spec_dir}"
        )

print(f"[SPEC] Base path: {base_path}")

# -----------------------------------------------------------------------------
# Arquivos de dados do PRÓPRIO projeto (assets, licença, versão)
# -----------------------------------------------------------------------------
datas = [
    (os.path.join(base_path, 'matfinder', 'assets', 'icons'), os.path.join('matfinder', 'assets', 'icons')),
    (os.path.join(base_path, 'matfinder', 'assets', 'logos'), os.path.join('matfinder', 'assets', 'logos')),
    # NÃO empacotar 'assets/config': continha a MP_API_KEY (config.txt) e o
    # language.json com de_DE. A chave agora fica em pasta gravável do usuário.
    (os.path.join(base_path, 'matfinder', 'assets', 'translations'), os.path.join('matfinder', 'assets', 'translations')),
    (os.path.join(base_path, 'licenses', 'LICENSE_FULL.txt'), '.'),
    (os.path.join(base_path, 'VERSION'), '.'),
]
binaries = []

# Inclui TODO o código próprio (módulos carregados sob demanda inclusos).
hiddenimports = collect_submodules('matfinder')

# -----------------------------------------------------------------------------
# Coleta COMPLETA dos pacotes de import dinâmico/lazy.
# collect_all -> (datas, binaries, hiddenimports). É isto que mata o whack-a-mole:
# pega submódulos + dados (ex.: tabela periódica do pymatgen) + binários de uma vez.
# -----------------------------------------------------------------------------
COLLECT_ALL_PKGS = [
    'pymatgen',     # cristalografia - MUITO import dinâmico + arquivos de dados (JSON)
    'mp_api',       # Materials Project - rotas resolvidas dinamicamente
    'emmet',        # modelos de dados (pydantic) do MP
    'monty',        # IO/serialização do pymatgen
    'chempy',       # balanceamento estequiométrico (usa sympy)
    'spglib',       # simetria (binário + dados)
    'pyqtgraph',    # visualização 3D (carrega itens GL dinamicamente)
    'cloudscraper', # scraping (resolve módulos em runtime)
    # plotly: NAO usar collect_all. O app nao usa plotly (vem so transitivo do
    # pymatgen e nunca cria figuras). collect_all puxava 1594 modulos + 40MB de
    # validadores inuteis e dominava o tempo de analise. O gerador + analise
    # estatica incluem o minimo para o IMPORT funcionar.
    'uncertainties',# dep do pymatgen
    'ruamel',       # YAML usado por pymatgen/monty
    'latexcodec',   # dep do pybtex (citações no pymatgen)
    'pybtex',       # bibliografia (pymatgen)
]

_SKIP_SEGS = {'tests', 'test', 'testing', '_tests', 'examples', 'example', 'docs'}

def _is_test_or_example(modname):
    return any(seg in _SKIP_SEGS for seg in modname.split('.'))

def _skip_data(dest):
    parts = dest.replace('\\', '/').split('/')
    return any(seg in _SKIP_SEGS for seg in parts)

for pkg in COLLECT_ALL_PKGS:
    try:
        d, b, h = collect_all(pkg)
        # Tira tests/examples/docs: o app nao usa, e eles dominavam o tempo de
        # analise (centenas de pyqtgraph.examples.*) e incham o bundle.
        h = [m for m in h if not _is_test_or_example(m)]
        d = [(s, dst) for (s, dst) in d if not _skip_data(dst)]
        datas += d
        binaries += b
        hiddenimports += h
        print(f"[SPEC] collect_all('{pkg}'): +{len(d)} datas, +{len(b)} bins, +{len(h)} hidden (sem tests/examples)")
    except Exception as e:
        print(f"[SPEC] AVISO: collect_all('{pkg}') falhou ({e}) - seguindo.")

# Submódulos extras de import dinâmico (sem precisar de collect_all completo).
for pkg in ['scipy.signal', 'scipy.optimize', 'scipy.interpolate', 'scipy.special',
            'matplotlib.backends']:
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception as e:
        print(f"[SPEC] AVISO: collect_submodules('{pkg}') falhou ({e}).")

# Dados do pymatgen às vezes ficam fora do pacote importável -> reforço.
try:
    datas += collect_data_files('pymatgen', includes=['**/*.json', '**/*.json.gz', '**/*.yaml', '**/*.csv'])
except Exception:
    pass

# Hidden imports pontuais que não vêm por dependência óbvia.
hiddenimports += [
    'PySide6.QtPrintSupport', 'PySide6.QtOpenGLWidgets', 'PySide6.QtOpenGL',
    'OpenGL.platform.win32', 'OpenGL.arrays.numpymodule',
    'pydantic.deprecated.decorator',
    'encodings.idna',
    # pkg_resources/setuptools._vendor: o runtime hook do PyInstaller carrega
    # pkg_resources no boot, que faz "from backports import tarfile" e
    # "from jaraco... import ...". Sem isto o .exe quebra ANTES de rodar qualquer
    # código (erro clássico "No module named 'backports'").
    'backports', 'backports.tarfile',
]
# Coleta TODO o setuptools._vendor (backports, jaraco, more_itertools,
# platformdirs, ...) - mata a classe inteira do pkg_resources de uma vez.
try:
    hiddenimports += collect_submodules('setuptools._vendor')
except Exception as e:
    print(f"[SPEC] AVISO: collect_submodules('setuptools._vendor') falhou ({e}).")

# -----------------------------------------------------------------------------
# QUEBRA-CICLO: lista COMPLETA de imports do app, gerada rodando o app no venv
# limpo (build_tools/gen_hiddenimports.py). Inclui imports dinâmicos/lazy que a
# análise estática perderia. Se o arquivo não existir, o build segue sem ele.
# -----------------------------------------------------------------------------
_gen = os.path.join(base_path, 'build_tools', 'hiddenimports_generated.txt')
if os.path.exists(_gen):
    with open(_gen, encoding='utf-8') as _fh:
        _extra = [ln.strip() for ln in _fh if ln.strip() and not ln.startswith('#')]
    hiddenimports += _extra
    print(f"[SPEC] hiddenimports_generated.txt: +{len(_extra)} módulos do fecho real")
else:
    print("[SPEC] AVISO: hiddenimports_generated.txt ausente (rode gen_hiddenimports.py).")

# -----------------------------------------------------------------------------
# EXCLUDES - lixo que não deve entrar (no venv limpo a maioria nem existe;
# mantido como cinto-de-segurança). NÃO excluir sympy/networkx/pandas: o
# pymatgen/chempy precisam deles.
# -----------------------------------------------------------------------------
excludes = [
    # GUIs/toolkits não usados
    'tkinter', '_tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'wx',
    # Ciência/ML pesado não usado pelo app
    # (plotly NÃO entra aqui: matfinder.core.api_logic e mp_api o importam)
    'cv2', 'opencv', 'tensorflow', 'torch', 'jax', 'jaxlib', 'sklearn',
    'mediapipe', 'h5py', 'sounddevice', 'xrayutilities',
    # Notebook/dev
    'IPython', 'ipykernel', 'jupyter', 'jupyterlab', 'notebook', 'nbconvert',
    'nbformat', 'debugpy', 'pytest', '_pytest', 'nose', 'sphinx',
    # Cloud não usado
    'boto3', 'botocore', 's3transfer',
    # PySide6 Addons pesados (DLLs também filtradas abaixo)
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
    'PySide6.QtWebChannel', 'PySide6.QtWebSockets', 'PySide6.QtQuick', 'PySide6.QtQml',
    'PySide6.QtQuick3D', 'PySide6.QtQuickWidgets', 'PySide6.QtQuickControls2',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras', 'PySide6.QtCharts',
    'PySide6.QtDataVisualization', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtLocation',
    'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSql', 'PySide6.QtTest',
    'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtScxml',
    # matplotlib 3D (usamos pyqtgraph)
    'mpl_toolkits.mplot3d',
    # exemplos/testes que so pesavam o build (nao usados pelo app)
    'pyqtgraph.examples',
    'pyqtgraph.opengl.examples',
    'chempy.util.tests',
    'pymatgen.util.testing',
]

# -----------------------------------------------------------------------------
# ANÁLISE
# -----------------------------------------------------------------------------
a = Analysis(
    [os.path.join(base_path, 'run_matfinder.py')],
    pathex=[base_path],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],          # NÃO usar os hooks antigos de scripts/hooks (substituídos por collect_all)
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,            # remove asserts e nível 1 de otimização de bytecode
)

# -----------------------------------------------------------------------------
# FILTRO DE BINÁRIOS - remove DLLs pesadas do Qt (PySide6_Addons) ~300MB
# -----------------------------------------------------------------------------
excluded_binaries = [
    'Qt6WebEngineCore', 'Qt6WebEngine', 'QtWebEngine', 'QtWebEngineProcess',
    'Qt6Quick', 'Qt6Qml', 'Qt6QmlModels', 'Qt6QmlCore', 'Qt6QmlWorkerScript',
    'Qt6QuickControls2', 'Qt6QuickLayouts', 'Qt6QuickParticles', 'Qt6QuickShapes',
    'Qt6QuickTemplates2', 'Qt6QuickWidgets', 'Qt6QuickDialogs2', 'QtQuick', 'QtQml',
    'Qt6Multimedia', 'Qt6MultimediaWidgets', 'QtMultimedia',
    'avcodec', 'avformat', 'avutil', 'swresample', 'swscale',
    'Qt63DCore', 'Qt63DRender', 'Qt63DInput', 'Qt63DLogic', 'Qt63DAnimation',
    'Qt63DExtras', 'Qt3D',
    'Qt6Pdf', 'Qt6PdfWidgets',
    'Qt6WebChannel', 'Qt6WebSockets', 'Qt6Bluetooth', 'Qt6Designer', 'Qt6Help',
    'Qt6Location', 'Qt6Nfc', 'Qt6Positioning', 'Qt6RemoteObjects', 'Qt6Scxml',
    'Qt6Sensors', 'Qt6SerialPort', 'Qt6SerialBus', 'Qt6Sql', 'Qt6Test',
    'Qt6TextToSpeech', 'Qt6VirtualKeyboard', 'Qt6Charts', 'Qt6DataVisualization',
    'Qt6StateMachine', 'Qt6LanguageServer', 'Qt6Quick3D',
]
a.binaries = [
    (name, path, typ) for (name, path, typ) in a.binaries
    if not any(excl in name for excl in excluded_binaries)
]

# -----------------------------------------------------------------------------
# EMPACOTAMENTO
# -----------------------------------------------------------------------------
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MatFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # UPX desligado (DLLs do Qt quebram com UPX)
    console=False,         # GUI sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_path, 'matfinder', 'assets', 'icons', 'polvo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='MatFinder',
)
