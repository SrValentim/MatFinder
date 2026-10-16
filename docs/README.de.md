# MatFinder

<div align="center">
  <img src="../matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Suche und Analyse kristalliner Materialien**
  
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20778195.svg)](https://doi.org/10.5281/zenodo.20778195)
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](../LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#matfinder-beziehen)
  
  🌐 [English](../README.md) · [Português](README.pt-BR.md) · **Deutsch**

  <br/><br/>

  <a href="https://github.com/SrValentim/MatFinder/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD-Windows_64--bit-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="MatFinder für Windows herunterladen"/>
  </a>

  <br/>
  <sub>Windows-Installer oder portable <code>.zip</code> · kein Python erforderlich</sub>

  <br/><br/>

  ###  [Überblick](README.de.md) ·  [Screenshots](SCREENSHOTS.md)
</div>

---

##  Über

MatFinder ist eine vollständige Desktop-Anwendung zum Suchen, Visualisieren und Analysieren kristalliner Materialstrukturen. Entwickelt an der Bundesuniversität von Amazonas (UFAM) in Brasilien, vereint sie mehrere kristallographische Datenbanken und Werkzeuge zur Röntgenbeugungsanalyse.

###  Highlight: automatische Phasenidentifizierung (Search-Match)

PhaseDRX identifiziert die kristallinen Phasen eines Diffraktogramms mit einem
Search-Match-Ablauf wie in kommerzieller XRD-Software – **kostenlos und nur mit offenen Datenbanken**:

- **Robuste Peaksuche**: Multiskalen-Erkennung, Anpassung des Kα2-Dubletts, Kβ-Markierung und
  ein Modus für breite oder amorphe Muster. Die Peakliste lässt sich bearbeiten, ohne die Daten zu verändern.
- **Kandidaten aus offenen Datenbanken**: die [Crystallography Open Database (COD)](https://www.crystallography.net/)
  und das [Materials Project](https://next-gen.materialsproject.org/) (kostenloser API-Schlüssel),
  gefiltert über eine Elementauswahl im Periodensystem. Keine kostenpflichtige Datenbank oder Lizenz nötig.
- **Bewertung von 0 bis 100** nach Peakpositionen, erwarteten starken Reflexen und
  Intensitäten, mit gruppierten Duplikaten und einer Vorschau der Reflexe über Ihrem Muster.
- **Akzeptieren und neu bewerten**: Akzeptierte Phasen werden gemeinsam angepasst, die übrigen
  Kandidaten gegen die noch nicht erklärte Intensität neu bewertet, und Peaks ohne Phase werden markiert.
- **Halbquantitative Massenanteile** (RIR) und ein Klick, um die akzeptierten Phasen als
  Mehrphasenkombination an die Simulation zu senden.

Schritt für Schritt (auf Englisch): [Anleitung zur Phasenidentifizierung](https://srvalentim.github.io/MatFinder/guide/search-match/).

###  Mehrsprachige Unterstützung

MatFinder ist verfügbar in:
- 🇧🇷 **Portugiesisch** (Standard)
- 🇺🇸 **Englisch**
- 🇩🇪 **Deutsch**


### Hauptfunktionen

- **Integrierte Suche**: Materials Project, COD (Crystallography Open Database), OQMD, ROD (Raman Open Database)
- **XRD-Analyse**: Simulation und Vergleich von Beugungsmustern
- **Phasenidentifizierung (Search-Match)**: automatische Identifizierung der Phasen eines
  XRD-Musters mit Kandidaten aus COD und dem Materials Project
- **Analysewerkzeuge**:
  - CIF-Datei-Editor
  - Stöchiometrischer Rechner
  - Interaktives Periodensystem
  - Untergrundentfernung (SNIP, Polynom)
  - Datennormalisierung (mehrere Methoden)
- **Visualisierung**: interaktive, anpassbare Diagramme
- **Verwaltung**: Favoriten- und Suchverlaufssystem

---

##  MatFinder beziehen

###  Option 1 — Die fertige Anwendung herunterladen (empfohlen)

1. Öffnen Sie **[Releases ▸ latest](https://github.com/SrValentim/MatFinder/releases/latest)**.
2. Laden Sie entweder den **Installer** (`MatFinder-…-Setup.exe`) oder die portable
   **`MatFinder-…-win64.zip`** herunter.
3. Führen Sie den Installer aus **oder** entpacken Sie die ZIP-Datei und starten Sie
   **`MatFinder/MatFinder.exe`** (und `PhaseDRX.exe` für die XRD-Suite). Kein Python,
   keine Einrichtung.

> Funktioniert unter **Windows 10/11 (64-Bit)**. Mindestens 4 GB RAM (8 GB empfohlen).

###  Option 2 — Aus dem Quellcode ausführen (Windows, Linux oder macOS)

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

> Erfordert **Python 3.11 (64-Bit)**. Die gepinnte Datei
> `build_tools/requirements-build.lock.txt` ist der reproduzierbare Satz an
> Abhängigkeiten. Die Ausführung aus dem Quellcode funktioniert auf allen drei
> Plattformen; die vorkompilierte `.exe`/der Installer sind nur für Windows.

###  Option 3 — Eigene optimierte `.exe` kompilieren

1. Doppelklicken Sie auf **`build_tools/INSTALAR_REQUISITOS.bat`** — installiert Python 3.11 + Abhängigkeiten (einmalig).
2. Doppelklicken Sie auf **`build_tools/COMPILAR.bat`** — erzeugt `dist/MatFinder/` mit `MatFinder.exe`
   und `PhaseDRX.exe` (~450 MB, gemeinsam genutztes `_internal`).

Vollständige Anleitung: **[`COMO_COMPILAR.md`](compilation/COMO_COMPILAR.md)** · [`GUIA_COMPILACAO.md`](compilation/GUIA_COMPILACAO.md)

---

## Dokumentation

- **Benutzerhandbuch (Website)**: <https://srvalentim.github.io/MatFinder/> — Quelle in [`website/`](../website/)
- **Screenshots**: [`docs/SCREENSHOTS.md`](SCREENSHOTS.md)
- **Kompilierungsanleitungen** (PT): [`docs/compilation/`](compilation/)
- **Technische Notizen und Validierungsberichte** (PT): [`docs/dev/`](dev/)
- **Beispiele** (Beispiel-CIFs + echte XRD-Daten): [`examples/`](../examples/)
- **GPL-v3-Lizenz**: [`LICENSE`](../LICENSE)

---

##  Entwicklung

### Projektstruktur

```
MatFinder/
├── matfinder/                       # Quellcode
│   ├── core/                        # Kernmodule (Datenbank-APIs, Übersetzung, Favoriten, Verlauf)
│   ├── data/                        # Datenverarbeitung (CIF-Editor/-Handler, COD-API)
│   ├── tools/                       # Werkzeuge: Rechner, Periodensystem, XRD-Suite (PhaseDRX)
│   └── assets/                      # Symbole, Logos und Übersetzungen
├── tests/                           # Automatisierte Tests (pytest) + deren requirements.txt
├── examples/                        # Beispiel-CIFs und echte XRD-Daten (auch von den Tests genutzt)
├── docs/                            # Dokumentation
│   ├── README.pt-BR.md              # Diese README auf Portugiesisch
│   ├── README.de.md                 # Diese README auf Deutsch
│   ├── SCREENSHOTS.md               # Visuelle Tour (Bilder in screenshots/)
│   ├── compilation/                 # Build-Anleitungen (PT)
│   └── dev/                         # Technische Notizen und Validierungsberichte (PT)
├── website/                         # Dokumentationsseite (MkDocs -> GitHub Pages)
├── build_tools/                     # Build-, Installer- und Release-Werkzeuge
│   ├── INSTALAR_REQUISITOS.bat      # 1 Klick: Python 3.11 + Abhängigkeiten installieren
│   ├── COMPILAR.bat                 # 1 Klick: die .exe kompilieren
│   ├── build_clean.py               # Build-Pipeline: Imports abbilden + kompilieren + Selftest
│   ├── gen_hiddenimports.py         # Bildet den tatsächlichen Import-Abschluss der App ab
│   ├── MatFinder.spec               # PyInstaller-Konfiguration (collect_all + Qt-DLL-Filter)
│   ├── MatFinder.iss                # Windows-Installer (Inno Setup)
│   ├── release.py                   # Lokales Release mit einem Befehl
│   ├── version_manager.py           # Synchronisiert die Versionsnummer in allen Dateien
│   ├── requirements-build.lock.txt  # Exakte, reproduzierbare Abhängigkeiten (Python 3.11)
│   └── requirements-build.txt       # Lesbare/minimale Abhängigkeiten
├── .github/                         # CI-Workflows, Issue-Vorlagen, Beitragsleitfaden, Verhaltenskodex
├── run_matfinder.py                 # Einstiegspunkt: MatFinder (unterstützt --selftest)
├── run_phasedrx.py                  # Einstiegspunkt: PhaseDRX (eigenständige XRD-Suite)
├── CHANGELOG.md                     # Versionshistorie
├── CITATION.cff                     # Zitationsmetadaten (Zenodo)
├── LICENSE                          # GPL-v3-Lizenz
├── pytest.ini                       # Testkonfiguration
└── VERSION                          # Aktuelle Versionsnummer
```

### Kompilierung

Optimierter Build (~450 MB, zwei ausführbare Dateien, die sich `_internal` teilen, ohne
die "fehlendes Modul"-Schleife). Einmalige Einrichtung mit `INSTALAR_REQUISITOS.bat`,
danach `COMPILAR.bat` zum Bauen (beide liegen in `build_tools/`):

```bat
build_tools\INSTALAR_REQUISITOS.bat   :: 1x: Python 3.11 + Abhängigkeiten (aus dem Lock)
build_tools\COMPILAR.bat              :: Build -> dist\MatFinder\MatFinder.exe
build_tools\COMPILAR.bat --clean      :: sauberer Neubau (leert den Cache)
```

- Selbstprüfung nach einem Build (listet fehlende Module auf einmal auf): `MatFinder.exe --selftest`
- **Tests:** `python -m pip install -r tests/requirements.txt`, danach `python -m pytest`
  (siehe [`tests/README.md`](../tests/README.md)).
- **CI:** Das Pushen eines Tags `vX.Y.Z` löst `.github/workflows/build-release.yml` aus,
  das unter **Windows, Linux und macOS** baut und ein Release mit dem Windows-Installer
  + `.zip`, einem Linux-`.tar.gz` und einem macOS-`.zip` veröffentlicht.

Für Details siehe **[`COMO_COMPILAR.md`](compilation/COMO_COMPILAR.md)** und
[`GUIA_COMPILACAO.md`](compilation/GUIA_COMPILACAO.md).

### Verwendete Technologien

| Komponente | Technologie |
|-----------|------------|
| **Oberfläche** | PySide6 (Qt for Python) |
| **Grafiken** | Matplotlib |
| **Wissenschaftliches Rechnen** | NumPy, SciPy, Pandas |
| **Kristallographie** | Pymatgen |
| **APIs** | mp-api (Materials Project), OQMD, COD (Crystallography Open Database) und ROD (Raman Open Database) |
| **Kompilierung** | PyInstaller |

---

##  Mitwirken

Beiträge sind willkommen — Fehlerberichte, Funktionsideen, Dokumentation,
Übersetzungen und Code. Bitte lesen Sie **[`CONTRIBUTING.md`](../.github/CONTRIBUTING.md)**
(Dev-Einrichtung, Code- und Übersetzungsrichtlinien, PR-Prozess) und unseren
**[`CODE_OF_CONDUCT.md`](../.github/CODE_OF_CONDUCT.md)**.

Kurzfassung:

1. Forken Sie das Repository
2. Erstellen Sie einen Branch für Ihre Funktion (`git checkout -b feature/AmazingFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'feat: add some AmazingFeature'`)
4. Pushen Sie zum Branch (`git push origin feature/AmazingFeature`)
5. Öffnen Sie einen Pull Request

---

##  Wie zitieren

Wenn Sie MatFinder in Ihrer Forschung verwenden, zitieren Sie es bitte (archiviert auf **Zenodo**):

> Valentim, R. (2026). *MatFinder - X-ray diffraction analysis tools* (3.25.0). Zenodo. https://doi.org/10.5281/zenodo.20820779

**DOI:** [10.5281/zenodo.20820779](https://doi.org/10.5281/zenodo.20820779) (Version 3.25.0) · [10.5281/zenodo.20778195](https://doi.org/10.5281/zenodo.20778195) (alle Versionen, immer die neueste)

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

> 💡 GitHub erzeugt außerdem eine Schaltfläche **"Cite this repository"** (in der Seitenleiste der Repo-Seite) aus der [`CITATION.cff`](../CITATION.cff).

---

##  Lizenz

Dieses Projekt steht unter der **GNU General Public License v3.0** — Einzelheiten finden Sie in der Datei [`LICENSE`](../LICENSE).

### Lizenzübersicht

- ✅ Änderung erlaubt
- ✅ Verbreitung erlaubt
- ✅ Private Nutzung erlaubt
- ⚠️ Änderungen müssen dokumentiert werden
- ⚠️ Der Quellcode muss bereitgestellt werden
- ⚠️ In abgeleiteten Werken muss dieselbe Lizenz verwendet werden

---

##  Autor

**Raynner Valentim**
- 🎓 Bundesuniversität von Amazonas (UFAM) | Fachbereich Physik | Materialphysik
- 📧 E-Mail: [Raynnervalentim@hotmail.com](mailto:Raynnervalentim@hotmail.com)
- 🐙 GitHub: [@SrValentim](https://github.com/SrValentim)

---

## Danksagungen

- **Materials Project** — Materialdatenbank
- **Crystallography Open Database (COD)** — Kristallstrukturen
- **Open Quantum Materials Database (OQMD)**
- **Raman Open Database (ROD)**
- **Pymatgen** — Framework zur Materialanalyse
- **Python-Community** — Open-Source-Werkzeuge und -Bibliotheken

---

##  Projektstatus

🟢 **Aktiv** — in Entwicklung und Wartung.

**Aktuelle Version:** 3.27.0 — siehe [`CHANGELOG.md`](../CHANGELOG.md) für die vollständige Historie.

Aktuelle Highlights:
- Automatische Phasenidentifizierung (Search-Match) mit den offenen Datenbanken COD und Materials Project
- Vollständige Übersetzung der Oberfläche (Portugiesisch, Englisch, Deutsch)
- PhaseDRX als eigenständige Anwendung (`PhaseDRX.exe`) mit anwendungsübergreifendem CIF-Export
- Abruf von Open-Access-Artikeln per DOI (OpenAlex/Unpaywall)
- Ausführbar aus dem Quellcode unter Windows, Linux und macOS

---

## Probleme melden

Einen Fehler gefunden? Einen Vorschlag? Öffnen Sie eine [Issue](https://github.com/SrValentim/MatFinder/issues)
(Vorlagen verfügbar) — siehe [`CONTRIBUTING.md`](../.github/CONTRIBUTING.md) für die anzugebenden Informationen.

---

<div align="center">
  <sub>Excellence is a habit</sub>
</div>
