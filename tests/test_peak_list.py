# -*- coding: utf-8 -*-
"""Lista de picos editável (tools/xrd/search_match/peak_list)."""
import csv
import json
import math

import numpy as np
import pytest

from matfinder.tools.xrd.search_match.peak_list import Peak, PeakList, data_signature


def make_list():
    peaks = [Peak(two_theta=28.0, height=100.0, fwhm=0.1),
             Peak(two_theta=33.0, height=400.0, fwhm=0.12, two_theta_err=0.002),
             Peak(two_theta=47.0, height=50.0, fwhm=0.15, origin="manual"),
             Peak(two_theta=25.0, height=80.0, fwhm=7.0, kind="halo")]
    return PeakList(peaks, wavelength=1.54056)


def test_peaks_are_sorted_and_counted():
    pl = make_list()
    assert [p.two_theta for p in pl] == [25.0, 28.0, 33.0, 47.0]
    assert pl.counts() == (3, 1)


def test_area_is_computed_when_missing():
    p = Peak(two_theta=30.0, height=100.0, fwhm=0.2, eta=0.0)
    assert p.area == pytest.approx(100.0 * 0.2 * 0.5 * math.sqrt(math.pi / math.log(2.0)))


def test_invalid_kind_or_origin():
    with pytest.raises(ValueError):
        Peak(two_theta=30.0, height=1.0, fwhm=0.1, kind="ombro")
    with pytest.raises(ValueError):
        Peak(two_theta=30.0, height=1.0, fwhm=0.1, origin="robo")


def test_removed_auto_peaks_stay_suppressed_on_new_search():
    pl = make_list()
    auto = next(p for p in pl if p.two_theta == 28.0)
    pl.remove([auto.id])
    assert len(pl) == 3 and len(pl.suppressed) == 1
    new = [Peak(two_theta=28.01, height=90.0, fwhm=0.1), Peak(two_theta=60.0, height=70.0, fwhm=0.1),
           Peak(two_theta=47.02, height=55.0, fwhm=0.15)]  # 47,02 cai sobre o pico manual
    accepted = pl.replace_auto(new)
    assert [p.two_theta for p in accepted] == [60.0]
    assert [p.two_theta for p in pl] == [47.0, 60.0]  # manual mantido; automáticos antigos trocados
    assert pl.restore_suppressed() == 1
    assert [p.two_theta for p in pl.replace_auto(new)] == [28.01, 60.0]


def test_adding_on_a_suppressed_position_lifts_the_suppression():
    pl = make_list()
    auto = next(p for p in pl if p.two_theta == 28.0)
    pl.remove([auto.id])
    pl.add(Peak(two_theta=28.0, height=95.0, fwhm=0.1, origin="manual"))
    assert pl.suppressed == []


def test_removing_manual_peaks_does_not_suppress():
    pl = make_list()
    manual = next(p for p in pl if p.origin == "manual")
    pl.remove([manual.id])
    assert pl.suppressed == []


def test_d_spacing_and_its_error():
    pl = make_list()
    p = next(q for q in pl if q.two_theta == 33.0)
    d, d_err = pl.d_spacing(p)
    assert d == pytest.approx(1.54056 / (2 * math.sin(math.radians(16.5))))
    expected_err = d / math.tan(math.radians(16.5)) * math.radians(0.001)
    assert d_err == pytest.approx(expected_err)
    assert PeakList([p]).d_spacing(p) == (None, None)  # sem comprimento de onda


def test_relative_intensities_ignore_halos():
    rel = make_list().relative_intensities()
    assert len(rel) == 3
    assert max(rel.values()) == pytest.approx(100.0)


def test_nearest():
    pl = make_list()
    assert pl.nearest(32.9).two_theta == 33.0
    assert pl.nearest(40.0, max_distance=1.0) is None


def test_json_roundtrip_with_missing_values():
    pl = make_list()
    pl.peaks[0].flags.append("kbeta")
    pl.noise_level = float("nan")
    data = json.loads(json.dumps(pl.to_dict()))  # tem de ser JSON puro (sem NaN)
    assert data["noise_level"] is None
    back = PeakList.from_dict(data)
    assert [p.two_theta for p in back] == [p.two_theta for p in pl]
    assert [p.id for p in back] == [p.id for p in pl]
    assert back.peaks[0].flags == ["kbeta"]
    assert math.isnan(back.peaks[0].two_theta_err)
    assert back.wavelength == pytest.approx(1.54056)
    assert PeakList.from_dict(None).peaks == []


def test_numpy_values_serialize():
    p = Peak(two_theta=np.float64(30.0), height=np.float32(10.0), fwhm=0.1, ka2=np.bool_(True))
    data = json.loads(json.dumps(p.to_dict()))
    assert data["ka2"] is True and data["two_theta"] == 30.0


def test_csv_export(tmp_path):
    path = tmp_path / "picos.csv"
    make_list().write_csv(path)
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0] == "two_theta_deg" and len(rows) == 5
    assert rows[1][10] == "halo"


def test_data_signature_changes_with_data():
    x = np.linspace(10, 80, 100)
    y = np.sin(x)
    assert data_signature(x, y) == data_signature(x.copy(), y.copy())
    assert data_signature(x, y) != data_signature(x, y * 1.01)
