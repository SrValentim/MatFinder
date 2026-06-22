<div align="center">

# MatFinder — Screenshots

###  [Overview](README.md) ·  [Screenshots](SCREENSHOTS.md)

A visual tour of MatFinder and its built-in XRD suite, **PhaseDRX**.

</div>

---

## 🔬 Material discovery

### Search multiple databases at once
Query the **Materials Project**, **OQMD**, **COD** and **ROD** by element. Results list the
space group, band gap, formation energy and a color-coded thermodynamic stability — alongside
favorites, external-database links, a Sci-Hub DOI downloader and quick article search.

![MatFinder main window with Materials Project search results](docs/screenshots/screenshot1.png)

### Send a structure straight to analysis
Right-click any result to open it on the Materials Project, download its CIF, fetch the matching
**ICSD** collection codes, or **export the CIF directly into PhaseDRX** — no manual download/reload.

![Right-click context menu with export and database options](docs/screenshots/screenshot2.png)

### One search box, four databases
Switch between Materials Project, OQMD, COD and ROD from a single dropdown.

![Database selector dropdown](docs/screenshots/screenshot3.png)

---

## 📈 PhaseDRX — XRD analysis suite

### Project-based workflow
PhaseDRX opens with a project launcher: start a new project, reopen an existing one, or work in
an anonymous session.

![PhaseDRX project launcher dialog](docs/screenshots/screenshot4.png)

### Experimental data workspace
Load experimental XRD patterns and clean them up with normalization, smoothing, background
removal (SNIP / polynomial) and wavelet denoising. Toggle between the **2D diffractogram** and the
**3D crystal structure**.

![PhaseDRX experimental data workspace](docs/screenshots/screenshot5.png)

### Interactive 3D crystal structure
Render and rotate the unit cell straight from a CIF (here **SmFeO₃**), with an element legend and
lattice parameters, then simulate its diffraction pattern for a chosen radiation source.

![Interactive 3D crystal structure of SmFeO3](docs/screenshots/screenshot7.png)

### Compare calculated vs. experimental
Overlay simulated CIF patterns on experimental data and read any peak's **2θ, intensity and
d-spacing** with a single click.

![Calculated CIF patterns overlaid on experimental data](docs/screenshots/screenshot8.png)

### Crystallographic editor with Auto-Fit
Refine the unit-cell parameters (with **Auto-Fit**) and tune the peak profile (Pseudo-Voigt, FWHM)
until the simulation matches the measured pattern.

![Crystallographic editor dialog with unit-cell parameters](docs/screenshots/screenshot9.png)

### Stack and compare a whole series
Stack many diffractograms to follow how a sample evolves over time, all against the reference patterns.

![Stacked experimental diffractograms compared to reference patterns](docs/screenshots/screenshot6.png)

---

## 🖼️ Publication-ready figures

### Phase identification
Export clean, annotated figures — the experimental pattern against candidate phases
(Fe, Sm₂O₃) with labeled reflections.

![Exported XRD figure: experimental vs. candidate phases](docs/screenshots/XRD1.png)

### Phase-evolution study
A full synthesis time series (**1 h → 24 h**) of SmFeO₃, stacked over the reference CIF patterns.

![Exported XRD figure: synthesis time series from 1h to 24h](docs/screenshots/XRD2.png)

---

<div align="center">

📖 **[Back to Overview](README.md)**

</div>
