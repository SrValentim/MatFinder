# -*- coding: utf-8 -*-
"""Normalização de DOI (acesso aberto). Sem rede."""
from matfinder.core.api_logic import _normalize_doi


def test_normalize_doi_strips_prefixes_and_whitespace():
    expected = "10.1371/journal.pone.0000308"
    variants = [
        "10.1371/journal.pone.0000308",
        "https://doi.org/10.1371/journal.pone.0000308",
        "http://doi.org/10.1371/journal.pone.0000308",
        "https://dx.doi.org/10.1371/journal.pone.0000308",
        "doi:10.1371/journal.pone.0000308",
        "DOI:10.1371/journal.pone.0000308",
        "  10.1371/journal.pone.0000308  ",
    ]
    for v in variants:
        assert _normalize_doi(v) == expected
