# -*- coding: utf-8 -*-
"""Fase 3 do search-match: fases aceitas, resíduo, perfil, RIR e refino de rede."""
import json
import os

import numpy as np
import pytest

from xrd_synthetic import CU_KA1, CU_KA2, make_pattern, peaks_from_sticks
from matfinder.tools.xrd.search_match.candidates import Candidate
from matfinder.tools.xrd.search_match.peak_search import search_peaks
from matfinder.tools.xrd.search_match.phase_analysis import (
    AcceptedPhase, analyze, effective_mode, next_color, quantify_accepted, rescore,
)
from matfinder.tools.xrd.search_match.quantify import (
    build_profile_context, profile_score, rir_of, semi_quant,
)
from matfinder.tools.xrd.search_match.scoring import ObservedPeaks, ScoreSettings, reference_pattern, score_candidate


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MATFINDER_CACHE_DIR", str(tmp_path / "cache"))


def cif_of(example_cifs, name):
    return open(next(p for p in example_cifs if name in os.path.basename(p)), encoding="utf-8").read()


def candidate(example_cifs, name, source="COD", sid="1"):
    cif = cif_of(example_cifs, name)
    cand = Candidate(source, sid, name.strip("_"), cif=cif)
    cand.reference = reference_pattern(cif, CU_KA1, (10, 90))
    return cand


def mixture(example_cifs, scales=(10.0, 4.0)):
    """Picos de uma mistura SmFeO3 + Sm2O3 (alturas = escala × intensidade de referência)."""
    a = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    b = reference_pattern(cif_of(example_cifs, "Sm2O3"), CU_KA1, (10, 90))
    tt = np.concatenate([a.two_theta, b.two_theta])
    weighted = np.concatenate([a.intensity * scales[0], b.intensity * scales[1]])
    return peaks_from_sticks(tt, weighted, height_per_unit=1.0, min_intensity=20.0)


def test_accepting_the_main_phase_lifts_the_second(example_cifs):
    # escalas 10:2 -> o SmFeO3 responde pela maior parte da intensidade observada
    obs = ObservedPeaks.from_peaks(mixture(example_cifs, (10.0, 2.0)), (10, 90), noise=5.0)
    cands = [candidate(example_cifs, n, sid=str(i)) for i, n in enumerate(("SmFeO3", "Sm2O3", "_Fe_"))]
    ranked, _ = rescore(cands, obs, [], ScoreSettings())
    assert ranked[0].formula == "SmFeO3"
    sm2o3_before = next(c for c in ranked if c.formula == "Sm2O3").score

    accepted = [AcceptedPhase(ranked[0], next_color([]))]
    state = analyze(obs, accepted)
    assert 0 < state.explained_fraction < 0.95 and state.unexplained.any()
    ranked2, _ = rescore(cands, obs, accepted, ScoreSettings(), state=state)
    assert [c.formula for c in ranked2][0] == "Sm2O3"           # o aceito sai da lista
    assert all(c.formula != "SmFeO3" for c in ranked2)
    assert ranked2[0].score > max(80.0, sm2o3_before)
    assert ranked2[0].subscores["observed"] > 0.8


def test_joint_scales_and_full_explanation(example_cifs):
    obs = ObservedPeaks.from_peaks(mixture(example_cifs, (10.0, 4.0)), (10, 90), noise=5.0)
    cands = {n: candidate(example_cifs, n, sid=n) for n in ("SmFeO3", "Sm2O3")}
    for c in cands.values():
        c.match = score_candidate(c.reference, obs, ScoreSettings(), c.source)
    accepted = [AcceptedPhase(cands["SmFeO3"], "#2ca02c"), AcceptedPhase(cands["Sm2O3"], "#9467bd")]
    state = analyze(obs, accepted)
    assert accepted[0].scale == pytest.approx(10.0, rel=0.1)
    assert accepted[1].scale == pytest.approx(4.0, rel=0.15)
    assert state.explained_fraction > 0.95 and not state.unexplained.any()
    assert set(state.dominant) <= {0, 1}


