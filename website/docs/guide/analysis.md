# Analysis (PhaseDRX)

**PhaseDRX** is MatFinder's X-ray diffraction analysis module. It can be opened from
MatFinder (*Tools ▸ PhaseDRX*) or run as a standalone application (`PhaseDRX.exe`).

## 1. Load experimental data

Use **Experimental Data → Load Exp. File(s)…** to import one or more diffractograms.
Multiple files are stacked in the **Diffractogram (2D)** view, which makes it easy to
follow a **time series** (for example, a synthesis sampled at several reaction times).

## 2. Clean the data

PhaseDRX includes validated signal-processing tools:

- **Background removal**
    - **SNIP** — Statistics-sensitive Non-linear Iterative Peak-clipping
    - **arPLS** — asymmetrically reweighted penalized least squares
    - **Polynomial** and **spline**
- **Normalization** (several methods)
- **Smoothing** — Savitzky–Golay
- **Denoising** — wavelet
- **Peak detection**

!!! info "Method validation"
    The background-removal and denoising methods are validated against primary
    references and compared with established software; the methodology is documented
    in the repository under `docs/dev/`. The goal of these tools is to keep genuine
    diffraction peaks while removing background and noise.

## 3. Simulate patterns from CIF

In **Theoretical Simulation (from CIF)**, load one or more CIF files, choose a
**radiation source** (e.g. Cu Kα) and a maximum 2θ, then **Calculate Selected**. The
simulated pattern is computed with `pymatgen`.

## 4. Compare and identify

Overlay the calculated patterns on the experimental data:

- A matching pattern identifies a **phase**.
- In a time series, you can watch precursor/secondary phases disappear and the target
  phase form.
- Click any peak to read its **2θ**, **intensity** and **d-spacing**.

## 5. Export

Use **Save Plot…** to export a publication-ready figure of the comparison.

---

Next: inspect the structure in the [3D viewer](structure-viewer.md), or follow the
[guided video tutorials](../tutorial.md).
