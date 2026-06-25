# Quick start

A five-minute tour, from launching MatFinder to identifying a phase. It uses the
worked example shipped in the repository — see [Examples](../examples.md).

!!! tip "Before you start"
    Install MatFinder first (see [Download & Install](index.md)). COD/OQMD/ROD need
    no key; only the Materials Project requires a free
    [API key](index.md#optional-materials-project-api-key).

## 1. Find a structure

1. Launch **MatFinder** (`MatFinder.exe` or `python run_matfinder.py`).
2. Type the elements you are looking for, e.g. `Sm, Fe, O`, and pick a database.
3. Inspect the results — space group, band gap, formation energy and stability are
   shown for each candidate.

## 2. Get the CIF

Right-click a promising result and choose:

- **Download CIF** to save it locally, or
- **Export CIF to PhaseDRX** to send it straight into the analysis module.

## 3. Load your data in PhaseDRX

1. Open **PhaseDRX** (`PhaseDRX.exe`, or *Tools ▸ PhaseDRX* in MatFinder).
2. **Experimental Data → Load Exp. File(s)…** and select your diffractogram(s).
3. Optionally clean the data: **Normalization…**, **Smooth**,
   **Remove Background…** (try SNIP), **Noise Reduction (Wavelet)**.

## 4. Simulate and compare

1. **Theoretical Simulation (from CIF)** → load your CIF(s).
2. Choose a **radiation source** (e.g. Cu Kα) and a maximum 2θ, then
   **Calculate Selected**.
3. **Overlay** the calculated pattern on the experimental data. A good match
   identifies the phase; click a peak to read its 2θ / d-spacing.

## 5. Inspect the structure in 3D

Open the **Crystal Structure (3D)** tab to rotate the unit cell, then **Save Plot…**
to export a publication-ready figure.

---

That's the full loop the tool was built for: **search → get CIF → simulate →
compare → identify**. For a complete worked example with real data, see
[Examples](../examples.md); for guided videos, see
[Tutorials & Videos](../tutorial.md).
