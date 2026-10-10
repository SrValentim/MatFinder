# -*- coding: utf-8 -*-
"""Pontuação de candidatos (tools/xrd/search_match/scoring) e busca completa sem rede."""
import os

import numpy as np
import pytest

from xrd_synthetic import CU_KA1, CU_KA2
from matfinder.tools.xrd.search_match.candidate_search import CandidateSearchSettings, find_candidates
from matfinder.tools.xrd.search_match.candidates import Candidate, ElementFilter
from matfinder.tools.xrd.search_match.peak_list import Peak
from matfinder.tools.xrd.search_match.peak_search import search_peaks
from matfinder.tools.xrd.search_match.scoring import (
    ObservedPeaks, ReferencePattern, ScoreSettings, merge_reflections, reference_pattern, score_candidate,
)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MATFINDER_CACHE_DIR", str(tmp_path / "cache"))


def cif_of(example_cifs, name):
    return open(next(p for p in example_cifs if name in os.path.basename(p)), encoding="utf-8").read()


def peaks_from_reference(ref, scale=1.0, shift=0.0, height=1000.0, fwhm=0.12, min_i=3.0, lo=10.0, hi=90.0):
    """Picos 'observados' gerados a partir de reflexões (com rede e zero alterados)."""
    out = []
    for tt, inten in zip(ref.two_theta, ref.intensity):
        if inten < min_i:
            continue
        s = np.sin(np.radians(tt / 2.0)) / scale
        if abs(s) >= 1:
            continue
        pos = 2.0 * np.degrees(np.arcsin(s)) + shift
        if lo <= pos <= hi:
            out.append(Peak(two_theta=float(pos), height=height * inten / 100.0, fwhm=fwhm, two_theta_err=0.003))
    return out


def test_reference_pattern_is_cached(example_cifs):
    cif = cif_of(example_cifs, "SmFeO3")
    ref = reference_pattern(cif, CU_KA1, (10, 90))
    assert len(ref.two_theta) > 20 and ref.intensity.max() == pytest.approx(100.0)
    again = reference_pattern(cif, CU_KA1, (10, 90))
    assert np.allclose(ref.two_theta, again.two_theta) and ref.hkl == again.hkl


def test_merge_reflections():
    ref = ReferencePattern(np.array([30.0, 30.01, 40.0]), np.array([50.0, 50.0, 10.0]), ["1 1 1", "2 0 0", "2 2 0"])
    merged = merge_reflections(ref, 0.05)
    assert np.allclose(merged.two_theta, [30.005, 40.0]) and np.allclose(merged.intensity, [100.0, 10.0])
    assert merged.hkl[0].endswith("+")


def test_true_phase_scores_high_and_recovers_alignment(example_cifs):
    cif = cif_of(example_cifs, "SmFeO3")
    ref = reference_pattern(cif, CU_KA1, (10, 90))
    obs = ObservedPeaks.from_peaks(peaks_from_reference(ref, scale=1.012, shift=0.05), (10, 90), noise=5.0)
    match = score_candidate(ref, obs, ScoreSettings(), source="MP")   # MP: rede de DFT
    assert match.score > 90
    assert match.lattice_scale == pytest.approx(1.012, abs=0.001)
    assert match.shift == pytest.approx(0.05, abs=0.011)
    assert match.subscores["reference"] > 0.9  # ponderado pela intensidade das reflexões esperadas


def test_wrong_phase_scores_low(example_cifs):
    ref_true = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    obs = ObservedPeaks.from_peaks(peaks_from_reference(ref_true), (10, 90), noise=5.0)
    for wrong in ("Sm2O3", "_Fe_"):
        ref = reference_pattern(cif_of(example_cifs, wrong), CU_KA1, (10, 90))
        assert score_candidate(ref, obs, ScoreSettings(), source="COD").score < 50


def test_weak_reference_lines_below_noise_are_not_penalized(example_cifs):
    ref = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    strong_only = peaks_from_reference(ref, min_i=10.0)     # só o que um dado ruidoso mostraria
    noisy = score_candidate(ref, ObservedPeaks.from_peaks(strong_only, (10, 90), noise=34.0))  # limite = I de 10%
    quiet = score_candidate(ref, ObservedPeaks.from_peaks(strong_only, (10, 90), noise=2.0))
    assert noisy.subscores["reference"] > quiet.subscores["reference"]
    assert noisy.subscores["reference"] > 0.95 and noisy.score > 85


