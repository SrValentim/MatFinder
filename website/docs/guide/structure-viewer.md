# 3D structure viewer

The **Crystal Structure (3D)** tab renders the unit cell of a loaded CIF as an
interactive 3D model.

## What it shows

- **Atomic positions**, converted from fractional to Cartesian coordinates using the
  lattice matrix.
- **Bond distances**, computed with periodic boundary conditions.
- **Lattice parameters** and the unit-cell edges.
- **Space group** and crystal system, preserved from the CIF.

All geometric quantities come directly from `pymatgen`, the de-facto standard library
for crystal-structure manipulation in materials science.

## Interacting

- **Rotate** and **zoom** the cell to inspect coordination and geometry.
- Read lattice parameters and bond lengths.
- **Save Plot…** to export a figure for a report or paper.

!!! note "About atom radii"
    The sphere radii used to draw atoms are tabulated, approximate values for
    **visualization only**. They are adjustable via a scale factor and do **not**
    affect atomic positions, bond distances or any computed quantity.

## Scope

The viewer is intended for accurate visualization and inspection of crystal
structures. It does not compute electronic properties or run molecular dynamics —
those are outside the scope of MatFinder.
