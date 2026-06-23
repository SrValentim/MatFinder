# -*- coding: utf-8 -*-
"""Normalização de difratogramas (lógica pura)."""
import numpy as np
import pytest

from matfinder.tools.xrd.normalization_dialog import (
    normalize_data, normalize_by_peak, get_method_description,
)


def test_normalize_01_maps_to_unit_range():
    out = normalize_data(np.array([1.0, 2, 3, 4, 5]), "normalize_01")
    assert len(out) == 5
    assert np.isclose(out.min(), 0.0)
    assert np.isclose(out.max(), 1.0)


def test_divide_by_max():
    out = normalize_data(np.array([2.0, 4, 8]), "divide_by_max")
    assert np.isclose(out.max(), 1.0)


def test_divide_by_median():
    out = normalize_data(np.array([1.0, 2, 3]), "divide_by_median")
    assert np.isclose(out[1], 1.0)


def test_constant_data_raises():
    with pytest.raises(ValueError):
        normalize_data(np.array([5.0, 5, 5]), "normalize_01")


def test_invalid_method_raises():
    with pytest.raises(ValueError):
        normalize_data(np.array([1.0, 2, 3]), "does_not_exist")


def test_normalize_by_peak():
    x = np.linspace(10, 80, 1401)
    y = 100 * np.exp(-0.5 * ((x - 30.0) / 0.3) ** 2) + 1.0  # pico em 2θ=30
    y_norm, peak_intensity = normalize_by_peak(x, y, 30.0, window_size=0.5)
    assert peak_intensity > 0
    assert len(y_norm) == len(y)
    assert np.allclose(y_norm, y / peak_intensity)


def test_get_method_description_returns_text():
    desc = get_method_description("normalize_01")
    assert isinstance(desc, str) and desc
