# -*- coding: utf-8 -*-
"""Busca robusta de picos (tools/xrd/search_match/peak_search).

Cenários sintéticos com picos conhecidos (sementes fixas) e o difratograma real
de SmFeO3 dos exemplos, identificado como fase única.
"""
import dataclasses
import os

import numpy as np
import pytest
from scipy.signal import savgol_filter

from xrd_synthetic import CU_KA1, CU_KA2, make_pattern, match
from matfinder.tools.xrd.search_match.peak_search import (
    PRESETS, PeakSearchSettings, SearchCancelled, estimate_background, estimate_noise,
    fit_peak_at, search_peaks,
)
from matfinder.tools.xrd.search_match.profiles import pv_area
from matfinder.tools.xrd.emission_lines import same_d_two_theta

NO_KA2 = PeakSearchSettings(ka2=False)


def positions(result, kind="peak"):
    return [p.two_theta for p in result.peaks if p.kind == kind]


def test_single_peak_precision():
    x, y, _ = make_pattern([(45.123, 10000, 0.10)], background=100)
    res = search_peaks(x, y, settings=NO_KA2)
    assert len(res.peaks) == 1
    p = res.peaks[0]
    assert abs(p.two_theta - 45.123) < 0.002          # passo de 0,02°: precisão bem abaixo do passo
    assert abs(p.two_theta - 45.123) < 4 * p.two_theta_err
    assert abs(p.fwhm - 0.10) / 0.10 < 0.03
    assert abs(p.area - pv_area(10000, 0.10, 0.5)) / pv_area(10000, 0.10, 0.5) < 0.02
    assert p.origin == "auto" and p.kind == "peak"


def test_noisy_pattern_recall_without_false_positives():
    truth = [(15.2, 40, .12), (21.7, 60, .10), (27.3, 90, .15), (33.0, 150, .10), (38.4, 250, .20),
             (44.1, 400, .12), (50.6, 800, .18), (56.2, 1500, .14), (62.9, 3000, .22), (69.4, 120, .16),
             (75.8, 70, .25), (82.3, 200, .20)]
    x, y, _ = make_pattern(truth, background=200, slope=-1.0, seed=3)
    found = positions(search_peaks(x, y, settings=NO_KA2))
    strong = [c for c, h, _ in truth if h >= 100]
    pairs, missed, extra = match(found, [c for c, _, _ in truth], tol=0.05)
    assert not [c for c in missed if c in strong]
    assert extra == []
    assert np.sqrt(np.mean([(f - t) ** 2 for t, f in pairs])) < 0.03


def test_overlapping_peaks_are_resolved():
    x, y, _ = make_pattern([(40.0, 1000, .20), (40.16, 600, .20)], background=100, seed=1)
    found = positions(search_peaks(x, y, settings=NO_KA2))
    pairs, missed, extra = match(found, [40.0, 40.16], tol=0.03)
    assert missed == [] and extra == []


def test_ka2_doublet_is_reported_once_at_ka1():
    truth = [30.0, 60.0, 85.0]
    x, y, _ = make_pattern([(c, 2500, .12) for c in truth], background=150, ka2_ratio=0.5, seed=2)
    res = search_peaks(x, y, wavelength=CU_KA1, wavelength_ka2=CU_KA2)
    found = positions(res)
    pairs, missed, extra = match(found, truth, tol=0.005)
    assert missed == [] and extra == []
    assert all(p.ka2 for p in res.peaks)


def test_without_ka2_model_the_doublet_shows_both_lines():
    x, y, _ = make_pattern([(85.0, 2500, .12)], background=150, ka2_ratio=0.5, seed=2)
    found = positions(search_peaks(x, y, settings=NO_KA2))
    ka2 = same_d_two_theta(85.0, CU_KA1, CU_KA2)  # ≈ 85,258°
    pairs, missed, extra = match(found, [85.0, ka2], tol=0.01)
    assert missed == [] and extra == []


