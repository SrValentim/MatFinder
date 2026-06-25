# Tutorials & Videos

Short, practical guides to the main MatFinder workflows. Three feature videos are
planned — the slots are ready below.

!!! info "How to add a video"
    Upload your screen recording to YouTube (an **Unlisted** video is enough — it
    won't appear in search but anyone with the link can watch). Then replace the
    placeholder note in each section with this snippet, swapping `VIDEO_ID` for the
    id in your video URL (`https://youtu.be/VIDEO_ID`):

    ```html
    <div class="video-wrapper" markdown>
    <iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID"
            title="MatFinder tutorial" allowfullscreen></iframe>
    </div>
    ```

    The `.video-wrapper` styling makes the player fully responsive on phones and
    desktops automatically.

---

## 1. Search a database and get a CIF

!!! note "🎬 Video 1 — placeholder"
    *Workflow to record:* search elements (e.g. `Sm, Fe, O`) in the Materials Project
    / COD, inspect results, and download or export a CIF.
    Replace this note with the embed snippet above.

**Steps**

1. Launch **MatFinder** (`MatFinder.exe` or `python run_matfinder.py`).
2. Type the elements (e.g. `Sm, Fe, O`) and choose a database.
   COD/OQMD/ROD need no key; Materials Project needs a free
   [API key](install.md#optional-materials-project-api-key).
3. Right-click a result → **Download CIF** or **Export CIF to PhaseDRX**.

---

## 2. Analyze a diffractogram with PhaseDRX

!!! note "🎬 Video 2 — placeholder"
    *Workflow to record:* load experimental `.dat` files, clean them
    (background removal, smoothing, denoising), simulate patterns from CIFs and
    overlay them for phase identification.
    Replace this note with the embed snippet above.

**Steps**

1. Open **PhaseDRX** (`PhaseDRX.exe`, or *Tools ▸ PhaseDRX* in MatFinder).
2. **Experimental Data** → **Load Exp. File(s)…** and select your diffractograms.
3. Clean the data: **Normalization…**, **Smooth**, **Remove Background…** (try SNIP),
   **Noise Reduction (Wavelet)**.
4. **Theoretical Simulation (from CIF)** → load CIFs, pick a radiation source and a
   maximum 2θ, then **Calculate Selected**.
5. **Compare:** overlay the calculated patterns on the experimental data and read
   each peak's 2θ / d-spacing.

---

## 3. Explore the crystal structure in 3D

!!! note "🎬 Video 3 — placeholder"
    *Workflow to record:* open the **Crystal Structure (3D)** tab, rotate the unit
    cell, and export a publication-ready figure.
    Replace this note with the embed snippet above.

**Steps**

1. In PhaseDRX, open the **Crystal Structure (3D)** tab.
2. Rotate and zoom the unit cell; atom positions and bond distances come from
   `pymatgen`.
3. Use **Save Plot…** to export a figure.

---

For a full worked example with real data, see [Examples](examples.md).
