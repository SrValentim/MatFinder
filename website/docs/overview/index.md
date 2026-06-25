# Summary

**MatFinder** is a free, open-source desktop application that unifies, in a single
interface, the everyday workflow of a powder X-ray diffraction (XRD) laboratory:
searching multiple open crystallographic databases, retrieving and managing
Crystallographic Information Files (CIFs), simulating and comparing diffraction
patterns, and visualizing crystal structures in 3D.

Its analysis module, **PhaseDRX**, loads experimental diffractograms, cleans them
(background removal, normalization, smoothing, denoising), simulates patterns from
CIFs and overlays them with the measured data for qualitative phase identification —
including an interactive 3D view of the unit cell.

MatFinder is built in Python on PySide6, `pymatgen`, NumPy/SciPy and Matplotlib; it
runs on Windows, Linux and macOS, and is available in Portuguese, English and German.
It was developed at the Federal University of Amazonas (UFAM), Brazil.

## At a glance

| | |
|---|---|
| **What it is** | Desktop app for crystallographic search + qualitative XRD phase analysis |
| **Analysis module** | PhaseDRX (also available standalone) |
| **Databases** | Materials Project, COD, OQMD, ROD |
| **Built with** | Python · PySide6 · pymatgen · NumPy/SciPy · Matplotlib |
| **Platforms** | Windows (installer) · Linux · macOS (from source) |
| **Interface languages** | Portuguese · English · German |
| **License** | GPL-3.0 (free and open-source) |
| **Download** | [GitHub Releases](https://github.com/SrValentim/MatFinder/releases/latest) — no registration |
| **DOI** | [10.5281/zenodo.20778195](https://doi.org/10.5281/zenodo.20778195) (all versions) |

## Where to go next

<div class="grid cards" markdown>

-   :material-help-circle-outline:{ .lg .middle } __What is MatFinder?__

    ---

    The problem it solves and how the pieces fit together.

    [:octicons-arrow-right-24: Read more](what-is-matfinder.md)

-   :material-target:{ .lg .middle } __Statement of need__

    ---

    Why the tool exists and where it sits among existing software.

    [:octicons-arrow-right-24: Read more](statement-of-need.md)

-   :material-star-four-points:{ .lg .middle } __Key features__

    ---

    A concise map of everything MatFinder can do.

    [:octicons-arrow-right-24: Read more](features.md)

-   :material-download:{ .lg .middle } __Get started__

    ---

    Download, install and run your first analysis.

    [:octicons-arrow-right-24: Get started](../getting-started/index.md)

</div>
