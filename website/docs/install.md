# Download & Install

!!! success "No account or registration required"
    All downloads come from the public [GitHub Releases](https://github.com/SrValentim/MatFinder/releases/latest)
    page. No sign-up, no email, no GitHub account needed.

[Download the latest release](https://github.com/SrValentim/MatFinder/releases/latest){ .md-button .md-button--primary }

---

## Option 1 — Ready-to-use app (recommended)

1. Open the [latest release](https://github.com/SrValentim/MatFinder/releases/latest).
2. Download either the **installer** (`MatFinder-…-Setup.exe`) or the portable
   **`MatFinder-…-win64.zip`**.
3. Run the installer **or** extract the zip and launch **`MatFinder/MatFinder.exe`**
   (and `PhaseDRX.exe` for the XRD suite). No Python, no setup.

!!! note "System requirements"
    Windows 10/11 (64-bit). 4 GB RAM minimum (8 GB recommended).

!!! warning "Windows SmartScreen"
    The installer is not code-signed yet, so Windows may show a SmartScreen
    warning. Click **More info → Run anyway**. See the [FAQ](faq.md) for details.

---

## Option 2 — Run from source (Windows, Linux or macOS)

```bash
git clone https://github.com/SrValentim/MatFinder.git
cd MatFinder

# Windows
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
.venv\Scripts\python run_matfinder.py

# Linux / macOS
python3.11 -m venv .venv
.venv/bin/python -m pip install -r build_tools/requirements-build.lock.txt
.venv/bin/python run_matfinder.py
```

Requires **Python 3.11 (64-bit)**. The pinned `build_tools/requirements-build.lock.txt`
is the reproducible dependency set. Running from source works on all three
platforms; the pre-built `.exe`/installer are Windows-only.

---

## Option 3 — Compile your own optimized `.exe`

1. Double-click **`INSTALAR_REQUISITOS.bat`** — installs Python 3.11 + dependencies (once).
2. Double-click **`COMPILAR.bat`** — produces `dist/MatFinder/` with `MatFinder.exe`
   and `PhaseDRX.exe` (~450 MB, shared `_internal`).

Full guide: [`COMO_COMPILAR.md`](https://github.com/SrValentim/MatFinder/blob/main/COMO_COMPILAR.md).

---

## Optional — Materials Project API key

Searching the **Materials Project** database needs a free API key (COD, OQMD and ROD
work without one). Get a key from the
[Materials Project dashboard](https://next-gen.materialsproject.org/api) and set it in
MatFinder under *Settings ▸ Materials Project Key…*. The key is stored locally on your
machine and is never bundled with the app.
