# MatFinder — Examples

Sample data to try MatFinder and its XRD suite **PhaseDRX** end to end, and to
reproduce a real phase-identification workflow. The same files are reused as
fixtures by the automated tests (see [`../tests/`](../tests/)).

## Contents

- **`cif/`** — three reference structures (symmetrized CIFs from the Materials Project):
  - `MP_mpaaaabdyp_SmFeO3_sym.cif` — the target phase, **SmFeO₃**
  - `MP_mpaaaaacpd_Sm2O3_sym.cif` — **Sm₂O₃** (a possible secondary phase)
  - `MP_mpaaaaaaan_Fe_sym.cif` — metallic **Fe** (a possible precursor)
- **`experimental/SmFeO3/`** — a real powder-XRD **time series** of an SmFeO₃ synthesis,
  measured at 1, 5, 10, 12, 14, 16, 18, 20, 22 and 24 h. Each `.dat` is 2θ vs. intensity.

The scientific question: *as the synthesis progresses (1 h → 24 h), do the precursor/
secondary phases disappear and the SmFeO₃ phase form?*

## Tutorial A — analyze and identify phases (PhaseDRX)

1. Launch **PhaseDRX** — run `PhaseDRX.exe`, or open it from MatFinder
   (*Tools ▸ PhaseDRX*), or from source: `python run_phasedrx.py`. Choose
   **Continue in Anonymous Session**.
2. **Experimental Data** tab → **Load Exp. File(s)…** → select all `.dat` files in
   `examples/experimental/SmFeO3/`. They appear stacked in the **Diffractogram (2D)** view.
3. *(optional)* Clean the data: **Normalization…**, **Smooth**, **Remove Background…**
   (try SNIP), **Noise Reduction (Wavelet)**.
4. **Theoretical Simulation (from CIF)** tab → **Load CIF File(s)…** → select the three
   CIFs in `examples/cif/`. Pick a **radiation source** (e.g., Cu Kα) and a maximum 2θ,
   then **Calculate Selected**.
5. **Compare:** overlay the calculated patterns on the experimental series. The
   **SmFeO₃** pattern should match the late-time curves; **Fe** and **Sm₂O₃** help you
   spot precursor/secondary phases at early times. Click a peak to read its 2θ / d-spacing.
6. **Crystal Structure (3D)** tab → rotate the SmFeO₃ unit cell.
7. **Save Plot…** to export a publication-ready figure.

## Tutorial B — get a CIF from a database (MatFinder)

1. Launch **MatFinder** (`MatFinder.exe` or `python run_matfinder.py`).
2. Search elements **`Sm, Fe, O`** in **Materials Project** (needs a free API key,
   set in *Settings ▸ Materials Project Key…*) or in **COD/OQMD** (no key required).
3. Right-click a result → **Download CIF (MP)** to save it, or
   **Export CIF to PhaseDRX** to send it straight into the analysis window.

That's the full loop the tool was built for: search → get CIF → simulate → compare →
identify — without juggling separate programs.
