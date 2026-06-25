# Features

MatFinder targets the full *discovery-to-identification* loop of a powder-XRD lab,
in one application.

## Integrated database search

Search across multiple open databases without leaving the app:

- **Materials Project** (free API key)
- **COD** — Crystallography Open Database
- **OQMD** — Open Quantum Materials Database
- **ROD** — Raman Open Database

Results show space group, band gap, formation energy and thermodynamic stability,
with one-click CIF download or export into the analysis module.

## CIF retrieval and management

Download, edit and validate CIF files, generate symmetrized structures, and send a
structure straight into PhaseDRX for analysis.

## PhaseDRX — XRD analysis suite

![PhaseDRX](assets/phasedrx.png){ width="260" }

PhaseDRX is the analysis module (also available as a standalone `PhaseDRX.exe`):

- Load experimental diffractograms and stack a whole time series.
- Simulate diffraction patterns from CIF files and overlay them on the measured data.
- Read per-peak 2θ, intensity and d-spacing.
- Inspect the crystal structure in an interactive **3D viewer**.

## Data treatment

Built-in, validated signal-processing tools:

- **Background removal**: SNIP, asymmetrically reweighted penalized least squares
  (arPLS), polynomial and spline.
- **Normalization** (multiple methods).
- **Smoothing**: Savitzky–Golay.
- **Denoising**: wavelet.
- **Peak detection**.

## Other tools

- CIF file editor
- Stoichiometric calculator
- Interactive periodic table
- Open-access article retrieval by DOI (OpenAlex / Unpaywall)

## Cross-platform & multilingual

- Runs from source on **Windows, Linux and macOS**; pre-built installer for Windows.
- Interface available in **Portuguese, English and German**.
- Free and open-source under **GPL-3.0**.

---

!!! note "Screenshots wanted"
    This page can be enriched with screenshots of each tool. Drop images into
    `website/docs/assets/` and reference them here, for example:
    `![Main window](assets/screenshot-main.png)`.
