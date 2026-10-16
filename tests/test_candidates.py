# -*- coding: utf-8 -*-
"""Candidatos do search-match (tools/xrd/search_match/candidates) sem acesso à rede."""
import json
import os

import pytest
import requests

from matfinder.tools.xrd.search_match import candidates as cm
from matfinder.tools.xrd.search_match.candidates import (
    Candidate, ElementFilter, clean_spacegroup, cod_query_plans, fetch_cod_cifs, formula_elements,
    group_duplicates, mp_query_kwargs, pretty_formula, search_cod, search_mp,
)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MATFINDER_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(cm.time, "sleep", lambda s: None)


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text if payload is None else json.dumps(payload)
        self.content = self.text.encode()

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class FakeSession:
    """Responde por rota; pode falhar nas primeiras chamadas HTTPS."""

    def __init__(self, routes, fail_https=0):
        self.routes = routes
        self.fail_https = fail_https
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(url)
        if url.startswith("https://") and self.fail_https > 0:
            self.fail_https -= 1
            raise requests.ConnectionError("TLS derrubado")
        for suffix, response in self.routes.items():
            if url.endswith(suffix):
                return response
        return FakeResponse(404)


COD_ROWS = [
    {"file": "9009008", "formula": "- Ce O2 -", "sg": "F m -3 m", "sgNumber": "225", "a": "5.411", "b": "5.411",
     "c": "5.411", "alpha": "90", "beta": "90", "gamma": "90", "flags": "has coordinates", "year": "1999"},
    {"file": "1010279", "formula": "- Ce2 O3 -", "sg": "P 3 2 1", "sgNumber": "150", "a": "3.88", "b": "3.88",
     "c": "6.06", "alpha": "90", "beta": "90", "gamma": "120", "flags": "has coordinates"},
    {"file": "1111111", "formula": "- Ce O2 -", "sg": "F m -3 m", "flags": ""},                    # sem coordenadas
    {"file": "2222222", "formula": "- Ce O2 Zr -", "sg": "F m -3 m", "flags": "has coordinates"},  # Zr não permitido
]


def test_element_filter_rules():
    flt = ElementFilter(required=["O", "Ce"], possible=["Zr", "Ce"], forbidden=["H"])
    assert flt.required == ["Ce", "O"] and flt.possible == ["Zr"]
    assert flt.validate() is None
    assert flt.allows(["Ce", "O"]) and flt.allows(["Ce", "O", "Zr"])
    assert not flt.allows(["Ce"])                 # falta obrigatório
    assert not flt.allows(["Ce", "O", "Fe"])      # sistema fechado
    assert ElementFilter(required=["Ce", "O"], allow_others=True).allows(["Ce", "O", "Fe"])
    assert not ElementFilter(required=["Ce"], forbidden=["O"], allow_others=True).allows(["Ce", "O"])
    assert flt.chemsys_list() == ["Ce-O", "Ce-O-Zr"]
    assert ElementFilter.from_dict(flt.to_dict()) == flt


def test_element_filter_validation_messages():
    assert ElementFilter(possible=["O"]).validate()
    assert ElementFilter(required=["Ce"], forbidden=["Ce"]).validate()
    assert ElementFilter(required=list("BCNOFPSKVY")[:9]).validate()  # 9 obrigatórios: acima do limite do COD


def test_formula_and_spacegroup_helpers():
    assert formula_elements("- Ce2 O3 -") == ["Ce", "O"]
    assert pretty_formula("- Nb16.8 O42 -") == "Nb2O5"
    assert pretty_formula("- Fe2.94 O4 -") == "Fe2.94O4"
    assert clean_spacegroup("P 1 21/c 1") == "P21/c"
    assert clean_spacegroup("F m -3 m") == "Fm-3m"
    assert clean_spacegroup("P 1") == "P1"


def test_cod_query_plans():
    plans = cod_query_plans(ElementFilter(required=["O"], possible=["Sm", "Fe"]))
    systems = sorted("-".join(p[k] for k in sorted(p) if k.startswith("el")) for p in plans)
    assert systems == ["Fe-O", "Fe-O-Sm", "O", "O-Sm"]          # uma consulta exata por sistema
    assert all(p["strictmin"] == p["strictmax"] for p in plans)
    (opened,) = cod_query_plans(ElementFilter(required=["Ce"], forbidden=["H"], allow_others=True))
    assert opened["el1"] == "Ce" and opened["nel1"] == "H" and opened["strictmax"] == 3


