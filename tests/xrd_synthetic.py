# -*- coding: utf-8 -*-
"""Gerador de difratogramas sintéticos para os testes da busca de picos.

Os picos são pseudo-Voigt com parâmetros conhecidos; opcionalmente com dubleto
Kα2 (Cu), halos amorfos, fundo inclinado/decaindo, ruído de Poisson e spikes.
"""

import numpy as np

from matfinder.tools.xrd.emission_lines import same_d_two_theta
from matfinder.tools.xrd.search_match.profiles import pv_shape

CU_KA1 = 1.54056
CU_KA2 = 1.54439


def make_pattern(peaks, start=10.0, stop=90.0, step=0.02, background=200.0, slope=0.0,
                 decay=0.0, halos=(), ka2_ratio=0.0, eta=0.5, seed=0, noise="poisson", spikes=()):
    """Gera (2θ, intensidade medida, intensidade esperada sem ruído).

    Args:
        peaks: sequência de (2θ, altura, fwhm) ou (2θ, altura, fwhm, eta).
        halos: sequência de (2θ, altura, fwhm) de componentes amorfos largos.
        ka2_ratio: intensidade do Kα2 relativa ao Kα1 (0 = sem dubleto).
        noise: "poisson", "none" ou o desvio-padrão de um ruído gaussiano constante.
        spikes: sequência de (2θ, amplitude) somada a um único ponto.
    """
    x = np.arange(start, stop + step / 2.0, step)
    mean = background + slope * (x - start) + decay * np.exp(-(x - start) / 8.0)
    for peak in peaks:
        center, height, fwhm = peak[:3]
        mix = peak[3] if len(peak) > 3 else eta
        mean = mean + height * pv_shape(x, center, fwhm, mix)
        if ka2_ratio:
            c2 = same_d_two_theta(center, CU_KA1, CU_KA2)
            mean = mean + ka2_ratio * height * pv_shape(x, c2, fwhm, mix)
    for center, height, fwhm in halos:
        mean = mean + height * pv_shape(x, center, fwhm, 0.3)
    rng = np.random.default_rng(seed)
    if noise == "poisson":
        y = rng.poisson(np.maximum(mean, 0.0)).astype(float)
    elif noise == "none":
        y = mean.copy()
    else:
        y = mean + rng.normal(0.0, float(noise), size=len(x))
    for position, amplitude in spikes:
        y[int(np.argmin(np.abs(x - position)))] += amplitude
    return x, y, mean


def match(found, truth, tol):
    """Pareia posições encontradas com as verdadeiras (cada uma usada uma vez).

    Returns:
        (pares (verdade, encontrada), verdadeiras não achadas, encontradas sobrando)
    """
    found = sorted(found)
    remaining = list(found)
    pairs, missed = [], []
    for t in sorted(truth):
        if not remaining:
            missed.append(t)
            continue
        best = min(remaining, key=lambda f: abs(f - t))
        if abs(best - t) <= tol:
            pairs.append((t, best))
            remaining.remove(best)
        else:
            missed.append(t)
    return pairs, missed, remaining
