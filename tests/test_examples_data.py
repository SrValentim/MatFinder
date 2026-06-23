# -*- coding: utf-8 -*-
"""Valida os dados de exemplo (examples/): CIFs e difratogramas .dat."""
from pymatgen.core import Structure


def test_example_cifs_parse(example_cifs):
    assert len(example_cifs) >= 3
    for path in example_cifs:
        structure = Structure.from_file(path)
        assert len(structure) > 0  # tem átomos


def test_smfeo3_cif_has_expected_elements(example_cifs):
    target = [c for c in example_cifs if "SmFeO3" in c]
    assert target, "CIF de SmFeO3 não encontrado em examples/cif/"
    structure = Structure.from_file(target[0])
    elements = {str(e) for e in structure.composition.elements}
    assert {"Sm", "Fe", "O"} <= elements


def test_experimental_dat_files_are_increasing_xrd(example_dat):
    assert len(example_dat) >= 10  # série temporal completa
    for path in example_dat[:3]:
        rows = []
        for line in open(path, encoding="utf-8", errors="ignore"):
            parts = line.replace(",", ".").split()
            try:
                rows.append((float(parts[0]), float(parts[1])))
            except (ValueError, IndexError):
                continue  # pula cabeçalho/linhas não numéricas
        assert len(rows) > 100
        xs = [r[0] for r in rows]
        assert xs == sorted(xs)         # 2θ crescente
        assert all(r[1] >= 0 for r in rows)  # intensidades não negativas
