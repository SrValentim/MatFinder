# -*- coding: utf-8 -*-
"""Ferramentas matemáticas de DRX (suavização e detecção de picos)."""
import numpy as np

from matfinder.tools.xrd.xrd_math_tools import smooth_data, detect_peaks


def test_smooth_data_reduces_noise():
    x = np.linspace(0, 10, 600)
    clean = np.sin(x)
    rng = np.random.default_rng(0)
    noisy = clean + rng.normal(0, 0.2, clean.size)
    smoothed = smooth_data(noisy, window_length=21, polyorder=3)
    assert len(smoothed) == len(noisy)
    # o suavizado fica mais perto do sinal limpo do que o ruidoso
    assert np.std(smoothed - clean) < np.std(noisy - clean)


def test_smooth_data_fixes_even_window():
    # janela par é inválida -> a função corrige e ainda retorna o mesmo tamanho
    y = np.linspace(0, 1, 100)
    out = smooth_data(y, window_length=10, polyorder=2)
    assert len(out) == len(y)


def test_detect_peaks_finds_known_positions():
    x = np.linspace(10, 80, 2000)
    y = np.zeros_like(x)
    for center in (20.0, 45.0, 70.0):
        y += 100 * np.exp(-0.5 * ((x - center) / 0.1) ** 2)
    positions, intensities = detect_peaks(y, x_data=x, prominence=0.05, width=1)
    assert len(positions) >= 3
    for center in (20.0, 45.0, 70.0):
        assert np.min(np.abs(positions - center)) < 0.5


def test_detect_peaks_empty_input():
    positions, intensities = detect_peaks(np.array([]))
    assert len(positions) == 0
    assert len(intensities) == 0


def test_detect_peaks_constant_input():
    positions, _ = detect_peaks(np.ones(100))
    assert len(positions) == 0
