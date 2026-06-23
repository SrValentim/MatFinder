# -*- coding: utf-8 -*-
"""Remoção de background (SNIP / arPLS / dispatcher)."""
import numpy as np

from matfinder.tools.xrd.background_removal import (
    snip_background, calculate_background, get_method_description,
)


def _synthetic():
    """Sinal = background linear + 1 pico gaussiano forte em 2θ=45."""
    x = np.linspace(10, 80, 1000)
    bg = 50 + 0.5 * x
    peak = 500 * np.exp(-0.5 * ((x - 45.0) / 0.2) ** 2)
    return x, bg + peak, bg


def test_snip_keeps_peak_removes_background():
    x, y, _ = _synthetic()
    est = snip_background(y, iterations=40)
    assert len(est) == len(y)
    corrected = y - est
    peak_idx = int(np.argmax(y))
    # o pico sobrevive à subtração do background
    assert corrected[peak_idx] > 0.5 * 500
    # longe do pico, o corrigido fica próximo de zero
    mask = (x < 40) | (x > 50)
    assert np.median(np.abs(corrected[mask])) < 0.1 * corrected.max()


def test_calculate_background_dispatch():
    x, y, _ = _synthetic()
    for method in ("snip", "arpls"):
        est = calculate_background(x, y, method=method)
        assert len(est) == len(y)


def test_unknown_method_returns_zeros():
    x, y, _ = _synthetic()
    est = calculate_background(x, y, method="inexistente")
    assert np.allclose(est, 0)


def test_get_method_description_returns_text():
    assert isinstance(get_method_description("snip"), str)
