# MatFinder v3.24.0

<div align="center">
  <img src="matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Crystalline Materials Search and Analysis**
  
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20778195.svg)](https://doi.org/10.5281/zenodo.20778195)
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](licenses/LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
  
  🌐 **Available in:** Português | English | Deutsch

  <br/><br/>

  <a href="https://github.com/SrValentim/MatFinder/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD-Windows_64--bit-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="Download MatFinder for Windows"/>
  </a>

  <br/>
  <sub><b>~172 MB</b> · no Python required · just extract and run <code>MatFinder.exe</code></sub>
</div>

---

## 📋 About

MatFinder is a complete desktop application for searching, visualizing, and analyzing crystalline material structures. Developed at the Federal University of Amazonas (UFAM), Brazil, it integrates multiple crystallographic databases and X-ray diffraction analysis tools.

### 🌍 Multilingual Support

MatFinder is available in:
- 🇧🇷 **Portuguese** (default)
- 🇺🇸 **English**
- 🇩🇪 **German** (Deutsch)


### Main Features

- **Integrated Search**: Materials Project, COD (Crystallography Open Database), OQMD, ROD (Raman Open Database)
- **XRD Analysis**: Diffraction pattern simulation and comparison
- **Analysis Tools**:
  - CIF file editor
  - Stoichiometric calculator
  - Interactive periodic table
  - Background removal (SNIP, Polynomial)
  - Data normalization (multiple methods)
- **Visualization**: Interactive graphs with customization
- **Management**: Favorites and search history system

---

## 🚀 Get MatFinder

### ⬇️ Option 1 — Download the ready-to-use app (recommended)

1. Open **[Releases ▸ latest](https://github.com/SrValentim/MatFinder/releases/latest)**.
2. Download **`MatFinder-3.24.0-win64.zip`** (~172 MB).
3. Extract and run **`MatFinder/MatFinder.exe`**. No Python, no install.

> Works on **Windows 10/11 (64-bit)**. 4 GB RAM minimum (8 GB recommended).

### 🐍 Option 2 — Run from source

```bash
git clone https://github.com/SrValentim/MatFinder.git
cd MatFinder
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
.venv\Scripts\python run_matfinder.py
```

> Requires **Python 3.11 (64-bit)**. The pinned `build_tools/requirements-build.lock.txt`
> is the reproducible dependency set (the root `requirements.txt` is a full env freeze).

### 🔨 Option 3 — Compile your own optimized `.exe`

1. Double-click **`INSTALAR_REQUISITOS.bat`** — installs Python 3.11 + dependencies (once).
2. Double-click **`COMPILAR.bat`** — produces `dist/MatFinder/MatFinder.exe` (~402 MB).

Full guide: **[`COMO_COMPILAR.md`](COMO_COMPILAR.md)** · [`docs/compilation/GUIA_COMPILACAO.md`](docs/compilation/GUIA_COMPILACAO.md)

---

## Documentation

- **User Manual**: [`docs/Manual do Usuário.pdf`](docs/Manual%20do%20Usuário.pdf)
- **Compilation Guide**: [`docs/compilation/`](docs/compilation/)
- **GPL v3 License**: [`licenses/LICENSE_FULL.txt`](licenses/LICENSE_FULL.txt)

---

## 🛠️ Development

### Project Structure

```
MatFinder/
├── matfinder/                       # Main source code
│   ├── core/                       # Core modules
│   ├── data/                       # Data handling (CIF, APIs)
│   ├── tools/                      # Tools (calculator, XRD, etc.)
│   └── assets/                     # Resources (icons, logos, configs)
├── build_tools/
│   ├── MatFinder.spec              # PyInstaller config (collect_all + Qt DLL filter)
│   ├── build_clean.py              # Build pipeline: map imports + build + selftest
│   ├── gen_hiddenimports.py        # Maps the app's real import closure
│   ├── requirements-build.lock.txt # Exact, reproducible deps (Python 3.11)
│   └── requirements-build.txt      # Readable/minimal deps
├── .github/workflows/
│   └── build-release.yml           # CI: build on Windows + publish Release
├── docs/                           # Documentation (incl. compilation guide)
├── licenses/                       # License files
├── tests/                          # Tests
├── INSTALAR_REQUISITOS.bat         # 1-click: install Python 3.11 + deps
├── COMPILAR.bat                    # 1-click: compile the .exe
├── COMO_COMPILAR.md                # Build walkthrough (PT)
├── run_matfinder.py                # Entry point (supports --selftest)
└── requirements.txt                # Full environment freeze (not for building)
```

### Compilation

Optimized build (~402 MB, no "missing module" loop). One-time setup with
`INSTALAR_REQUISITOS.bat`, then `COMPILAR.bat` to build:

```bat
INSTALAR_REQUISITOS.bat       :: 1x: Python 3.11 + deps (from the lock)
COMPILAR.bat                  :: build -> dist\MatFinder\MatFinder.exe
COMPILAR.bat --clean          :: pristine rebuild (clears the cache)
```

- Self-check after a build (lists any missing module at once): `MatFinder.exe --selftest`
- **CI:** pushing a tag `vX.Y.Z` triggers `.github/workflows/build-release.yml`,
  which builds on Windows and publishes a Release with the `.zip`.

For details, see **[`COMO_COMPILAR.md`](COMO_COMPILAR.md)** and
[`docs/compilation/GUIA_COMPILACAO.md`](docs/compilation/GUIA_COMPILACAO.md).

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

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📖 How to cite

If you use MatFinder in your research, please cite it (archived on **Zenodo**):

> Valentim, R. (2026). *MatFinder - X-ray diffraction analysis tools* (3.24). Zenodo. https://doi.org/10.5281/zenodo.20778196

**DOI:** [10.5281/zenodo.20778196](https://doi.org/10.5281/zenodo.20778196) (version 3.24) · [10.5281/zenodo.20778195](https://doi.org/10.5281/zenodo.20778195) (all versions, always latest)

<details>
<summary>BibTeX</summary>

```bibtex
@software{valentim_matfinder_2026,
  author    = {Valentim, Raynner},
  title     = {{MatFinder - X-ray diffraction analysis tools}},
  year      = {2026},
  publisher = {Zenodo},
  version   = {3.24},
  doi       = {10.5281/zenodo.20778196},
  url       = {https://doi.org/10.5281/zenodo.20778196}
}
```
</details>

> 💡 GitHub also generates a **"Cite this repository"** button (sidebar of the repo page) from [`CITATION.cff`](CITATION.cff).

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0** - see the [`licenses/LICENSE`](licenses/LICENSE) file for details.

### License Summary

- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Changes must be documented
- ⚠️ Source code must be made available
- ⚠️ Same license must be used in derivative works

---

## 👨‍💻 Author

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

## 📊 Project Status

🟢 **Active** - Under development and maintenance

### Current Version: 3.24.0

**Latest Updates**:
- 🌍 Full multilingual support (Portuguese, English, German)
- Peak-specific normalization
- Interactive legend dialog
- Background removal (SNIP, Polynomial)
- Bug fixes in CIF editor
- Plotting performance improvements
- GPL v3 license integration

---

## 🐛 Report Issues

Found a bug? Have a suggestion? Open an [issue](https://github.com/SrValentim/MatFinder/issues).

---

<div align="center">
  <sub>Excellence is a habit</sub>
</div>

