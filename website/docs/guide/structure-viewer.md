# 3D structure viewer

The **Structure** tab renders the unit cell of a loaded CIF as an interactive 3D model.

## What it shows

- **Atomic positions**, converted from fractional to Cartesian coordinates using the
  lattice matrix.
- **Complete unit cell**: atoms on faces, edges and corners are drawn at all their
  boundary images, and bonded neighbours just outside the cell are included so that rings
  and coordination polyhedra are closed (the convention used by VESTA and Mercury). The
  atomic positions are not altered.
- **Bonds**, computed with periodic boundary conditions and drawn as two-colour sticks
  (half the colour of each connected atom).
- **Lattice parameters** and the unit-cell edges.
- **Space group** and crystal system, preserved from the CIF.

All geometric quantities come directly from `pymatgen`.

## Interacting

- **Rotate** and **zoom** to inspect coordination and geometry.
- **Measure interatomic distances**: double-click one atom and then another — a dashed
  line is drawn and the distance is labelled in Å at its midpoint. Right-click clears the
  measurements.
- **Orient the camera** along the crystallographic axes with the **a**, **b** and **c**
  buttons, or return to an isometric view.
- **Save Plot…** to export a figure for a report or paper.

!!! note "About atom radii"
    The sphere radii used to draw atoms are tabulated, approximate values for
    visualization only. They are adjustable via a scale factor and do **not** affect
    atomic positions, bond distances or any computed quantity.

## Scope

The viewer is intended for visualization and inspection of crystal structures. It does
not compute electronic properties or run molecular dynamics.
