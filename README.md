# MatFinder v3.24.0

<div align="center">
  <img src="matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Crystalline Materials Search and Analysis**
  
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](licenses/LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
  
  🌐 **Available in:** Português | English | Deutsch
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

## Installation

### Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB

### Installation via Python

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SrValentim/MatFinder.git
   cd MatFinder
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the program**:
   ```bash
   python run_matfinder.py
   ```

### Pre-compiled Executable

Download the latest version from [Releases](https://github.com/SrValentim/MatFinder/releases) and run `MatFinder.exe`.

---

## Documentation

- **User Manual**: [`docs/Manual do Usuário.pdf`](docs/Manual%20do%20Usuário.pdf)
- **Compilation Guide**: [`docs/compilation/`](docs/compilation/)
- **DEBUSSY Windows Setup Guide**: 
  - [🇧🇷 Portuguese](docs/DEBUSSY_WINDOWS_GUIA.md)
  - [🇺🇸 English](docs/DEBUSSY_WINDOWS_GUIDE.md)
- **GPL v3 License**: [`licenses/LICENSE_FULL.txt`](licenses/LICENSE_FULL.txt)

---

## 🛠️ Development

### Project Structure

```
MatFinder/
├── matfinder/              # Main source code
│   ├── core/              # Core modules
│   ├── data/              # Data handling (CIF, APIs)
│   ├── tools/             # Tools (calculator, XRD, etc.)
│   └── assets/            # Resources (icons, logos, configs)
├── build_tools/           # Compilation scripts
│   ├── MatFinder.spec     # PyInstaller configuration
│   ├── build_optimized.py # Optimized build script
│   └── COMPILE.bat        # Automated compilation
├── scripts/               # Auxiliary scripts
│   ├── hooks/            # Custom PyInstaller hooks
│   └── build_msi.py      # MSI installer generator
├── docs/                  # Documentation
├── licenses/              # License files
├── tests/                 # Tests
├── run_matfinder.py       # Application entry point
├── setup.py               # Installation configuration
└── requirements.txt       # Python dependencies
```

### Compilation

To compile MatFinder into an executable:

1. **Navigate to the build tools folder**:
   ```bash
   cd build_tools
   ```

2. **Run the compilation script**:
   ```bash
   COMPILE.bat
   ```

3. **The executable will be generated at**: `dist/MatFinder/MatFinder.exe`

For more details, see [`docs/compilation/BUILD_GUIDE.md`](docs/compilation/).

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

