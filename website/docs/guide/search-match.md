# Phase identification (search-match)

PhaseDRX can identify the crystalline phases in a diffractogram, in the style of
search-match programs such as PANalytical HighScore. The workflow uses two tabs:

- **Peaks** builds a reliable peak list from the measured pattern.
- **Identification** searches candidate structures in the
  [Crystallography Open Database (COD)](https://www.crystallography.net/) and the
  [Materials Project](https://next-gen.materialsproject.org/), scores them against the
  peak list, and lets you accept phases one at a time.

!!! note "Identification, not refinement"
    Search-match tells you *which* phases are present. It does not refine lattice
    parameters or crystal structures.

## 1. Find the peaks

Open the **Peaks** tab, pick the diffractogram and click **Search peaks**.

- **Data type** presets: *Standard*, *Noisy data* and *Broad peaks / amorphous*. The
  broad mode separates amorphous halos and estimates the crystallinity.
- The search fits each peak with an asymmetric pseudo-Voigt profile, including the
  Kα2 doublet when the data contain it, and flags possible Kβ peaks.
- The table lists 2θ (with its uncertainty), d-spacing, relative intensity, height,
  area, FWHM and significance.

You can correct the list before identifying:

- **Add peak** and click on the plot to fit a peak the search missed.
- **Delete peak** removes a peak from the list only. The measured data never change.
- Deleted peaks stay deleted in a new search until you click **Restore deleted**.
- **Export CSV...** saves the list. The list is stored in the project and supports
  undo/redo.

## 2. Choose the elements

In the **Identification** tab, click **Choose elements...** to open a periodic table
with three states per element:

| State | Meaning |
|---|---|
| Required | Every candidate must contain this element. |
| Possible | Candidates may contain it. |
| Forbidden | Candidates containing it are excluded. |

Leave *Allow other elements besides the marked ones* unchecked for a closed system,
where candidates may only contain required or possible elements.

## 3. Search the candidates

Choose the sources and click **Search candidates**.

- **COD** needs no account.
- **Materials Project** needs your API key, configured in MatFinder. With
  *experimental only* checked, only structures linked to an experimental (ICSD) entry
  are used.

Each candidate is simulated and scored from 0 to 100. The score combines the peak
positions, the strong reflections that were found (only those expected above the
noise), the share of the observed intensity it explains, and the intensity agreement.
The zero shift and a small lattice scale are aligned for every candidate, with a wider
range for the computed (DFT) structures of the Materials Project.

The **Scoring** option sets how candidates are ranked:

| Mode | Use |
|---|---|
| Automatic | Peaks only when the peak list is good; peaks and full profile when there are few or broad peaks. |
| Peaks | Peak list only. |
| Profile | Fits each candidate's simulated pattern to the background-subtracted diffractogram. Useful for noisy or nanocrystalline data. |
| Peaks and profile | Geometric mean of both. |

Select a row to preview its reflections on the plot: matched lines in blue, expected
but missing lines dashed in red, weak lines dotted in grey. Entries of the same phase
are grouped, and **Open at source** shows the entry on the COD or Materials Project
website.

## 4. Accept phases

Select the best candidate and click **Accept phase**. PhaseDRX then:

1. fits the scales of all accepted phases together to the peak heights;
2. computes the intensity each peak still lacks;
3. rescores the remaining candidates against that leftover intensity, with the zero
   shift anchored to the accepted phases.

A phase that only repeats peaks already explained drops in the list, and a minor
phase hidden under the main one rises. Repeat until the leftover peaks are explained.

The **Accepted phases** table shows each phase's colour, score, mass fraction, scale
and the number of peaks it explains best. The summary line reports how much of the
peak intensity is explained, how many peaks have no phase, and the global zero shift.
On the plot, the reflections of each accepted phase use its colour, every peak takes
the colour of the phase that explains it best, and peaks without a phase get a red
ring.

!!! info "Mass fractions are an estimate"
    The mass fraction uses the reference intensity ratio (RIR, I/I<sub>corundum</sub>)
    computed from each structure. Texture, microabsorption and amorphous content are not
    taken into account, so treat it as semi-quantitative.

**Remove phase** (or the Delete key) takes a phase out and rescores the candidates.
Accepting and removing phases supports undo/redo, and the accepted phases are saved in
the project together with their CIFs, so a project reopens without network access.

## 5. Send the phases to the list

**Send accepted phases to the list** loads the CIFs of the accepted phases into the
simulation tab and creates a multiphase combination weighted by the fitted scales. You
can then compare the simulated mixture with the measured pattern, as described in
[Analysis (PhaseDRX)](analysis.md).

---

Downloaded structures, simulated patterns and query results are cached locally, so a
repeated search is much faster.