def test_kbeta_flagged_peaks_do_not_count_as_unexplained(example_cifs):
    ref = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    peaks = peaks_from_reference(ref)
    extra = Peak(two_theta=29.0, height=400.0, fwhm=0.12, flags=["kbeta"])
    obs = ObservedPeaks.from_peaks(peaks + [extra], (10, 90), noise=5.0)
    assert score_candidate(ref, obs).subscores["observed"] == pytest.approx(1.0, abs=1e-6)


def test_real_smfeo3_ranks_the_right_phase(examples_dir, example_cifs):
    rows = []
    path = os.path.join(examples_dir, "experimental", "SmFeO3", "2_SmFeO3_24h.dat")
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            values = [float(t) for t in line.replace(",", " ").split()]
        except ValueError:
            continue
        if len(values) >= 4:
            rows.append((values[0], values[3]))
    x, y = np.array(rows).T
    res = search_peaks(x, y, wavelength=CU_KA1, wavelength_ka2=CU_KA2)
    obs = ObservedPeaks.from_peaks(res.peaks, (x[0], x[-1]), res.info["noise_median"])
    scores = {name: score_candidate(reference_pattern(cif_of(example_cifs, name), CU_KA1, (x[0], x[-1])), obs,
                                    source="MP").score for name in ("SmFeO3", "Sm2O3", "_Fe_")}
    assert scores["SmFeO3"] > 75
    assert scores["SmFeO3"] > scores["Sm2O3"] + 25 and scores["SmFeO3"] > scores["_Fe_"] + 25


def test_find_candidates_end_to_end_without_network(examples_dir, example_cifs, monkeypatch):
    """COD e MP substituídos por candidatos locais: a busca completa ordena e agrupa."""
    from matfinder.tools.xrd.search_match import candidate_search as cs

    def fake_cod(flt, cancel=None, session=None):
        return [Candidate("COD", "1", "SmFeO3", ("Fe", "O", "Sm"), "Pbnm", 62, cif=cif_of(example_cifs, "SmFeO3")),
                Candidate("COD", "2", "Sm2O3", ("O", "Sm"), "Ia-3", 206, cif=cif_of(example_cifs, "Sm2O3")),
                Candidate("COD", "3", "SmFeO3", ("Fe", "O", "Sm"), "Pbnm", 62, cif=cif_of(example_cifs, "SmFeO3")),
                Candidate("COD", "4", "X", ("Fe", "O", "Sm"), cif="isto não é um CIF")]

    def fake_mp(flt, key, only_exp, max_e, cancel=None, rester_factory=None):
        return [Candidate("MP", "mp-13", "Fe", ("Fe",), "Im-3m", 229, cif=cif_of(example_cifs, "_Fe_"))]

    monkeypatch.setattr(cs, "search_cod", fake_cod)
    monkeypatch.setattr(cs, "search_mp", fake_mp)
    x = np.linspace(10, 90, 4001)
    ref = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    peaks = peaks_from_reference(ref, scale=1.003)
    stages = []
    result = find_candidates(peaks, ElementFilter(required=["Sm", "Fe", "O"], possible=["Fe"]), CU_KA1, (10, 90),
                             CandidateSearchSettings(), noise=5.0, mp_api_key="k" * 32,
                             progress=lambda f, s: stages.append((f, s)))
    assert result.candidates[0].formula == "SmFeO3" and result.candidates[0].score > 90
    assert result.candidates[0].group_members == ["COD:3"]          # duplicata agrupada
    assert result.info["failed"] == 1                                 # o CIF inválido ficou de fora
    assert stages[-1] == (1.0, "concluído")
    assert [f for f, _ in stages] == sorted(f for f, _ in stages)


def test_find_candidates_validates_inputs():
    with pytest.raises(ValueError):
        find_candidates([Peak(two_theta=30, height=1, fwhm=0.1)] * 3, ElementFilter(), CU_KA1, (10, 90))
    with pytest.raises(ValueError):
        find_candidates([Peak(two_theta=30, height=1, fwhm=0.1)], ElementFilter(required=["Fe"]), CU_KA1, (10, 90))


def test_source_errors_are_reported_without_aborting(example_cifs, monkeypatch):
    from matfinder.tools.xrd.search_match import candidate_search as cs

    def broken_cod(*a, **k):
        raise ConnectionError("COD indisponível")

    monkeypatch.setattr(cs, "search_cod", broken_cod)
    monkeypatch.setattr(cs, "find_mp_api_key", lambda: None)
    ref = reference_pattern(cif_of(example_cifs, "SmFeO3"), CU_KA1, (10, 90))
    result = find_candidates(peaks_from_reference(ref), ElementFilter(required=["Sm", "Fe", "O"]), CU_KA1, (10, 90))
    assert "COD" in result.errors and "MP" in result.errors
    assert result.candidates == []