def test_semi_quant_bookkeeping():
    infos = [{"rir": 2.0, "inrange_fraction": 1.0}, {"rir": 8.0, "inrange_fraction": 0.5}]
    weights = np.array([0.7, 0.3])
    scales = [w * info["rir"] * info["inrange_fraction"] for w, info in zip(weights, infos)]
    assert np.allclose(semi_quant(scales, infos), weights)
    assert semi_quant([1.0, 1.0], [infos[0], None]) == [1.0, None]


def _cif(structure):
    from pymatgen.io.cif import CifWriter
    return str(CifWriter(structure))


def test_rir_from_structure():
    from pymatgen.core import Lattice, Structure
    corundum = Structure.from_spacegroup("R-3c", Lattice.hexagonal(4.7589, 12.991), ["Al", "O"],
                                         [[0, 0, 0.35216], [0.30624, 0, 0.25]])
    assert rir_of(_cif(corundum), CU_KA1, (10, 90))["rir"] == pytest.approx(1.0, rel=1e-6)
    silicon = Structure.from_spacegroup("Fd-3m", Lattice.cubic(5.431), ["Si"], [[0, 0, 0]])
    halite = Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.640), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    assert 3.0 < rir_of(_cif(silicon), CU_KA1, (10, 90))["rir"] < 7.0       # tabelado ≈ 4,7
    assert 3.0 < rir_of(_cif(halite), CU_KA1, (10, 90))["rir"] < 7.0        # tabelado ≈ 4,4


def test_profile_score_on_broad_noisy_data(example_cifs):
    ref = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    peaks = [(t, 0.6 * i, 0.6) for t, i in zip(ref.two_theta, ref.intensity) if i >= 2.0]
    x, y, _ = make_pattern(peaks, background=60.0, seed=21)
    res = search_peaks(x, y, settings=None, wavelength=CU_KA1)
    ctx = build_profile_context(x, y, res.peaks, background=res.background, noise=res.noise)
    obs = ObservedPeaks.from_peaks(res.peaks, (10, 90), res.info["noise_median"])
    explained = {}
    for name in ("SmFeO3", "Sm2O3", "_Fe_"):
        match = score_candidate(reference_pattern(cif_of(example_cifs, name), CU_KA1, (10, 90)), obs, ScoreSettings())
        explained[name], _ = profile_score(ctx, match)
    assert explained["SmFeO3"] > 0.6
    assert explained["SmFeO3"] > explained["Sm2O3"] + 0.2 and explained["SmFeO3"] > explained["_Fe_"] + 0.2


def test_effective_score_mode():
    rich = ObservedPeaks.from_peaks(peaks_from_sticks(np.linspace(20, 80, 12), np.full(12, 50.0)), (10, 90))
    poor = ObservedPeaks.from_peaks(peaks_from_sticks([30.0, 40.0, 50.0], [50.0, 50.0, 50.0]), (10, 90))
    ctx = object()
    assert effective_mode("auto", rich, ctx) == "peaks"
    assert effective_mode("auto", poor, ctx) == "both"
    assert effective_mode("profile", rich, None) == "peaks"     # sem contexto de perfil
    assert effective_mode("profile", rich, ctx) == "profile"


def test_accepted_phase_roundtrip_and_quantify(example_cifs):
    obs = ObservedPeaks.from_peaks(mixture(example_cifs), (10, 90), noise=5.0)
    cand = candidate(example_cifs, "SmFeO3")
    cand.match = score_candidate(cand.reference, obs, ScoreSettings(), cand.source)
    phase = AcceptedPhase(cand, "#2ca02c")
    analyze(obs, [phase])
    quantify_accepted([phase], CU_KA1, (10, 90), obs)
    assert phase.rir and phase.rir["rir"] > 0 and phase.weight_fraction == pytest.approx(1.0)
    data = json.loads(json.dumps(phase.to_dict()))
    back = AcceptedPhase.from_dict(data)
    assert back.candidate.key == cand.key and back.candidate.cif == cand.cif
    assert back.scale == pytest.approx(phase.scale) and back.color == "#2ca02c"
