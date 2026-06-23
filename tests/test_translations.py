# -*- coding: utf-8 -*-
"""Sistema de tradução: ptr() (mapa plano) e integridade dos JSONs do tr()."""
import json
import os

from matfinder.core import translator
from matfinder.core.translator import ptr

TRANS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "matfinder", "assets", "translations",
)


def _set_lang(lang):
    translator.get_translator()._current_language = lang


def test_ptr_identity_in_portuguese():
    _set_lang("pt_BR")
    assert ptr("Salvar CIF") == "Salvar CIF"


def test_ptr_translates_english_and_german():
    _set_lang("en_US")
    assert ptr("Salvar CIF") == "Save CIF"
    _set_lang("de_DE")
    assert ptr("Salvar CIF") == "CIF speichern"


def test_ptr_passthrough_unknown_string():
    _set_lang("en_US")
    # string que não está no mapa -> retorna o próprio texto (fallback seguro)
    assert ptr("xyzzy string inexistente 123") == "xyzzy string inexistente 123"


def test_tr_json_files_are_valid_and_consistent():
    data = {}
    for lang in ("pt_BR", "en_US", "de_DE"):
        with open(os.path.join(TRANS_DIR, f"{lang}.json"), encoding="utf-8") as f:
            data[lang] = json.load(f)
    # os três idiomas devem ter os mesmos blocos de topo
    assert set(data["pt_BR"]) == set(data["en_US"]) == set(data["de_DE"])


def test_no_scihub_left_in_translations():
    for lang in ("pt_BR", "en_US", "de_DE"):
        content = open(os.path.join(TRANS_DIR, f"{lang}.json"), encoding="utf-8").read().lower()
        assert "sci-hub" not in content and "scihub" not in content
