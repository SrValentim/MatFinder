# Statement of need

A recurring bottleneck in materials synthesis–characterization loops is the
**fragmentation of the qualitative phase-analysis workflow**. After measuring a
sample, a researcher typically converts the instrument file to a plottable format in
one program, plots it in another, and then hunts for candidate structures across
several disconnected databases — converting and re-plotting each candidate by trial
and error until a phase is identified, and repeating the whole cycle at every
synthesis step.

Much of the effort is spent on format conversion, switching between programs that do
not talk to each other, and searching for CIFs scattered across the web — often only
to discover that a candidate was wrong and start over.

## What MatFinder does about it

MatFinder was created to remove this friction. It integrates, in one place:

- search across the **Materials Project**, the **Crystallography Open Database
  (COD)**, the **Open Quantum Materials Database (OQMD)** and the **Raman Open
  Database (ROD)**;
- CIF retrieval and management;
- literature lookup by DOI; and
- the simulation and comparison of diffraction patterns,

turning a multi-program, multi-minute loop into a single, fast workflow.

## Where it sits among existing tools

Existing tools tend to be either **closed/commercial** (e.g. Match!, HighScore) or
focused on a **single step** of the process — `VESTA` for structure visualization,
`GSAS-II` or BGMN/`Profex` for Rietveld refinement, `Dioptas`/`pyFAI` for 2D data
reduction.

MatFinder instead targets the **integrated discovery-to-identification loop**, using
open databases and an open (GPL-3.0) license, which lowers the barrier for students
and laboratories without access to commercial software.

!!! note "Honest scope"
    MatFinder is complementary to — not a replacement for — refinement engines and
    dedicated visualizers. Its contribution is **integration, breadth of input
    sources, and accessibility**, not automated search-match against a reference
    database (a capability on the roadmap).