def test_halo_in_broad_mode_and_crystallinity():
    sharp = [(28.5, 800, .15), (33.1, 400, .15), (47.5, 600, .18), (56.3, 300, .2)]
    x, y, _ = make_pattern(sharp, background=150, halos=[(25.0, 500, 8.0)], seed=4)
    res = search_peaks(x, y, settings=PRESETS["broad"])
    halos = [p for p in res.peaks if p.kind == "halo"]
    assert len(halos) == 1
    assert abs(halos[0].two_theta - 25.0) < 0.5
    assert abs(halos[0].fwhm - 8.0) / 8.0 < 0.1
    pairs, missed, extra = match(positions(res), [c for c, _, _ in sharp], tol=0.05)
    assert missed == [] and extra == []
    crystal = sum(pv_area(h, w, 0.5) for _, h, w in sharp)
    truth = crystal / (crystal + pv_area(500, 8.0, 0.3))
    assert abs(res.crystallinity - truth) < 0.02


def test_pure_noise_gives_no_peaks():
    x, y, _ = make_pattern([], background=300, slope=-0.5, seed=5)
    assert search_peaks(x, y, settings=NO_KA2).peaks == []


def test_single_point_spikes_are_ignored():
    x, y, _ = make_pattern([(50.0, 500, .15)], background=200, spikes=[(35.0, 2000), (65.0, 1500)], seed=6)
    res = search_peaks(x, y, settings=NO_KA2)
    assert res.info["spikes_removed"] == 2
    pairs, missed, extra = match(positions(res), [50.0], tol=0.02)
    assert missed == [] and extra == []


def test_low_counts_broad_peaks():
    truth = [(28.4, 30, .5), (32.9, 20, .5), (47.3, 25, .6), (56.1, 15, .6), (69.0, 10, .7), (76.5, 12, .7)]
    x, y, _ = make_pattern(truth, background=5, seed=7)
    pairs, missed, extra = match(positions(search_peaks(x, y, settings=NO_KA2)), [c for c, _, _ in truth], tol=0.15)
    assert missed == [] and extra == []


def test_peaks_next_to_the_edges_are_kept():
    truth = [(10.15, 800, .12), (89.9, 600, .12), (50.0, 700, .12)]
    x, y, _ = make_pattern(truth, background=300, decay=500, seed=8)
    pairs, missed, extra = match(positions(search_peaks(x, y, settings=NO_KA2)), [c for c, _, _ in truth], tol=0.02)
    assert missed == [] and extra == []


def test_normalized_and_smoothed_data_without_false_positives():
    truth = [(25.0, 400, .12), (35.0, 120, .12), (45.0, 60, .15), (55.0, 900, .14), (65.0, 80, .18)]
    x, y, _ = make_pattern(truth, background=250, seed=9)
    normalized = (y - y.min()) / np.ptp(y)
    for data in (normalized, savgol_filter(normalized, 11, 2)):
        res = search_peaks(x, data, settings=NO_KA2)
        assert not res.info["poisson_noise"]
        pairs, missed, extra = match(positions(res), [c for c, _, _ in truth], tol=0.07)
        assert extra == []
        assert {25.0, 35.0, 55.0} <= {t for t, _ in pairs}


def test_unsorted_and_irregular_input():
    truth = [(30.0, 900, .12), (50.0, 600, .15)]
    x, y, _ = make_pattern(truth, background=200, seed=10)
    reference = positions(search_peaks(x, y, settings=NO_KA2))
    rng = np.random.default_rng(0)
    keep = np.sort(rng.choice(len(x), size=int(0.9 * len(x)), replace=False))
    order = rng.permutation(len(keep))
    res = search_peaks(x[keep][order], y[keep][order], settings=NO_KA2)
    assert res.info["resampled"]
    found = positions(res)
    assert len(found) == len(reference)
    assert np.allclose(found, reference, atol=0.01)


def test_constant_or_tiny_inputs_return_empty():
    assert search_peaks(np.arange(10.0), np.ones(10)).peaks == []
    assert search_peaks(np.linspace(10, 80, 500), np.full(500, 7.0)).peaks == []


def test_cancel_raises():
    x, y, _ = make_pattern([(45.0, 1000, .12)], background=100)
    with pytest.raises(SearchCancelled):
        search_peaks(x, y, cancel=lambda: True)


def test_progress_reports_increasing_fractions():
    x, y, _ = make_pattern([(45.0, 1000, .12)], background=100)
    seen = []
    search_peaks(x, y, settings=NO_KA2, progress=lambda f, m: seen.append(f))
    assert seen and seen[-1] == 1.0 and seen == sorted(seen)


