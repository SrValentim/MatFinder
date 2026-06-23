# -*- coding: utf-8 -*-
"""Calculadora estequiométrica (massa molar, conversões)."""
from matfinder.tools.calculator import quimica_calc as qc


def test_parse_formula_water():
    d = qc.parse_formula("H2O")
    assert d.get("H") == 2.0
    assert d.get("O") == 1.0


def test_molar_mass_water():
    assert abs(qc.calcular_massa_molar("H2O") - 18.015) < 0.05


def test_molar_mass_from_dict():
    # FeO ~ 55.845 + 15.999
    assert abs(qc.calcular_massa_molar({"Fe": 1.0, "O": 1.0}) - 71.84) < 0.2


def test_molar_mass_invalid_input():
    assert qc.calcular_massa_molar(12345) == 0.0


def test_moles_particles_roundtrip():
    na = qc.moles_para_particulas(1.0)  # constante de Avogadro usada pelo app
    assert 6.0e23 < na < 6.1e23
    assert abs(qc.moles_para_particulas(2.0) - 2 * na) / na < 1e-6
    assert abs(qc.particulas_para_moles(na) - 1.0) < 1e-6


def test_mass_moles_roundtrip():
    mm = qc.calcular_massa_molar("H2O")
    moles = qc.massa_para_moles(mm, "H2O")
    assert abs(moles - 1.0) < 1e-3
    massa = qc.moles_para_massa(1.0, "H2O")
    assert abs(massa - mm) < 0.01