def test_search_cod_filters_rows_and_uses_cache():
    session = FakeSession({"/cod/result": FakeResponse(payload=COD_ROWS)})
    flt = ElementFilter(required=["Ce", "O"])
    found = search_cod(flt, session=session)
    assert [c.source_id for c in found] == ["9009008", "1010279"]
    assert found[0].formula == "CeO2" and found[0].spacegroup == "Fm-3m" and found[0].sg_number == 225
    assert found[0].cell[0] == pytest.approx(5.411)
    calls = len(session.calls)
    search_cod(flt, session=session)          # segunda vez: cache
    assert len(session.calls) == calls


def test_cod_falls_back_to_http_when_https_fails():
    session = FakeSession({"/cod/result": FakeResponse(payload=COD_ROWS[:1])}, fail_https=10)
    found = search_cod(ElementFilter(required=["Ce", "O"]), session=session)
    assert len(found) == 1
    assert any(url.startswith("http://") for url in session.calls)


def test_fetch_cod_cifs_downloads_once_and_reports_errors(example_cifs):
    cif_text = open(example_cifs[0], encoding="utf-8").read()
    session = FakeSession({"/cod/9009008.cif": FakeResponse(text=cif_text)})
    cands = [Candidate("COD", "9009008", "CeO2"), Candidate("COD", "404404", "X")]
    fetch_cod_cifs(cands, session=session)
    assert cands[0].cif == cif_text
    assert cands[1].cif is None and cands[1].error
    again = [Candidate("COD", "9009008", "CeO2")]
    calls = len(session.calls)
    fetch_cod_cifs(again, session=session)    # vem do cache em disco
    assert again[0].cif == cif_text and len(session.calls) == calls


def test_mp_query_kwargs():
    closed = mp_query_kwargs(ElementFilter(required=["Fe", "O"], possible=["Sm"]), True, 0.1)
    assert closed["chemsys"] == ["Fe-O", "Fe-O-Sm"] and closed["theoretical"] is False
    assert closed["energy_above_hull"] == (0.0, 0.1)
    opened = mp_query_kwargs(ElementFilter(required=["Fe"], forbidden=["H"], allow_others=True), False, None)
    assert opened == {"elements": ["Fe"], "exclude_elements": ["H"]}


class _Doc:
    def __init__(self, mid, structure, formula, elements):
        self.material_id = mid
        self.structure = structure
        self.formula_pretty = formula
        self.elements = elements
        self.symmetry = type("Sym", (), {"symbol": "Pnma", "number": 62})()
        self.energy_above_hull = 0.0
        self.theoretical = False
        self.database_IDs = {"icsd": ["icsd-1"]}


class _FakeRester:
    def __init__(self, docs):
        self.docs = docs
        self.kwargs = None
        outer = self

        class Summary:
            def search(self, **kwargs):
                outer.kwargs = kwargs
                return outer.docs
        self.materials = type("Materials", (), {"summary": Summary()})()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_search_mp_with_fake_rester(example_cifs):
    from pymatgen.core import Structure
    path = next(p for p in example_cifs if "SmFeO3" in p)
    doc = _Doc("mp-123", Structure.from_file(path), "SmFeO3", ["Sm", "Fe", "O"])
    rester = _FakeRester([doc])
    found = search_mp(ElementFilter(required=["Sm", "Fe", "O"]), "chave", rester_factory=lambda: rester)
    assert len(found) == 1 and found[0].source == "MP" and found[0].cif.startswith("#")
    assert rester.kwargs["chemsys"] == ["Fe-O-Sm"] and "structure" in rester.kwargs["fields"]
    assert found[0].url.endswith("/mp-123")


def test_group_duplicates_keeps_best_representative():
    a = Candidate("COD", "1", "CeO2", spacegroup="Fm-3m", sg_number=225, cell=(5.41, 5.41, 5.41, 90, 90, 90), score=98)
    b = Candidate("COD", "2", "CeO2", spacegroup="Fm-3m", sg_number=225, cell=(5.42, 5.42, 5.42, 90, 90, 90), score=95)
    c = Candidate("MP", "mp-1", "CeO2", spacegroup="Fm-3m", sg_number=225, score=90)
    d = Candidate("COD", "3", "CeO2", spacegroup="P1", sg_number=1, score=70)
    reps = group_duplicates([a, b, c, d])
    assert [r.source_id for r in reps] == ["1", "3"]
    assert reps[0].group_members == ["COD:2", "MP:mp-1"]


def test_find_mp_api_key_from_env(monkeypatch):
    monkeypatch.setenv("MP_API_KEY", "x" * 32)
    assert cm.find_mp_api_key() == "x" * 32
    monkeypatch.delenv("MP_API_KEY")
    monkeypatch.setenv("LOCALAPPDATA", os.path.dirname(os.environ["MATFINDER_CACHE_DIR"]))
    monkeypatch.chdir(os.path.dirname(os.environ["MATFINDER_CACHE_DIR"]))
    assert cm.find_mp_api_key() in (None,) or len(cm.find_mp_api_key()) >= 16
