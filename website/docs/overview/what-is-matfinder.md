# What is MatFinder?

MatFinder is a desktop application for **searching, visualizing and analyzing
crystalline material structures**. It brings together, in one place, the steps a
researcher normally has to perform across several disconnected programs when
identifying the phases present in a powder sample.

## The workflow it covers

A typical powder-XRD identification loop looks like this:

1. **Measure** a sample and obtain a diffractogram.
2. **Search** crystallographic databases for candidate structures.
3. **Retrieve** the corresponding CIF files.
4. **Simulate** the diffraction pattern of each candidate.
5. **Compare** the simulated patterns against the experimental data.
6. **Repeat** at every synthesis step, often in a time series.

MatFinder turns this multi-program, multi-window loop into a single, fast workflow:

```
Search databases  →  Get CIF  →  Simulate pattern  →  Compare  →  Identify
        (MatFinder)                       (PhaseDRX)
```

## The two parts

### MatFinder — search & discovery

The main application searches the **Materials Project**, **COD**, **OQMD** and
**ROD** databases, shows crystallographic and thermodynamic properties for each
result, and downloads or exports CIF files. It also includes auxiliary tools: a CIF
editor, a stoichiometric calculator, an interactive periodic table, and open-access
article retrieval by DOI.

### PhaseDRX — analysis & identification

PhaseDRX is the X-ray diffraction analysis module (also shipped as a standalone
`PhaseDRX.exe`). It loads experimental diffractograms — including whole time series —
cleans them, simulates patterns from CIF files, overlays them with the measured data,
and provides an interactive 3D viewer of the crystal structure.

## Who it is for

- **Students and researchers** doing materials synthesis and characterization who
  need a fast, integrated phase-identification workflow.
- **Laboratories** that want an **open-source** alternative to closed/commercial
  packages, without licensing costs.
- **Teaching**, where an integrated, visual tool lowers the barrier to learning
  crystallography and powder diffraction.

## What it is *not*

MatFinder focuses on **qualitative** phase identification and the discovery loop. It
is **not** a Rietveld refinement engine (tools such as GSAS-II or BGMN/Profex cover
that) nor a 2D detector data-reduction package. See the
[Statement of need](statement-of-need.md) for how it relates to existing tools.
