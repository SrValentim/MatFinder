# Key features

A concise map of what MatFinder can do. For step-by-step usage, see the
[User Guide](../guide/index.md).

## Search & discovery

- **Integrated database search** across Materials Project, COD, OQMD and ROD,
  built on `pymatgen`. Results show space group, band gap, formation energy and
  thermodynamic stability.
- **CIF retrieval and management**, including direct export into the analysis module
  and generation of symmetrized, validatable CIFs.
- **Favorites and search history** to keep track of candidate structures.

## Analysis (PhaseDRX)

- **Load and stack** experimental diffractograms, including full time series.
- **Simulate** diffraction patterns from CIF files for a chosen radiation source.
- **Overlay and compare** calculated vs. measured patterns for qualitative phase
  identification.
- **Read per-peak** 2θ, intensity and d-spacing.
- **Interactive 3D viewer** of the crystal structure (positions and bonds from
  `pymatgen`): complete unit cell, two-colour bonds, interatomic-distance measurement
  and camera orientation along the a/b/c axes.

## Data treatment

- **Background removal:** SNIP, asymmetrically reweighted penalized least squares
  (arPLS), polynomial and spline.
- **Normalization** (multiple methods).
- **Smoothing:** Savitzky–Golay.
- **Denoising:** wavelet.
- **Peak detection.**

## Auxiliary tools

- CIF file editor
- Stoichiometric calculator and mass-proportion calculator
- Interactive periodic table
- Open-access article retrieval by DOI (OpenAlex / Unpaywall)

## Platform & licensing

- Runs from source on **Windows, Linux and macOS**; pre-built installer for Windows.
- Interface in **Portuguese, English and German**.
- **Free and open-source** under GPL-3.0.
- **No registration** to download — straight from GitHub Releases.