def test_settings_roundtrip_ignores_unknown_keys():
    s = dataclasses.replace(PeakSearchSettings(), sensitivity=3.3, broad_mode=True)
    data = s.to_dict()
    data["campo_antigo"] = 1
    assert PeakSearchSettings.from_dict(data) == s


def test_noise_model_poisson_and_empirical():
    x, y, mean = make_pattern([(40.0, 3000, .2)], background=400, seed=11)
    sigma, poisson = estimate_noise(y)
    assert poisson
    flat = np.abs(x - 40.0) > 2
    assert np.median(sigma[flat] / np.sqrt(mean[flat])) == pytest.approx(1.0, abs=0.1)
    x2, y2, _ = make_pattern([(40.0, 300, .2)], background=50.0, noise=2.0, seed=12)
    sigma2, poisson2 = estimate_noise(y2 / 1000.0)
    assert not poisson2
    assert np.median(sigma2[flat]) == pytest.approx(0.002, rel=0.2)


def test_background_follows_baseline_and_keeps_edge_peaks():
    truth = [(10.2, 900, .12), (45.0, 900, .12)]
    x, y, mean = make_pattern(truth, background=500, decay=300, seed=13)
    true_bg = 500 + 300 * np.exp(-(x - 10.0) / 8.0)
    mask = np.zeros(len(x), dtype=bool)
    for c, _, w in truth:
        mask |= np.abs(x - c) < 2.5 * w
    bg = estimate_background(y, 0.6 / 0.02, smooth_sigma=1.5, peak_mask=mask)
    free = ~mask & (x > 12)
    assert np.median(np.abs(bg[free] - true_bg[free])) < 2 * np.sqrt(500)
    edge = np.argmin(np.abs(x - 10.2))
    assert y[edge] - bg[edge] > 600  # o pico da borda não foi absorvido pelo fundo


def test_manual_peak_fit_near_click():
    x, y, _ = make_pattern([(30.0, 1500, .12), (52.37, 70, .14)], background=200, seed=14)
    res = search_peaks(x, y, settings=dataclasses.replace(NO_KA2, sensitivity=8.0))
    assert not any(abs(p.two_theta - 52.37) < 0.1 for p in res.peaks)
    peak = fit_peak_at(x, y, 52.30, settings=NO_KA2, existing=res.peaks)
    assert peak.origin == "manual"
    assert abs(peak.two_theta - 52.37) < 0.03
    assert 30 < peak.height < 140


def _load_smfeo3(path):
    rows = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        parts = line.replace(",", " ").split()
        try:
            values = [float(p) for p in parts]
        except ValueError:
            continue
        if len(values) >= 4:
            rows.append((values[0], values[3]))  # coluna 4: contagens
    data = np.array(rows)
    return data[:, 0], data[:, 1]


def test_real_smfeo3_peaks_belong_to_the_phase(examples_dir, example_cifs):
    """SmFeO3 de 24 h (fase única): todo pico achado é reflexão do SmFeO3."""
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.core import Structure

    x, y = _load_smfeo3(os.path.join(examples_dir, "experimental", "SmFeO3", "2_SmFeO3_24h.dat"))
    res = search_peaks(x, y, wavelength=CU_KA1, wavelength_ka2=CU_KA2)
    peaks = [p for p in res.peaks if p.kind == "peak"]
    assert len(peaks) >= 7
    strongest = max(peaks, key=lambda p: p.height)
    assert 32.6 < strongest.two_theta < 32.95

    cif = next(p for p in example_cifs if "SmFeO3" in p)
    ref = XRDCalculator(wavelength=CU_KA1).get_pattern(Structure.from_file(cif), two_theta_range=(5, 100))
    ref_tt = np.array(ref.x)[np.array(ref.y) >= 1.0]
    found = np.array([p.two_theta for p in peaks])
    # A rede do Materials Project (DFT) é um pouco maior que a real: alinha zero e escala.
    theta = np.radians(ref_tt / 2.0)
    best = 0
    for scale in np.arange(0.985, 1.0151, 0.001):
        pred0 = np.degrees(2.0 * np.arcsin(np.clip(np.sin(theta) / scale, -1, 1)))
        for shift in np.arange(-0.3, 0.301, 0.01):
            dist = np.min(np.abs(found[:, None] - (pred0 + shift)[None, :]), axis=1)
            best = max(best, int(np.sum(dist < 0.15)))
    assert best == len(found)
