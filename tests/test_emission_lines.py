# -*- coding: utf-8 -*-
"""Linhas de emissão Kα/Kβ da simulação do PhaseDRX (tools/xrd/emission_lines)."""
import math
import os

import numpy as np
import pytest

pytest.importorskip("pymatgen")
from pymatgen.analysis.diffraction.xrd import WAVELENGTHS, XRDCalculator  # noqa: E402
from pymatgen.core import Structure  # noqa: E402

from matfinder.tools.xrd.emission_lines import (  # noqa: E402
    ANODE_LINES, KB_TO_KA1_RATIO, combined_sticks, radiation_lines, same_d_two_theta,
)


@pytest.fixture(scope="module")
def fe_structure(examples_dir):
    return Structure.from_file(os.path.join(examples_dir, "cif", "MP_mpaaaaaaan_Fe_sym.cif"))


def test_wavelengths_match_pymatgen_table():
    for anode, lines in ANODE_LINES.items():
        assert lines["kb"] == pytest.approx(WAVELENGTHS[f"{anode}Kb1"], abs=1e-6)
        # Kα1 do seletor do PhaseDRX (o Co difere do pymatgen na 5ª casa decimal).
        assert lines["ka"] == pytest.approx(WAVELENGTHS[f"{anode}Ka1"], abs=2e-5)


def test_default_is_ka_only():
    assert radiation_lines("Cu") == [(1.54056, 1.0)]


def test_ka_and_kb_with_intensity_ratio():
    assert radiation_lines("Cu", use_ka=True, use_kb=True) == [
        (1.54056, 1.0), (1.39222, KB_TO_KA1_RATIO["Cu"])]


def test_kb_only():
    assert radiation_lines("Mo", use_ka=False, use_kb=True) == [(0.63229, KB_TO_KA1_RATIO["Mo"])]


def test_at_least_one_line_required():
    with pytest.raises(ValueError):
        radiation_lines("Cu", use_ka=False, use_kb=False)


def test_unknown_anode_raises():
    with pytest.raises(ValueError):
        radiation_lines("W")


def test_custom_wavelength_is_single_line_and_ignores_flags():
    assert radiation_lines(custom_wavelength="0.8", use_ka=False, use_kb=False) == [(0.8, 1.0)]
    for bad in ("0", "-1", "nan", "abc"):
        with pytest.raises(ValueError):
            radiation_lines(custom_wavelength=bad)


def test_ka_only_reproduces_previous_simulation(fe_structure):
    """Só Kα: mesmo padrão de antes (XRDCalculator com o λ do seletor, escala 0-100)."""
    legacy = XRDCalculator(wavelength=1.54056).get_pattern(fe_structure, two_theta_range=(0, 100))
    x, y = combined_sticks(fe_structure, radiation_lines("Cu"), 100)
    np.testing.assert_allclose(x, legacy.x)
    np.testing.assert_allclose(y * (100.0 / y.max()), legacy.y)


def test_kb_peaks_follow_bragg_law(fe_structure):
    lam_a, lam_b = ANODE_LINES["Cu"]["ka"], ANODE_LINES["Cu"]["kb"]
    xa, _ = combined_sticks(fe_structure, [(lam_a, 1.0)], 100)
    xb, _ = combined_sticks(fe_structure, [(lam_b, 1.0)], 100)
    # Primeira reflexão (110 do Fe-α): sen(θβ)/sen(θα) = λβ/λα, com o Kβ em ângulo menor.
    ratio = math.sin(math.radians(xb[0] / 2)) / math.sin(math.radians(xa[0] / 2))
    assert ratio == pytest.approx(lam_b / lam_a, rel=1e-6)
    assert xb[0] < xa[0]


def test_both_lines_are_summed_with_weight(fe_structure):
    lam_a, lam_b = ANODE_LINES["Cu"]["ka"], ANODE_LINES["Cu"]["kb"]
    xa, ya = combined_sticks(fe_structure, [(lam_a, 1.0)], 100)
    xb, yb = combined_sticks(fe_structure, [(lam_b, 1.0)], 100)
    x, y = combined_sticks(fe_structure, radiation_lines("Cu", use_ka=True, use_kb=True), 100)
    assert len(x) == len(xa) + len(xb)
    assert np.all(np.diff(x) >= 0)  # ordenado por 2θ
    assert y.sum() == pytest.approx(ya.sum() + KB_TO_KA1_RATIO["Cu"] * yb.sum())


def test_combined_sticks_requires_lines(fe_structure):
    with pytest.raises(ValueError):
        combined_sticks(fe_structure, [], 100)


def test_ka2_wavelengths_match_pymatgen_table():
    for anode, lines in ANODE_LINES.items():
        assert lines["ka2"] == pytest.approx(WAVELENGTHS[f"{anode}Ka2"], abs=1e-6)


def test_same_d_two_theta_between_lines():
    lam1, lam2 = ANODE_LINES["Cu"]["ka"], ANODE_LINES["Cu"]["ka2"]
    t2 = same_d_two_theta(88.4, lam1, lam2)
    assert t2 == pytest.approx(88.677, abs=1e-3)       # Kα2 de 88,4° (Cu)
    assert same_d_two_theta(t2, lam2, lam1) == pytest.approx(88.4, abs=1e-9)
    assert math.isnan(same_d_two_theta(170.0, 1.0, 1.2))  # sen θ > 1: não existe
    assert np.allclose(same_d_two_theta(np.array([30.0, 60.0]), lam1, lam1), [30.0, 60.0])
