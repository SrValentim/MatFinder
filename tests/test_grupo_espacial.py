# -*- coding: utf-8 -*-
"""Tabela de grupos espaciais (dados de cristalografia)."""
from matfinder.core import grupo_espacial as ge


def test_has_all_230_space_groups():
    numeros = {g["numero"] for g in ge.LISTA_GRUPOS_ESPACIAIS}
    assert numeros == set(range(1, 231))


def test_entries_have_required_fields():
    for g in ge.LISTA_GRUPOS_ESPACIAIS:
        assert "numero" in g
        assert g.get("simbolo_hm")          # símbolo Hermann-Mauguin não vazio
        assert g.get("sistema_cristalino")  # sistema cristalino não vazio


def test_crystal_systems_are_known():
    known = {
        "Triclínico", "Monoclínico", "Ortorrômbico", "Tetragonal",
        "Trigonal", "Romboédrico", "Hexagonal", "Cúbico",
    }
    systems = {g["sistema_cristalino"] for g in ge.LISTA_GRUPOS_ESPACIAIS}
    assert systems  # não vazio
    assert systems <= known
    assert "Monoclínico" in systems
