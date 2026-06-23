---
title: 'MatFinder: an integrated open-source tool for crystallographic database search and X-ray diffraction phase analysis'
tags:
  - Python
  - crystallography
  - X-ray diffraction
  - materials science
  - CIF
  - phase identification
authors:
  - name: Raynner Valentim
    orcid: 0009-0004-3470-6893
    affiliation: 1
affiliations:
  - name: Department of Physics (Materials Physics), Federal University of Amazonas (UFAM), Brazil
    index: 1
date: 23 June 2026
bibliography: paper.bib
---

# Summary

`MatFinder` is a free, open-source desktop application that unifies, in a single
interface, the everyday workflow of a powder X-ray diffraction (XRD) laboratory:
searching multiple open crystallographic databases, retrieving and managing
Crystallographic Information Files (CIFs), simulating and comparing diffraction
patterns, and visualizing crystal structures in 3D. Its analysis module,
**PhaseDRX**, loads experimental diffractograms, cleans them (background removal,
normalization, smoothing, denoising), simulates patterns from CIFs and overlays
them with the measured data for qualitative phase identification, including an
interactive 3D view of the unit cell. `MatFinder` is built in Python on `PySide6`,
`pymatgen` [@ong2013pymatgen], NumPy/SciPy and Matplotlib, runs on Windows, Linux
and macOS, and is available in Portuguese, English and German.

# Statement of need

A recurring bottleneck in materials synthesis–characterization loops is the
fragmentation of the qualitative phase-analysis workflow. After measuring a
sample, a researcher typically converts the instrument file to a plottable format
in one program, plots it in another, and then hunts for candidate structures
across several disconnected databases — converting and re-plotting each candidate
by trial and error until a phase is identified, and repeating the whole cycle at
every synthesis step. Much of the effort is spent on format conversion, switching
between programs that do not talk to each other, and searching for CIFs scattered
across the web, often only to discover that a candidate was wrong and start over.

`MatFinder` was created to remove this friction. It integrates, in one place,
search across the **Materials Project** [@jain2013materialsproject], the
**Crystallography Open Database (COD)** [@grazulis2009cod], the **Open Quantum
Materials Database (OQMD)** [@saal2013oqmd] and the **Raman Open Database (ROD)**
[@elmendili2019rod]; CIF retrieval and management; literature lookup; and the
simulation/comparison of diffraction patterns — turning a multi-program,
multi-minute loop into a single, fast workflow.

Existing tools tend to be either closed/commercial (e.g., Match!, HighScore) or
focused on a single step of the process: `VESTA` for structure visualization
[@momma2011vesta], or `GSAS-II` for Rietveld refinement [@toby2013gsasii].
`MatFinder` instead targets the *integrated discovery-to-identification loop*,
using open databases and an open (GPL-3.0) license, lowering the barrier for
students and laboratories without access to commercial software.

# Functionality

- **Integrated database search** across Materials Project, COD, OQMD and ROD,
  built on `pymatgen` [@ong2013pymatgen]; results show space group, band gap,
  formation energy and thermodynamic stability.
- **CIF retrieval and management**, including direct export of a structure into
  the analysis module and generation of symmetrized, validatable CIFs.
- **PhaseDRX** analysis suite: simulate diffraction patterns from CIFs, overlay
  and stack experimental and calculated patterns, read per-peak 2θ/intensity/
  d-spacing, and inspect the crystal structure in an interactive 3D viewer.
- **Data treatment**: background removal (SNIP [@ryan1988snip], asymmetrically
  reweighted penalized least squares (arPLS) [@baek2015arpls], polynomial and
  spline), normalization, Savitzky–Golay smoothing, wavelet denoising and peak
  detection.
- **Open-access literature retrieval** by DOI via OpenAlex [@priem2022openalex]
  and Unpaywall.
- **Multilingual** interface (Portuguese/English/German), reproducible builds, and
  distribution as a Windows installer or runnable from source on all major
  platforms.

A worked example reproducing a phase-evolution study (an SmFeO₃ synthesis time
series compared against candidate phases) is provided in the `examples/` directory.

# Acknowledgements

`MatFinder` relies on the open databases it integrates — the Materials Project,
COD, OQMD and ROD — and on the `pymatgen` project. The software was developed at
the Federal University of Amazonas (UFAM), Brazil.

# References
