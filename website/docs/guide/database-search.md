# Database search

MatFinder searches several open crystallographic databases from a single interface,
built on top of `pymatgen`.

## Supported databases

| Database | Needs key | Notes |
|---|---|---|
| **Materials Project** | Yes (free) | Computed structures and properties |
| **COD** — Crystallography Open Database | No | Experimental structures, open |
| **OQMD** — Open Quantum Materials Database | No | Computed thermodynamics |
| **ROD** — Raman Open Database | No | Raman + structural data |

See [API key setup](../getting-started/index.md#optional-materials-project-api-key)
for the Materials Project.

## Running a search

1. Enter the elements of interest, comma-separated (e.g. `Sm, Fe, O`).
2. Choose the database.
3. Run the search and browse the results table.

## Reading the results

Each result row can show:

- **Formula** and **space group**
- **Crystal system** and lattice parameters
- **Band gap**
- **Formation energy**
- **Thermodynamic stability** (e.g. energy above hull)
- Source **reference** / database ID

## Acting on a result

Right-click a row to:

- **Download CIF** (symmetrized, conventional or primitive, where available)
- **Export CIF to PhaseDRX** for immediate analysis
- **Open in the browser** on the source database
- **Copy** the ID, formula or full row
- **Add to favorites**

## Favorites & history

Mark candidates as **favorites** to compare them later, and revisit past queries from
the **search history**. Both persist between sessions.
