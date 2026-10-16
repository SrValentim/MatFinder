# MatFinder

<div align="center">
  <img src="matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Crystalline Materials Search and Analysis**
  
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20778195.svg)](https://doi.org/10.5281/zenodo.20778195)
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#get-matfinder)
  
  🌐 **English** · [Português](docs/README.pt-BR.md) · [Deutsch](docs/README.de.md)

  <br/><br/>

  <a href="https://github.com/SrValentim/MatFinder/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD-Windows_64--bit-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="Download MatFinder for Windows"/>
  </a>

  <br/>
  <sub>Windows installer or portable <code>.zip</code> · no Python required</sub>

  <br/><br/>

  ###  [Overview](README.md) ·  [Screenshots](docs/SCREENSHOTS.md)
</div>

---

##  About

MatFinder is a complete desktop application for searching, visualizing, and analyzing crystalline material structures. Developed at the Federal University of Amazonas (UFAM), Brazil, it integrates multiple crystallographic databases and X-ray diffraction analysis tools.

###  Highlight: automatic phase identification (search-match)

PhaseDRX identifies the crystalline phases in a diffractogram with a search-match
workflow like the ones in commercial XRD software — **free, and using open databases only**:

- **Robust peak search**: multi-scale detection, Kα2 doublet fitting, Kβ flags and a mode
  for broad or amorphous patterns. The peak list can be edited without touching the data.
- **Candidates from open databases**: the [Crystallography Open Database (COD)](https://www.crystallography.net/)
  and the [Materials Project](https://next-gen.materialsproject.org/) (free API key), filtered
  with a periodic-table element selector. No paid database or license is required.
- **Scores from 0 to 100** that weigh peak positions, expected strong reflections and
  intensities, with duplicate entries grouped and the reflections previewed over your pattern.
- **Accept and rescore**: accepted phases are fitted together, the remaining candidates are
  rescored against the intensity that is still unexplained, and unexplained peaks are flagged.
- **Semi-quantitative mass fractions** (RIR), and one click to send the accepted phases to
  the simulation as a multiphase combination.

Step by step: [Phase identification guide](https://srvalentim.github.io/MatFinder/guide/search-match/).

###  Multilingual Support

MatFinder is available in:
- 🇧🇷 **Portuguese** (default)
- 🇺🇸 **English**
- 🇩🇪 **German** (Deutsch)


### Main Features

- **Integrated Search**: Materials Project, COD (Crystallography Open Database), OQMD, ROD (Raman Open Database)
- **XRD Analysis**: Diffraction pattern simulation and comparison
- **Phase Identification (search-match)**: automatic identification of the phases in an XRD
  pattern, with candidates from COD and the Materials Project
- **Analysis Tools**:
  - CIF file editor
  - Stoichiometric calculator
  - Interactive periodic table
  - Background removal (SNIP, Polynomial)
  - Data normalization (multiple methods)
- **Visualization**: Interactive graphs with customization
- **Management**: Favorites and search history system

---

##  Get MatFinder

###  Option 1 — Download the ready-to-use app (recommended)

1. Open **[Releases ▸ latest](https://github.com/SrValentim/MatFinder/releases/latest)**.
2. Download either the **installer** (`MatFinder-…-Setup.exe`) or the portable
   **`MatFinder-…-win64.zip`**.
3. Run the installer **or** extract the zip and run **`MatFinder/MatFinder.exe`**
   (and `PhaseDRX.exe` for the XRD suite). No Python, no setup.

> Works on **Windows 10/11 (64-bit)**. 4 GB RAM minimum (8 GB recommended).

###  Option 2 — Run from source (Windows, Linux or macOS)

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

> Requires **Python 3.11 (64-bit)**. The pinned `build_tools/requirements-build.lock.txt`
> is the reproducible dependency set. Running from source works on all three
> platforms; the pre-built `.exe`/installer are Windows-only.

###  Option 3 — Compile your own optimized `.exe`

1. Double-click **`build_tools/INSTALAR_REQUISITOS.bat`** — installs Python 3.11 + dependencies (once).
2. Double-click **`build_tools/COMPILAR.bat`** — produces `dist/MatFinder/` with `MatFinder.exe`
   and `PhaseDRX.exe` (~450 MB, shared `_internal`).

Full guide: **[`COMO_COMPILAR.md`](docs/compilation/COMO_COMPILAR.md)** · [`GUIA_COMPILACAO.md`](docs/compilation/GUIA_COMPILACAO.md)

---

## Documentation

- **User guide (website)**: <https://srvalentim.github.io/MatFinder/> — source in [`website/`](website/)
- **Screenshots**: [`docs/SCREENSHOTS.md`](docs/SCREENSHOTS.md)
- **Compilation guides** (PT): [`docs/compilation/`](docs/compilation/)
- **Technical notes and validation reports** (PT): [`docs/dev/`](docs/dev/)
- **Examples** (sample CIFs + real XRD data): [`examples/`](examples/)
- **GPL v3 License**: [`LICENSE`](LICENSE)

---

##  Development

### Project Structure

```
MatFinder/
├── matfinder/                       # Source code
│   ├── core/                        # Core modules (database APIs, translator, favorites, history)
│   ├── data/                        # Data handling (CIF editor/handler, COD API)
│   ├── tools/                       # Tools: calculator, periodic table, XRD suite (PhaseDRX)
│   └── assets/                      # Icons, logos and translations
├── tests/                           # Automated tests (pytest) + their requirements.txt
├── examples/                        # Sample CIFs and real XRD data (also used by the tests)
├── docs/                            # Documentation
│   ├── README.pt-BR.md              # This README in Portuguese
│   ├── README.de.md                 # This README in German
│   ├── SCREENSHOTS.md               # Visual tour (images in screenshots/)
│   ├── compilation/                 # Build guides (PT)
│   └── dev/                         # Technical notes and validation reports (PT)
├── website/                         # Documentation site (MkDocs -> GitHub Pages)
├── build_tools/                     # Build, installer and release tooling
│   ├── INSTALAR_REQUISITOS.bat      # 1-click: install Python 3.11 + deps
│   ├── COMPILAR.bat                 # 1-click: compile the .exe
│   ├── build_clean.py               # Build pipeline: map imports + build + selftest
│   ├── gen_hiddenimports.py         # Maps the app's real import closure
│   ├── MatFinder.spec               # PyInstaller config (collect_all + Qt DLL filter)
│   ├── MatFinder.iss                # Windows installer (Inno Setup)
│   ├── release.py                   # Local release in one command
│   ├── version_manager.py           # Syncs the version number in every file
│   ├── requirements-build.lock.txt  # Exact, reproducible deps (Python 3.11)
│   └── requirements-build.txt       # Readable/minimal deps
├── .github/                         # CI workflows, issue templates, contributing guide, code of conduct
├── run_matfinder.py                 # Entry point: MatFinder (supports --selftest)
├── run_phasedrx.py                  # Entry point: PhaseDRX (standalone XRD suite)
├── CHANGELOG.md                     # Version history
├── CITATION.cff                     # Citation metadata (Zenodo)
├── LICENSE                          # GPL v3 license
├── pytest.ini                       # Test configuration
└── VERSION                          # Current version number
```

### Compilation

Optimized build (~450 MB, two exes sharing `_internal`, no "missing module" loop).
One-time setup with `INSTALAR_REQUISITOS.bat`, then `COMPILAR.bat` to build (both in
`build_tools/`):

```bat
build_tools\INSTALAR_REQUISITOS.bat   :: 1x: Python 3.11 + deps (from the lock)
build_tools\COMPILAR.bat              :: build -> dist\MatFinder\MatFinder.exe
build_tools\COMPILAR.bat --clean      :: pristine rebuild (clears the cache)
```

- Self-check after a build (lists any missing module at once): `MatFinder.exe --selftest`
- **Tests:** `python -m pip install -r tests/requirements.txt`, then `python -m pytest`
  (see [`tests/README.md`](tests/README.md)).
- **CI:** pushing a tag `vX.Y.Z` triggers `.github/workflows/build-release.yml`,
  which builds on **Windows, Linux and macOS** and publishes a Release with the
  Windows installer + `.zip`, a Linux `.tar.gz` and a macOS `.zip`.

For details, see **[`COMO_COMPILAR.md`](docs/compilation/COMO_COMPILAR.md)** and
[`GUIA_COMPILACAO.md`](docs/compilation/GUIA_COMPILACAO.md).

### Technologies Used

| Component | Technology |
|-----------|------------|
| **Interface** | PySide6 (Qt for Python) |
| **Graphics** | Matplotlib |
| **Scientific Computing** | NumPy, SciPy, Pandas |
| **Crystallography** | Pymatgen |
| **APIs** | mp-api (Materials Project), OQMD, COD (Crystallography Open Database) and ROD (Raman Open Database) |
| **Compilation** | PyInstaller |

---

##  Contributing

Contributions are welcome — bug reports, feature ideas, docs, translations and
code. Please read **[`CONTRIBUTING.md`](.github/CONTRIBUTING.md)** (dev setup, coding and
translation guidelines, PR process) and our
**[`CODE_OF_CONDUCT.md`](.github/CODE_OF_CONDUCT.md)**.

Quick version:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

##  How to cite

If you use MatFinder in your research, please cite it (archived on **Zenodo**):

> Valentim, R. (2026). *MatFinder - X-ray diffraction analysis tools* (3.25.0). Zenodo. https://doi.org/10.5281/zenodo.20820779

**DOI:** [10.5281/zenodo.20820779](https://doi.org/10.5281/zenodo.20820779) (version 3.25.0) · [10.5281/zenodo.20778195](https://doi.org/10.5281/zenodo.20778195) (all versions, always latest)

<details>
<summary>BibTeX</summary>

```bibtex
@software{valentim_matfinder_2026,
  author    = {Valentim, Raynner},
  title     = {{MatFinder - X-ray diffraction analysis tools}},
  year      = {2026},
  publisher = {Zenodo},
  version   = {3.25.0},
  doi       = {10.5281/zenodo.20820779},
  url       = {https://doi.org/10.5281/zenodo.20820779}
}
```
</details>

> 💡 GitHub also generates a **"Cite this repository"** button (sidebar of the repo page) from [`CITATION.cff`](CITATION.cff).

---

##  License

This project is licensed under the **GNU General Public License v3.0** - see the [`LICENSE`](LICENSE) file for details.

### License Summary

- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Changes must be documented
- ⚠️ Source code must be made available
- ⚠️ Same license must be used in derivative works

---

##  Author

**Raynner Valentim**
- 🎓 Federal University of Amazonas (UFAM) | Department of Physics | Materials Physics Department
- 📧 Email: [Raynnervalentim@hotmail.com](mailto:Raynnervalentim@hotmail.com)
- 🐙 GitHub: [@SrValentim](https://github.com/SrValentim)

---

## Acknowledgments

- **Materials Project** - Materials database
- **Crystallography Open Database (COD)** - Crystal structures
- **Open Quantum Materials Database (OQMD)**
- **Raman Open Database (ROD)**
- **Pymatgen** - Materials analysis framework
- **Python Community** - Open source tools and libraries

---

##  Project Status

🟢 **Active** — under development and maintenance.

**Current version:** 3.27.0 — see the [`CHANGELOG.md`](CHANGELOG.md) for the full history.

Recent highlights:
- Automatic phase identification (search-match) using the open COD and Materials Project databases
- Full UI translation (Portuguese, English, German)
- PhaseDRX as a standalone app (`PhaseDRX.exe`) with cross-app CIF export
- Open-access article retrieval by DOI (OpenAlex/Unpaywall)
- Runs from source on Windows, Linux and macOS

---

## Report Issues

Found a bug? Have a suggestion? Open an [issue](https://github.com/SrValentim/MatFinder/issues)
(templates available) — see [`CONTRIBUTING.md`](.github/CONTRIBUTING.md) for what to include.

---

<div align="center">
  <sub>Excellence is a habit</sub>
</div>

