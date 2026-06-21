#!/usr/bin/env python
"""
gen_hiddenimports.py - QUEBRA-CICLO do "módulo faltando".

Roda no VENV LIMPO (source) e importa o app inteiro + as libs que ele usa,
capturando o FECHO REAL de imports (sys.modules). Isso inclui imports
dinâmicos/lazy (importlib, __getattr__, lazy_loader) que a análise estática do
PyInstaller perde. A saída (hiddenimports_generated.txt) é lida pelo
MatFinder.spec, então o bundle passa a conter TUDO que o app toca.

Resultado: em vez de descobrir módulos faltantes 1 a 1 abrindo o .exe, o build
já empacota o conjunto completo medido de um app que importa de verdade.

USO (com o python do venv limpo):
    .venv-build\\Scripts\\python build_tools\\gen_hiddenimports.py
"""

import importlib
import os
import pkgutil
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Top-levels que NUNCA devem ir pro bundle (espelha os excludes do spec).
JUNK_TOPLEVEL = {
    "tkinter", "PyQt5", "PyQt6", "PySide2", "wx", "cv2", "tensorflow", "torch",
    "jax", "jaxlib", "sklearn", "mediapipe", "h5py", "sounddevice",
    "xrayutilities", "IPython", "ipykernel", "jupyter", "jupyterlab", "notebook",
    "nbconvert", "nbformat", "nbclient", "debugpy", "pytest", "_pytest", "nose",
    "sphinx", "boto3", "botocore", "s3transfer", "pip", "setuptools", "wheel",
    "_distutils_hack", "pydevd", "pydev",
}

# Sementes: o que o MatFinder usa (inclui submódulos lazy importantes).
SEEDS = [
    "PySide6.QtWidgets", "PySide6.QtGui", "PySide6.QtCore",
    "PySide6.QtOpenGLWidgets", "PySide6.QtPrintSupport", "PySide6.QtNetwork",
    "numpy", "scipy", "scipy.signal", "scipy.optimize", "scipy.interpolate",
    "scipy.ndimage", "scipy.special", "scipy.sparse",
    "matplotlib", "matplotlib.pyplot", "matplotlib.backends.backend_qtagg",
    "pyqtgraph", "pyqtgraph.opengl", "OpenGL.GL",
    "pymatgen.core", "pymatgen.core.structure", "pymatgen.io.cif",
    "pymatgen.symmetry.analyzer", "pymatgen.analysis.diffraction.xrd",
    "mp_api.client", "emmet.core", "monty.json", "monty.serialization",
    "spglib", "pydantic", "PIL.Image", "openpyxl", "bs4", "chempy",
    "cloudscraper", "requests", "pywt", "pandas",
]


def safe_import(name):
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def main():
    print(f"[gen] python: {sys.executable}")
    n_ok = 0
    for s in SEEDS:
        if safe_import(s):
            n_ok += 1
    print(f"[gen] sementes importadas: {n_ok}/{len(SEEDS)}")

    # Todos os submódulos do próprio app.
    if safe_import("matfinder"):
        import matfinder
        for info in pkgutil.walk_packages(matfinder.__path__, prefix="matfinder."):
            safe_import(info.name)
    # Entry point real (puxa a árvore de imports de verdade).
    safe_import("matfinder.app_main")

    mods = set()
    for name, mod in list(sys.modules.items()):
        if not name or mod is None:
            continue
        top = name.split(".")[0]
        if top in JUNK_TOPLEVEL:
            continue
        if name in sys.builtin_module_names:
            continue
        # precisa ter origem real (descarta módulos sintéticos)
        if getattr(mod, "__spec__", None) is None and getattr(mod, "__file__", None) is None:
            continue
        mods.add(name)

    out = os.path.join(HERE, "hiddenimports_generated.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# Gerado por gen_hiddenimports.py - NÃO editar à mão.\n")
        fh.write("# Fecho real de imports do MatFinder (venv limpo).\n")
        for m in sorted(mods):
            fh.write(m + "\n")
    print(f"[gen] escritos {len(mods)} módulos em {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
